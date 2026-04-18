import os
import torch
import torch.nn as nn
import json
import unicodedata
from transformers import AutoTokenizer, AutoModel
from torchcrf import CRF

# ==========================================
# 1. KHAI BÁO CẤU HÌNH & HẰNG SỐ
# ==========================================
MODEL_NAME = "Fsoft-AIC/videberta-base"
MAX_LEN = 224
CONTEXT_WINDOW = 5
MAX_OPS = 8
ASPECTS = ["Fashion", "Electronics", "General", "Service", "Ship", "Price", "App"]

def nfc(x): 
    return unicodedata.normalize("NFC", x)

def build_bio():
    labels = ["O"]
    for a in ASPECTS:
        labels += [f"B-{a}", f"I-{a}"]
    return labels, {l: i for i, l in enumerate(labels)}, {i: l for i, l in enumerate(labels)}

BIO_LABELS, BIO_L2I, BIO_I2L = build_bio()
N_BIO, N_SENT = len(BIO_LABELS), 3

# ==========================================
# 2. ĐỊNH NGHĨA KIẾN TRÚC MODEL (PHẢI TRÙNG VỚI LÚC TRAIN)
# ==========================================
class AttentionPooling(nn.Module):
    def __init__(self, hidden):
        super().__init__()
        self.fc = nn.Linear(hidden, 1)

    def forward(self, x, mask):
        # Dùng -1e4 để tránh lỗi overflow float16 trên SageMaker GPU
        score = self.fc(x).squeeze(-1).masked_fill(mask == 0, -1e4)
        return (x * torch.softmax(score, dim=-1).unsqueeze(-1)).sum(dim=2)

class ABSAModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone = AutoModel.from_pretrained(MODEL_NAME)
        h = self.backbone.config.hidden_size
        self.bio_head = nn.Linear(h, N_BIO)
        self.crf = CRF(N_BIO, batch_first=True)
        self.span_attn = AttentionPooling(h)
        self.sent_head = nn.Sequential(nn.Dropout(0.2), nn.Linear(h, N_SENT))
        self.global_head = nn.Linear(h, N_SENT)

    def forward(self, ids, mask, span_mask=None):
        seq = self.backbone(ids, attention_mask=mask).last_hidden_state
        h = seq.shape[-1]
        emissions = self.bio_head(seq)
        cls = seq[:, 0]

        span_logits = None
        if span_mask is not None:
            B, L = seq.shape[:2]
            M = span_mask.shape[1]
            span_repr = self.span_attn(seq.unsqueeze(1).expand(B, M, L, h), span_mask)
            span_logits = self.sent_head(span_repr)

        return emissions, span_logits, self.global_head(cls)

# Helper function trích xuất span
def extract_spans(seq):
    spans, start, cur = set(), None, None
    for i, lid in enumerate(seq):
        tag = BIO_I2L.get(lid, "O")
        if tag.startswith("B-"):
            if start is not None: spans.add((start, i - 1, cur))
            start, cur = i, tag[2:]
        elif tag.startswith("I-") and cur == tag[2:]:
            pass
        else:
            if start is not None: spans.add((start, i - 1, cur))
            start, cur = None, None
    if start is not None: spans.add((start, len(seq) - 1, cur))
    return spans

# ==========================================
# 3. SAGEMAKER HANDLERS (HÀM BẮT BUỘC)
# ==========================================

def model_fn(model_dir):
    """Load model từ thư mục model_dir (S3 giải nén ra)"""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = ABSAModel()
    with open(os.path.join(model_dir, "best_model_v5.pt"), "rb") as f:
        model.load_state_dict(torch.load(f, map_location=device))
    model.to(device).eval()
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    return {"model": model, "tokenizer": tokenizer, "device": device}

def input_fn(request_body, request_content_type):
    """Xử lý dữ liệu đầu vào từ API request"""
    if request_content_type == "application/json":
        data = json.loads(request_body)
        return data.get("inputs", data.get("text", ""))
    return request_body

def predict_fn(input_data, model_dict):
    model = model_dict["model"]
    tokenizer = model_dict["tokenizer"]
    device = model_dict["device"]
    
    # ÉP MÔ HÌNH VỀ FLOAT32 ĐỂ ĐỒNG NHẤT TRÊN CPU
    model.to(torch.float32)
    
    sent_map = {1: "Positive", 0: "Negative", 2: "Neutral"}
    text = nfc(input_data)
    
    enc = tokenizer(text, max_length=MAX_LEN, padding="max_length", 
                    truncation=True, return_special_tokens_mask=True, return_tensors="pt")
    
    # ÉP ĐẦU VÀO VỀ LONG (CHO IDS) VÀ MASK (CHO ATTENTION)
    ids = enc['input_ids'].to(device).long()
    mask = enc['attention_mask'].to(device).long()
    spec_mask = enc.pop("special_tokens_mask")[0]
    seq_len = ids.shape[1]

    with torch.no_grad():
        # KHÔNG DÙNG AUTOCAST, CHẠY THUẦN FLOAT32
        # Đảm bảo đầu vào seq không bị cast sang Half ở bước backbone
        emissions, _, glob_logits = model(ids, mask)
        
        bio_p = model.crf.decode(emissions, mask=mask.bool())[0]
        spans = sorted(list(extract_spans(bio_p)), key=lambda x: x[0])
        g_id = glob_logits.argmax(-1).item()

        if not spans:
            return {"global_sentiment": sent_map.get(g_id, "Unknown"), "aspects": []}

        span_mask = torch.zeros(1, MAX_OPS, seq_len).to(device).float() # Đảm bảo mask là Float32
        for op_idx, (tmin, tmax, _) in enumerate(spans[:MAX_OPS]):
            lo = max(tmin - CONTEXT_WINDOW, 1)
            hi = min(tmax + CONTEXT_WINDOW, seq_len - 1)
            if op_idx > 0: lo = max(lo, spans[op_idx - 1][1] + 1)
            if op_idx < len(spans) - 1: hi = min(hi, spans[op_idx + 1][0] - 1)
            for j in range(lo, hi + 1):
                if not spec_mask[j]: span_mask[0, op_idx, j] = 1.0

        # Chạy lần 2 lấy Sentiment
        _, sent_logits, _ = model(ids, mask, span_mask=span_mask)

        results = {"global_sentiment": sent_map.get(g_id, "Unknown"), "aspects": []}
        for i, (start, end, asp) in enumerate(spans[:MAX_OPS]):
            s_id = sent_logits[0][i].argmax().item()
            results["aspects"].append({
                "aspect": asp,
                "sentiment": sent_map.get(s_id, "Unknown"),
                "target": tokenizer.decode(ids[0][start:end+1]).strip()
            })
        return results

def output_fn(prediction, content_type):
    """Trả về kết quả dưới dạng JSON"""
    return json.dumps(prediction), "application/json"