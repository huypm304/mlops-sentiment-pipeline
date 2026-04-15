"""
train_absa_v3_colab.py
─────────────────
Bản dành riêng cho môi trường Colab Upload trực tiếp (Không dùng Drive)
Tự động tải file best_absa_v3.pt và log về máy tính nội bộ sau khi train xong.
"""

import json, random, os, csv, math, unicodedata
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from transformers import (
    AutoTokenizer, AutoModel,
    get_linear_schedule_with_warmup,
)
from sklearn.metrics import f1_score
from tqdm.auto import tqdm

try:
    from torchcrf import CRF
except ImportError:
    raise ImportError("Vui lòng chạy: !pip install pytorch-crf")

# ══════════════════════════════════════════════════════════════════════════════
# 1. CẤU HÌNH ĐƯỜNG DẪN LOCAL COLAB (/content/)
# ══════════════════════════════════════════════════════════════════════════════

# Đảm bảo bạn đã kéo thả 3 file này vào thư mục gốc của Colab
TRAIN_FILE    = "/content/train_data_v3.jsonl"
VAL_FILE      = "/content/val_data.jsonl"
TEST_FILE     = "/content/test_data.jsonl"

SAVE_PATH     = "/content/best_absa_v3.pt"
LOG_FILE      = "/content/training_log_v3.csv"

MODEL_NAME    = "Fsoft-AIC/videberta-base"
MAX_LEN       = 320
BATCH_SIZE    = 8
ACCUM_STEPS   = 4          # effective batch = 32
EPOCHS        = 12
LR_BACKBONE   = 1.5e-5
LR_HEADS      = 3e-5
WARMUP_RATIO  = 0.1

LAMBDA_BIO    = 1.0
LAMBDA_SENT   = 1.5
LAMBDA_GLOBAL = 0.3

CONTEXT_TOKENS = 2
MAX_OPS        = 8
SEED           = 42
PATIENCE       = 4

ASPECTS    = ["Product", "Service", "Ship", "Price", "App"]
SENTIMENTS = [0, 1, 2]
SENT_NAME  = {0: "Neg", 1: "Pos", 2: "Neu"}


# ── Label maps ────────────────────────────────────────────────────────────────

def build_bio_labels():
    labels = ["O"]
    for asp in ASPECTS:
        labels.append(f"B-{asp}")
        labels.append(f"I-{asp}")
    l2i = {l: i for i, l in enumerate(labels)}
    i2l = {i: l for i, l in enumerate(labels)}
    return labels, l2i, i2l

BIO_LABELS, BIO_LABEL2ID, BIO_ID2LABEL = build_bio_labels()
N_BIO    = len(BIO_LABELS)   # 11
N_SENT   = 3
N_GLOBAL = 3


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

# ══════════════════════════════════════════════════════════════════════════════
# ALIGNMENT & DATASET (Giữ nguyên logic cực xịn)
# ══════════════════════════════════════════════════════════════════════════════

def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text) if text else ""

def find_token_indices(offsets, special_mask, char_s: int, char_e: int):
    indices = []
    for i, (tok_s, tok_e) in enumerate(offsets):
        if special_mask[i] or (tok_s == 0 and tok_e == 0):
            continue
        if max(tok_s, char_s) < min(tok_e, char_e):
            indices.append(i)
    return indices

