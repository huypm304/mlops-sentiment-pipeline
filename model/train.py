import os
import json
import csv
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel, get_linear_schedule_with_warmup
from torchcrf import CRF
from torch.optim import AdamW
from sklearn.metrics import f1_score
from tqdm import tqdm
import unicodedata

# -----------------------------------------------------------------------------
# 1. CONFIGURATION (GIỮ NGUYÊN BẢN GỐC CỦA BẠN)
# -----------------------------------------------------------------------------
MODEL_NAME         = "Fsoft-AIC/videberta-base"
TRAIN_FILE         = "/content/drive/MyDrive/Colab Notebooks/Dataset_v4/data_train_v4.jsonl"
VAL_FILE           = "/content/drive/MyDrive/Colab Notebooks/Dataset_v4/val_data.jsonl"
MODEL_SAVE         = "model/absa_v4.pt"
LOG_FILE           = "model/training_log.csv"

MAX_LEN            = 320
BATCH_SIZE         = 16
EPOCHS             = 15
PATIENCE           = 4
MAX_OPS            = 8
NUM_WORKERS        = 2

LR_BACKBONE        = 2e-5
LR_HEADS           = 5e-5
WEIGHT_DECAY       = 0.01
MAX_GRAD_NORM      = 1.0

ASPECTS            = ["Fashion", "Electronics", "General", "Service", "Ship", "Price", "App"]
SENTIMENTS         = [0, 1, 2] 
STOP_WORDS         = {"nhưng", "tuy", "mà", "chứ"}

LAMBDA_BIO         = 2.0  
LAMBDA_SENT        = 1.0  
LAMBDA_GLOBAL      = 0.5  

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def build_bio_labels():
    labels = ["O"]
    for asp in ASPECTS:
        labels.extend([f"B-{asp}", f"I-{asp}"])
    return labels, {l: i for i, l in enumerate(labels)}, {i: l for i, l in enumerate(labels)}

BIO_LABELS, BIO_LABEL2ID, BIO_ID2LABEL = build_bio_labels()
N_BIO, N_SENT, N_GLOBAL = len(BIO_LABELS), len(SENTIMENTS), len(SENTIMENTS)

# -----------------------------------------------------------------------------
# 2. UTILS & LOSS
# -----------------------------------------------------------------------------
def nfc(text: str) -> str: return unicodedata.normalize("NFC", text) if text else ""

class FocalLoss(nn.Module):
    def __init__(self, alpha=None, gamma=2.5, reduction="none"):
        super().__init__()
        self.gamma, self.reduction, self.alpha = gamma, reduction, alpha 

    def forward(self, logits, targets):
        ce_loss = F.cross_entropy(logits, targets, reduction="none", weight=self.alpha)
        pt = torch.exp(-ce_loss)
        focal_loss = ((1 - pt) ** self.gamma) * ce_loss
        return focal_loss.mean() if self.reduction == "mean" else focal_loss

# -----------------------------------------------------------------------------
# 3. MODEL (FIX LỖI KIỂU DỮ LIỆU CRF)
# -----------------------------------------------------------------------------
class AttentionPooling(nn.Module):
    def __init__(self, hidden):
        super().__init__()
        self.fc = nn.Linear(hidden, 1)
    def forward(self, x, mask):
        scores = self.fc(x).squeeze(-1).masked_fill(mask == 0, -1e4)
        w = torch.softmax(scores, dim=-1)
        return (x * w.unsqueeze(-1)).sum(dim=2)

class ABSAv4(nn.Module):
    def __init__(self, model_name: str, dropout: float = 0.2): 
        super().__init__()
        self.backbone = AutoModel.from_pretrained(model_name)
        hidden = self.backbone.config.hidden_size
        self.dropout_seq  = nn.Dropout(dropout)
        self.bio_head    = nn.Linear(hidden, N_BIO)
        self.crf         = CRF(N_BIO, batch_first=True)
        self.span_attn   = AttentionPooling(hidden)
        self.sent_head   = nn.Sequential(nn.Dropout(dropout), nn.Linear(hidden, N_SENT))
        self.global_head = nn.Linear(hidden, N_GLOBAL)

    def forward(self, input_ids, attention_mask, span_masks=None, bio_labels=None):
        out       = self.backbone(input_ids=input_ids, attention_mask=attention_mask)
        seq_out   = self.dropout_seq(out.last_hidden_state)
        cls_out   = self.dropout_seq(seq_out[:, 0, :])
        
        # BẮT BUỘC: Ép emissions sang float32 cho CRF
        bio_emissions = self.bio_head(seq_out).float() 
        mask_bool = attention_mask.bool()

        crf_loss = None
        if bio_labels is not None:
            crf_loss = -self.crf(bio_emissions, bio_labels, mask=mask_bool, reduction="none")
        
        bio_preds = self.crf.decode(bio_emissions, mask=mask_bool)
        global_logits = self.global_head(cls_out)
        
        span_logits = None
        if span_masks is not None:
            B, L, H = seq_out.shape
            seq_exp = seq_out.unsqueeze(1).expand(B, span_masks.shape[1], L, H)
            span_logits = self.sent_head(self.span_attn(seq_exp, span_masks))

        return crf_loss, bio_preds, span_logits, global_logits

