import torch
import torch.nn as nn
from transformers import AutoModel
from torchcrf import CRF

class AttentionPooling(nn.Module):
    def __init__(self, hidden: int):
        super().__init__()
        # Đổi từ nn.Sequential thành nn.Linear với tên 'scorer' cho khớp file .pt
        self.scorer = nn.Linear(hidden, 1)

    def forward(self, x, mask):
        # Giữ nguyên logic forward của file train
        scores  = self.scorer(x).squeeze(-1)           
        scores  = scores.masked_fill(mask == 0, -1e9)
        weights = torch.softmax(scores, dim=-1)        
        return (x * weights.unsqueeze(-1)).sum(dim=2)

class ABSAv3(nn.Module):
    def __init__(self, model_name: str, dropout: float = 0.15):
        super().__init__()
        self.backbone    = AutoModel.from_pretrained(model_name)
        hidden           = self.backbone.config.hidden_size
        self.dropout     = nn.Dropout(dropout)
        
        self.bio_head    = nn.Linear(hidden, 11) # Khớp với N_BIO=11
        self.crf         = CRF(11, batch_first=True)
        
        self.span_attn   = AttentionPooling(hidden)
        # Lưu ý: Trong file train sent_head là nn.Sequential
        self.sent_head   = nn.Sequential(nn.Dropout(0.2), nn.Linear(hidden, 3)) 
        
        self.global_head = nn.Linear(hidden, 3)
    def forward(self, input_ids, attention_mask, span_masks=None, bio_labels=None):
        # 1. Chạy Backbone (Huy đã đổi thành self.backbone)
        out = self.backbone(input_ids=input_ids, attention_mask=attention_mask)
        
        # 2. Lấy output (Đoạn này bị NameError vì chưa định nghĩa sequence_output)
        sequence_output = out.last_hidden_state  # <-- THÊM DÒNG NÀY
        
        # 3. Dropout và lấy CLS (Token <s> ở vị trí 0)
        seq_out = self.dropout(sequence_output)
        cls_out = self.dropout(seq_out[:, 0, :])
        mask_bool = attention_mask.bool()

        # 4. BIO Head
        bio_emissions = self.bio_head(seq_out)

        # 5. Xử lý CRF Loss hoặc Decode
        if bio_labels is not None:
            crf_loss = -self.crf(bio_emissions, bio_labels, mask=mask_bool, reduction="mean")
            bio_preds = None
        else:
            crf_loss = None
            bio_preds = self.crf.decode(bio_emissions, mask=mask_bool)

        # 6. Global Head
        global_logits = self.global_head(cls_out)

        # 7. Span Head (Sentiment cục bộ)
        span_logits = None
        if span_masks is not None:
            B, L, H = seq_out.shape
            M = span_masks.shape[1]
            # Mở rộng seq_out để tính Attention Pooling cho từng Span
            seq_exp = seq_out.unsqueeze(1).expand(B, M, L, H)
            span_repr = self.span_attn(seq_exp, span_masks)
            span_logits = self.sent_head(span_repr)

        return bio_emissions, crf_loss, bio_preds, span_logits, global_logits

def extract_bio_spans(bio_labels):
    """Hàm giải mã ID thành Spans"""
    ASPECTS = ["Product", "Service", "Ship", "Price", "App"]
    id2label = {0: "O"}
    idx = 1
    for asp in ASPECTS:
        id2label[idx] = f"B-{asp}"
        id2label[idx+1] = f"I-{asp}"
        idx += 2

    spans = set()
    current_span = None
    for i, label_id in enumerate(bio_labels):
        label = id2label.get(label_id, "O")
        if label.startswith("B-"):
            if current_span: spans.add(current_span)
            current_span = (i, i, label[2:])
        elif label.startswith("I-"):
            if current_span and current_span[2] == label[2:]:
                current_span = (current_span[0], i, current_span[2])
            else:
                current_span = None
        else:
            if current_span:
                spans.add(current_span)
                current_span = None
    if current_span: spans.add(current_span)
    return spans