class ABSADataset(Dataset):
    def __init__(self, file_path: str, tokenizer, max_len: int):
        self.tokenizer = tokenizer
        self.max_len   = max_len
        self.items     = self._load(file_path)

    def _load(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"⚠️ Không tìm thấy file {file_path}. Nhớ upload lên Colab nhé!")

        items, skipped, align_miss = [], 0, 0
        with open(file_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                try: rec = json.loads(line)
                except json.JSONDecodeError: skipped += 1; continue

                text        = nfc(rec.get("text", "").strip())
                global_sent = rec.get("global_sentiment", -1)
                opinions    = rec.get("opinions", [])

                if len(text) < 2 or global_sent not in [0, 1, 2]:
                    skipped += 1; continue

                enc = self.tokenizer(
                    text, max_length=self.max_len, padding="max_length",
                    truncation=True, return_offsets_mapping=True,
                    return_special_tokens_mask=True,
                )

                offsets      = enc.pop("offset_mapping")
                special_mask = enc.pop("special_tokens_mask")
                seq_len      = len(enc["input_ids"])

                bio_labels = [BIO_LABEL2ID["O"]] * seq_len
                span_masks = torch.zeros(MAX_OPS, seq_len)
                span_sents = torch.full((MAX_OPS,), -100, dtype=torch.long)

                op_idx = 0
                for op in opinions:
                    if op_idx >= MAX_OPS: break

                    asp      = op.get("aspect", "")
                    sent_int = op.get("sentiment", -1)
                    char_s   = op.get("start", -1)
                    char_e   = op.get("end", -1)

                    if asp not in ASPECTS or sent_int not in SENTIMENTS: continue
                    if char_s < 0 or char_e <= char_s: continue

                    token_indices = find_token_indices(offsets, special_mask, char_s, char_e)
                    if not token_indices: align_miss += 1; continue

                    for idx, i in enumerate(token_indices):
                        prefix    = "B" if idx == 0 else "I"
                        label_str = f"{prefix}-{asp}"
                        if label_str in BIO_LABEL2ID: bio_labels[i] = BIO_LABEL2ID[label_str]

                    lo = max(0, token_indices[0]  - CONTEXT_TOKENS)
                    hi = min(seq_len - 1, token_indices[-1] + CONTEXT_TOKENS)
                    for i in range(lo, hi + 1):
                        if not special_mask[i] and not (offsets[i][0] == 0 and offsets[i][1] == 0):
                            span_masks[op_idx, i] = 1.0

                    span_sents[op_idx] = sent_int
                    op_idx += 1

                items.append({
                    "input_ids"     : torch.tensor(enc["input_ids"],      dtype=torch.long),
                    "attention_mask": torch.tensor(enc["attention_mask"], dtype=torch.long),
                    "bio_labels"    : torch.tensor(bio_labels,            dtype=torch.long),
                    "span_masks"    : span_masks,
                    "span_sents"    : span_sents,
                    "global_label"  : torch.tensor(global_sent,           dtype=torch.long),
                })

        print(f"  {os.path.basename(file_path)}: {len(items):,} items (skipped={skipped}, align_miss={align_miss})")
        return items

    def __len__(self):        return len(self.items)
    def __getitem__(self, i): return self.items[i]


# ══════════════════════════════════════════════════════════════════════════════
# MODEL, LOSS & METRICS (Giữ nguyên)
# ══════════════════════════════════════════════════════════════════════════════

class AttentionPooling(nn.Module):
    def __init__(self, hidden: int):
        super().__init__()
        self.scorer = nn.Linear(hidden, 1)

    def forward(self, x, mask):
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
        self.bio_head    = nn.Linear(hidden, N_BIO)
        self.crf         = CRF(N_BIO, batch_first=True)
        self.span_attn   = AttentionPooling(hidden)
        self.sent_head   = nn.Sequential(nn.Dropout(0.2), nn.Linear(hidden, N_SENT))
        self.global_head = nn.Linear(hidden, N_GLOBAL)

    def forward(self, input_ids, attention_mask, span_masks=None, bio_labels=None):
        out       = self.backbone(input_ids=input_ids, attention_mask=attention_mask)
        seq_out   = self.dropout(out.last_hidden_state)
        cls_out   = self.dropout(seq_out[:, 0, :])
        mask_bool = attention_mask.bool()

        bio_emissions = self.bio_head(seq_out)

        if bio_labels is not None:
            crf_loss  = -self.crf(bio_emissions, bio_labels, mask=mask_bool, reduction="mean")
            bio_preds = None
        else:
            crf_loss  = None
            bio_preds = self.crf.decode(bio_emissions, mask=mask_bool)

        global_logits = self.global_head(cls_out)
        span_logits = None
        if span_masks is not None:
            B, L, H = seq_out.shape
            M       = span_masks.shape[1]
            seq_exp     = seq_out.unsqueeze(1).expand(B, M, L, H)
            span_repr   = self.span_attn(seq_exp, span_masks)
            span_logits = self.sent_head(span_repr)

        return bio_emissions, crf_loss, bio_preds, span_logits, global_logits

def focal_loss(logits, labels, alpha_weights, gamma: float = 2.0, ignore_index: int = -100):
    valid  = labels != ignore_index
    if valid.sum() == 0: return torch.tensor(0.0, device=logits.device, requires_grad=True)
    logits = logits[valid]
    labels = labels[valid]
    ce     = F.cross_entropy(logits, labels, reduction="none")
    pt     = torch.exp(-ce)
    loss   = alpha_weights[labels] * (1 - pt) ** gamma * ce
    return loss.mean()

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

def span_prf(pred_list, gold_list, aspect_filter=None):
    tp = fp = fn = 0
    for ps, gs in zip(pred_list, gold_list):
        if aspect_filter:
            ps = {s for s in ps if s[2] == aspect_filter}
            gs = {s for s in gs if s[2] == aspect_filter}
        tp += len(ps & gs); fp += len(ps - gs); fn += len(gs - ps)
    p = tp / (tp + fp + 1e-9); r = tp / (tp + fn + 1e-9)
    return p, r, 2 * p * r / (p + r + 1e-9)

def run_eval(model, loader, alpha_sent, alpha_global, device):
    model.eval()
    total_loss = 0.0
    pred_spans, gold_spans           = [], []
    all_sent_preds, all_sent_golds   = [], []
    all_g_preds,    all_g_labels     = [], []

    with torch.no_grad():
        for b in loader:
            ids        = b["input_ids"].to(device)
            mask       = b["attention_mask"].to(device)
            bio_lbl    = b["bio_labels"].to(device)
            span_masks = b["span_masks"].to(device)
            span_sents = b["span_sents"].to(device)
            g_lbl      = b["global_label"].to(device)

            bio_em, crf_loss, _, span_log, g_log = model(ids, mask, span_masks, bio_labels=bio_lbl)
            bio_preds = model.crf.decode(bio_em, mask=mask.bool())

            l_s = focal_loss(span_log.view(-1, N_SENT), span_sents.view(-1), alpha_sent)
            l_g = focal_loss(g_log, g_lbl, alpha_global, ignore_index=-1)
            total_loss += (LAMBDA_BIO * crf_loss.item() + LAMBDA_SENT * l_s.item() + LAMBDA_GLOBAL * l_g.item())

            bio_golds = bio_lbl.cpu().tolist()
            mask_list = mask.cpu().tolist()
            for i, (p_seq, g_seq) in enumerate(zip(bio_preds, bio_golds)):
                vl = int(sum(mask_list[i]))
                pred_spans.append(extract_bio_spans(p_seq[:vl]))
                gold_spans.append(extract_bio_spans(g_seq[:vl]))

            if span_log is not None:
                for sp, sg in zip(span_log.argmax(-1).cpu().view(-1).tolist(), span_sents.cpu().view(-1).tolist()):
                    if sg != -100:
                        all_sent_preds.append(sp)
                        all_sent_golds.append(sg)

            all_g_preds.extend(g_log.argmax(-1).cpu().tolist())
            all_g_labels.extend(g_lbl.cpu().tolist())

    p, r, span_f1 = span_prf(pred_spans, gold_spans)
    sent_f1 = f1_score(all_sent_golds, all_sent_preds, average="macro", zero_division=0) if all_sent_golds else 0.0
    sent_per = {}
    if all_sent_golds:
        for sid, sname in SENT_NAME.items():
            pb = [1 if x == sid else 0 for x in all_sent_preds]
            gb = [1 if x == sid else 0 for x in all_sent_golds]
            sent_per[sname] = f1_score(gb, pb, zero_division=0)

    global_f1 = f1_score(all_g_labels, all_g_preds, average="macro", zero_division=0)
    per_asp = {asp: span_prf(pred_spans, gold_spans, aspect_filter=asp)[2] for asp in ASPECTS}

    return {
        "loss"      : total_loss / max(len(loader), 1),
        "span_f1"   : span_f1, "span_prec": p, "span_rec": r,
        "sent_f1"   : sent_f1, "sent_per": sent_per,
        "global_f1" : global_f1, "per_aspect": per_asp,
    }

def composite_score(m): return 0.4 * m["sent_f1"] + 0.4 * m["span_f1"] + 0.2 * m["global_f1"]


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    set_seed(SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device : {device}\nModel  : {MODEL_NAME}")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    print("\n📊 Loading datasets (từ /content/)...")
    train_ds = ABSADataset(TRAIN_FILE, tokenizer, MAX_LEN)
    val_ds   = ABSADataset(VAL_FILE,   tokenizer, MAX_LEN)
    test_ds  = ABSADataset(TEST_FILE,  tokenizer, MAX_LEN)

    train_dl = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,  num_workers=2, pin_memory=True)
    val_dl   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False, num_workers=2, pin_memory=True)
    test_dl  = DataLoader(test_ds,  batch_size=BATCH_SIZE, shuffle=False, num_workers=2, pin_memory=True)

    model = ABSAv3(MODEL_NAME).to(device).float()

    optimizer = AdamW([
        {"params": model.backbone.parameters(),    "lr": LR_BACKBONE},
        {"params": model.bio_head.parameters(),    "lr": LR_HEADS},
        {"params": model.crf.parameters(),         "lr": LR_HEADS},
        {"params": model.span_attn.parameters(),   "lr": LR_HEADS},
        {"params": model.sent_head.parameters(),   "lr": LR_HEADS},
        {"params": model.global_head.parameters(), "lr": LR_HEADS},
    ], weight_decay=0.01)

    total_steps  = math.ceil(len(train_dl) / ACCUM_STEPS) * EPOCHS
    scheduler    = get_linear_schedule_with_warmup(optimizer, int(total_steps * WARMUP_RATIO), total_steps)

    alpha_sent   = torch.tensor([1.2, 1.0, 1.8], device=device)
    alpha_global = torch.tensor([1.0, 1.0, 1.2], device=device)

    best_score, patience_cnt = 0.0, 0
    log_rows = []

    print(f"\n🚀 Training V3 (Local Storage Mode)")
    print("=" * 62)

    for epoch in range(1, EPOCHS + 1):
        model.train()
        train_loss = 0.0
        optimizer.zero_grad()

        loop = tqdm(train_dl, desc=f"Epoch {epoch}/{EPOCHS}", leave=False)
        for step, b in enumerate(loop):
            ids, mask = b["input_ids"].to(device), b["attention_mask"].to(device)
            bio_lbl, span_masks = b["bio_labels"].to(device), b["span_masks"].to(device)
            span_sents, g_lbl = b["span_sents"].to(device), b["global_label"].to(device)

            _, crf_loss, _, span_log, g_log = model(ids, mask, span_masks, bio_labels=bio_lbl)

            l_s = focal_loss(span_log.view(-1, N_SENT), span_sents.view(-1), alpha_sent)
            l_g = focal_loss(g_log, g_lbl, alpha_global, ignore_index=-1)

            loss = (LAMBDA_BIO * crf_loss + LAMBDA_SENT * l_s + LAMBDA_GLOBAL * l_g) / ACCUM_STEPS
            loss.backward()

            if (step + 1) % ACCUM_STEPS == 0 or (step + 1) == len(train_dl):
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()

            train_loss += loss.item() * ACCUM_STEPS
            loop.set_postfix(loss=f"{loss.item() * ACCUM_STEPS:.4f}")

        avg_train = train_loss / len(train_dl)
        m         = run_eval(model, val_dl, alpha_sent, alpha_global, device)
        score     = composite_score(m)

        print(f"\nEpoch {epoch:>2}  train={avg_train:.4f}  val={m['loss']:.4f}")
        print(f"  Span   F1={m['span_f1']:.4f}  P={m['span_prec']:.4f}  R={m['span_rec']:.4f}")
        print(f"  Sent   F1={m['sent_f1']:.4f}  " + "  ".join(f"{k}={v:.3f}" for k, v in m["sent_per"].items()))
        print(f"  Global F1={m['global_f1']:.4f}")
        print(f"  Per-aspect: " + "  ".join(f"{a}={m['per_aspect'][a]:.3f}" for a in ASPECTS))
        print(f"  🔥 Score={score:.4f}")

        row = {"epoch": epoch, "train_loss": avg_train, "val_loss": m["loss"], "score": score}
        log_rows.append(row)

        if score > best_score:
            best_score   = score
            patience_cnt = 0
            torch.save({
                "epoch"       : epoch,
                "model_state" : model.state_dict(),
                "config"      : {"model_name": MODEL_NAME, "max_len": MAX_LEN},
            }, SAVE_PATH)
            print(f"  ⭐ Best saved to {SAVE_PATH}")
        else:
            patience_cnt += 1
            if patience_cnt >= PATIENCE:
                print(f"\n⏹  Early stopping at epoch {epoch}")
                break

    if log_rows:
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=log_rows[0].keys())
            writer.writeheader(); writer.writerows(log_rows)

    print("\n🏁 Final Test...")
    model.load_state_dict(torch.load(SAVE_PATH)["model_state"])
    t = run_eval(model, test_dl, alpha_sent, alpha_global, device)
    print(f"🏆 TEST F1: Span={t['span_f1']:.4f} | Sent={t['sent_f1']:.4f} | Global={t['global_f1']:.4f}")

    # ==========================================
    # 🔥 AUTO-DOWNLOAD FILES XUỐNG MÁY BOSCH
    # ==========================================
    try:
        from google.colab import files
        print("\n📥 Đang kích hoạt tải model và log về máy tính của bạn...")
        if os.path.exists(SAVE_PATH): files.download(SAVE_PATH)
        if os.path.exists(LOG_FILE): files.download(LOG_FILE)
    except Exception as e:
        print(f"\n⚠️ Lỗi Auto-download: {e}. Bạn hãy tải thủ công từ cây thư mục bên trái của Colab nhé.")

if __name__ == "__main__":
    main()