# -----------------------------------------------------------------------------
# 4. DATASET & TRAINING (GIỮ NGUYÊN LOGIC CỦA BẠN)
# -----------------------------------------------------------------------------
class ABSADataset(Dataset):
    def __init__(self, file_path, tokenizer):
        self.items = []
        if not os.path.exists(file_path): return
        with open(file_path, encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line.strip())
                text = nfc(rec.get("text", "").strip())
                enc = tokenizer(text, max_length=MAX_LEN, padding="max_length", truncation=True, return_offsets_mapping=True, return_special_tokens_mask=True)
                offsets, special_mask = enc.pop("offset_mapping"), enc.pop("special_tokens_mask")
                seq_len = len(enc["input_ids"])
                bio_labels, span_masks, span_sents = [0]*seq_len, torch.zeros(MAX_OPS, seq_len), torch.full((MAX_OPS,), -100, dtype=torch.long)
                for op_idx, op in enumerate(rec.get("opinions", [])[:MAX_OPS]):
                    asp, sent_int = op.get("aspect", ""), op.get("sentiment", -1)
                    if asp not in ASPECTS or sent_int not in SENTIMENTS: continue
                    char_s, char_e = op.get("start", -1), op.get("end", -1)
                    tokens = [i for i, (ts, te) in enumerate(offsets) if not special_mask[i] and max(ts, char_s) < min(te, char_e)]
                    if not tokens: continue
                    for idx, i in enumerate(tokens): bio_labels[i] = BIO_LABEL2ID[f"{'B' if idx==0 else 'I'}-{asp}"]
                    lo, hi = tokens[0], tokens[-1]
                    while lo > 0 and not special_mask[lo-1] and text[offsets[lo-1][0]:offsets[lo-1][1]].lower() not in STOP_WORDS: lo -= 1
                    while hi < seq_len-1 and not special_mask[hi+1] and text[offsets[hi+1][0]:offsets[hi+1][1]].lower() not in STOP_WORDS: hi += 1
                    for i in range(lo, hi + 1): 
                        if not special_mask[i]: span_masks[op_idx, i] = 1.0
                    span_sents[op_idx] = sent_int
                sents_list = [o.get("sentiment", -1) for o in rec.get("opinions", [])]
                cw = 2.5 if (0 in sents_list and 1 in sents_list) else 1.0
                self.items.append({"input_ids": torch.tensor(enc["input_ids"], dtype=torch.long), "attention_mask": torch.tensor(enc["attention_mask"], dtype=torch.long), "bio_labels": torch.tensor(bio_labels, dtype=torch.long), "span_masks": span_masks, "span_sents": span_sents, "global_label": torch.tensor(rec.get("global_sentiment", -1), dtype=torch.long), "conflict_weight": torch.tensor(cw, dtype=torch.float)})
    def __len__(self): return len(self.items)
    def __getitem__(self, i): return self.items[i]

def train():
    os.makedirs("model", exist_ok=True)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    train_dl = DataLoader(ABSADataset(TRAIN_FILE, tokenizer), batch_size=BATCH_SIZE, shuffle=True, num_workers=NUM_WORKERS)
    val_dl   = DataLoader(ABSADataset(VAL_FILE, tokenizer), batch_size=BATCH_SIZE, shuffle=False)
    model = ABSAv4(MODEL_NAME).to(DEVICE)
    opt = AdamW([{"params": model.backbone.parameters(), "lr": LR_BACKBONE}, {"params": [p for n, p in model.named_parameters() if "backbone" not in n], "lr": LR_HEADS}], weight_decay=WEIGHT_DECAY)
    sch = get_linear_schedule_with_warmup(opt, int(0.1*len(train_dl)*EPOCHS), len(train_dl)*EPOCHS)
    
    # Dùng GradScaler chuẩn PyTorch 2.x+
    scaler = torch.amp.GradScaler('cuda')
    crit_sent = FocalLoss(alpha=torch.tensor([1.2, 1.0, 1.2], device=DEVICE), gamma=2.5)
    crit_global = FocalLoss(gamma=2.0)
    best_score = 0

    for epoch in range(1, EPOCHS + 1):
        model.train()
        total_tr_loss = 0
        pbar = tqdm(train_dl, desc=f"Epoch {epoch}/{EPOCHS}")
        for b in pbar:
            opt.zero_grad()
            ids, mask, bio, s_mask, s_sent, g_lbl, cw = [b[k].to(DEVICE) for k in b]
            with torch.amp.autocast('cuda'):
                c_loss_raw, _, s_logits, g_logits = model(ids, mask, s_mask, bio)
                loss_bio = (c_loss_raw * cw).mean()
                loss_s = torch.tensor(0.0, device=DEVICE)
                if (s_sent != -100).any():
                    ls_raw = crit_sent(s_logits.view(-1, N_SENT), s_sent.view(-1)).view(ids.size(0), MAX_OPS)
                    loss_s = (ls_raw * cw.unsqueeze(1))[(s_sent != -100)].mean()
                loss_g = torch.tensor(0.0, device=DEVICE)
                if (g_lbl != -1).any(): loss_g = (crit_global(g_logits, g_lbl) * cw).mean()
                loss = (LAMBDA_BIO * loss_bio) + (LAMBDA_SENT * loss_s) + (LAMBDA_GLOBAL * loss_g)

            scaler.scale(loss).backward()
            scaler.unscale_(opt) # Bước này cực kỳ quan trọng
            torch.nn.utils.clip_grad_norm_(model.parameters(), MAX_GRAD_NORM)
            scaler.step(opt)
            scaler.update()
            sch.step()
            total_tr_loss += loss.item()
            pbar.set_postfix({"loss": f"{loss.item():.4f}", "avg": f"{total_tr_loss/(pbar.n+1):.4f}"})

        # Đoạn Evaluate và Metric (Giữ nguyên của bạn)
        model.eval()
        all_p, all_g, all_gs_p, all_gs_g = [], [], [], []
        with torch.no_grad(), torch.amp.autocast('cuda'):
            for b in val_dl:
                ids, mask, bio, s_mask, s_sent, _, _ = [b[k].to(DEVICE) for k in b]
                _, b_preds, s_logits, _ = model(ids, mask, s_mask)
                for i, (p_seq, g_seq) in enumerate(zip(b_preds, bio.cpu().tolist())):
                    vl = int(mask[i].sum())
                    all_p.append(set(extract_bio_spans(p_seq[:vl])))
                    all_g.append(set(extract_bio_spans(g_seq[:vl])))
                if s_logits is not None:
                    mask_s = s_sent != -100
                    all_gs_p.extend(s_logits.argmax(-1)[mask_s].cpu().tolist()); all_gs_g.extend(s_sent[mask_s].cpu().tolist())

        tp = fp = fn = 0
        for ps, gs in zip(all_p, all_g): tp += len(ps & gs); fp += len(ps - gs); fn += len(gs - ps)
        f1_span = 2*tp/(2*tp+fp+fn+1e-9)
        f1_sent = f1_score(all_gs_g, all_gs_p, average="macro", zero_division=0)
        composite = (f1_span * 0.6) + (f1_sent * 0.4)
        print(f"Result: Span F1: {f1_span:.4f} | Sent F1: {f1_sent:.4f} | Score: {composite:.4f}")
        if composite > best_score:
            best_score = composite; torch.save(model.state_dict(), MODEL_SAVE)

def extract_bio_spans(label_seq):
    spans, start, cur = set(), None, None
    for i, lid in enumerate(label_seq):
        s = BIO_ID2LABEL.get(lid, "O")
        if s.startswith("B-"):
            if start is not None: spans.add((start, i - 1, cur))
            start, cur = i, s[2:]
        elif s.startswith("I-") and cur and s[2:] == cur: pass
        else:
            if start is not None: spans.add((start, i - 1, cur))
            start = cur = None
    if start is not None: spans.add((start, len(label_seq) - 1, cur))
    return spans

if __name__ == "__main__":
    train()