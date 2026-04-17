# =============================================================================
# ABSA v5 - Phased Training
# =============================================================================
import os, json, unicodedata, random, csv
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel, get_linear_schedule_with_warmup
from torch.optim import AdamW
from torchcrf import CRF
from sklearn.metrics import f1_score
from tqdm.auto import tqdm

# =========================
# CONFIG
# =========================
MODEL_NAME    = "Fsoft-AIC/videberta-base"
TRAIN_FILE    = "/content/data_train_v5.jsonl"
VAL_FILE      = "/content/val_data.jsonl"
MODEL_SAVE    = "best_model_v5.pt"
CSV_LOG       = "train_log_v5.csv"

MAX_LEN       = 256
BATCH_SIZE    = 8
EPOCHS        = 20
PATIENCE      = 6        # đủ rộng để phase 2 converge
PHASE1_EPOCHS = 5        # epoch 1-5: chỉ BIO + Global; epoch 6+: mở full loss
MAX_OPS       = 8

LR_BACKBONE      = 8e-6
LR_HEADS         = 2e-5
WARMUP_RATIO     = 0.1      # 10% bước đầu linear warmup
DROPOUT_RATE     = 0.3
CONTEXT_WINDOW   = 5        # ±token window quanh span cho sentiment head

# Trọng số loss
LAMBDA_BIO    = 1.5
LAMBDA_SENT   = 1.0
LAMBDA_GLOBAL = 0.5
LAMBDA_CONS   = 0.1

DEVICE  = torch.device("cuda" if torch.cuda.is_available() else "cpu")
ASPECTS = ["Fashion", "Electronics", "General", "Service", "Ship", "Price", "App"]
SENTIMENTS = [0, 1, 2]

# =========================
# LABEL & UTILS
# =========================
def build_bio():
    labels = ["O"]
    for a in ASPECTS: labels += [f"B-{a}", f"I-{a}"]
    l2i = {l:i for i,l in enumerate(labels)}
    i2l = {i:l for i,l in enumerate(labels)}
    return labels, l2i, i2l

BIO_LABELS, BIO_L2I, BIO_I2L = build_bio()
N_BIO, N_SENT = len(BIO_LABELS), len(SENTIMENTS)

def nfc(x): return unicodedata.normalize("NFC", x)

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

# =========================
# DATASET
# =========================
class ABSADataset(Dataset):
    def __init__(self, file, tokenizer):
        self.items = []
        if not os.path.exists(file):
            print(f"Warning: File not found at {file}")
            return

        with open(file, encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                text = nfc(rec["text"])

                enc = tokenizer(
                    text,
                    max_length=MAX_LEN,
                    padding="max_length",
                    truncation=True,
                    return_offsets_mapping=True,
                    return_special_tokens_mask=True,
                )

                offsets     = enc.pop("offset_mapping")
                special_mask = enc.pop("special_tokens_mask")
                L = len(enc["input_ids"])

                bio       = [0] * L
                span_mask = torch.zeros(MAX_OPS, L)
                span_sent = torch.full((MAX_OPS,), -100, dtype=torch.long)

                # Pass 1: thu thập token indices của từng opinion hợp lệ
                valid_ops = []
                for op in rec.get("opinions", []):
                    s    = op.get("start", -1)
                    e    = op.get("end", -1)
                    asp  = op.get("aspect", "")
                    sent = op.get("sentiment", -1)
                    if not asp or sent == -1:
                        continue
                    tokens = [
                        i for i, (a, b) in enumerate(offsets)
                        if not special_mask[i] and max(a, s) < min(b, e)
                    ]
                    if tokens:
                        valid_ops.append((tokens, asp, sent))

                # Sắp xếp theo vị trí để tính midpoint chính xác
                valid_ops.sort(key=lambda x: x[0][0])

                # Pass 2: gán BIO + span_mask với window bị clip tại midpoint
                for op_idx, (tokens, asp, sent) in enumerate(valid_ops[:MAX_OPS]):
                    # BIO labels
                    for k, i in enumerate(tokens):
                        tag = f"B-{asp}" if k == 0 else f"I-{asp}"
                        if tag in BIO_L2I:
                            bio[i] = BIO_L2I[tag]

                    tmin, tmax = min(tokens), max(tokens)

                    # Biên trái: không lấn sang cuối span trước
                    lo = tmin - CONTEXT_WINDOW
                    if op_idx > 0:
                        prev_end = max(valid_ops[op_idx - 1][0])
                        lo = max(lo, prev_end + 1)
                    lo = max(lo, 1)  # bỏ [CLS] pos 0

                    # Biên phải: không lấn sang đầu span sau
                    hi = tmax + CONTEXT_WINDOW
                    if op_idx < len(valid_ops) - 1:
                        next_start = min(valid_ops[op_idx + 1][0])
                        hi = min(hi, next_start - 1)
                    hi = min(hi, L - 1)

                    for i in range(lo, hi + 1):
                        if not special_mask[i]:
                            span_mask[op_idx, i] = 1.0

                    span_sent[op_idx] = sent

                self.items.append({
                    "ids":       torch.tensor(enc["input_ids"]),
                    "mask":      torch.tensor(enc["attention_mask"]),
                    "bio":       torch.tensor(bio, dtype=torch.long),
                    "span_mask": span_mask,
                    "span_sent": span_sent,
                    "global":    torch.tensor(rec.get("global_sentiment", -1), dtype=torch.long),
                })

    def __len__(self):         return len(self.items)
    def __getitem__(self, i):  return self.items[i]

# =========================
# MODEL
# =========================
class AttentionPooling(nn.Module):
    def __init__(self, hidden):
        super().__init__()
        self.fc = nn.Linear(hidden, 1)

    def forward(self, x, mask):
        score = self.fc(x).squeeze(-1).masked_fill(mask == 0, -1e9)
        w = torch.softmax(score, dim=-1)
        return (x * w.unsqueeze(-1)).sum(dim=2)


class ABSAModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone = AutoModel.from_pretrained(MODEL_NAME)
        h = self.backbone.config.hidden_size

        self.dropout = nn.Dropout(DROPOUT_RATE)

        self.bio_head = nn.Linear(h, N_BIO)
        self.crf      = CRF(N_BIO, batch_first=True)

        self.span_attn = AttentionPooling(h)
        self.sent_head = nn.Sequential(nn.Dropout(0.2), nn.Linear(h, N_SENT))

        self.global_head = nn.Linear(h, N_SENT)

    def forward(self, ids, mask, span_mask=None, bio=None):
        out = self.backbone(ids, attention_mask=mask)
        seq = self.dropout(out.last_hidden_state)
        cls = self.dropout(seq[:, 0])

        emissions = self.bio_head(seq)
        mask_bool = mask.bool()

        crf_loss = None
        if bio is not None:
            crf_loss = -self.crf(emissions, bio, mask=mask_bool, reduction="mean")

        bio_pred      = self.crf.decode(emissions, mask=mask_bool)
        global_logits = self.global_head(cls)

        span_logits = None
        if span_mask is not None:
            B, L, H  = seq.shape
            M        = span_mask.shape[1]
            seq_exp  = seq.unsqueeze(1).expand(B, M, L, H)
            span_repr = self.span_attn(seq_exp, span_mask)
            span_logits = self.sent_head(span_repr)

        return crf_loss, bio_pred, span_logits, global_logits

# =========================
# EVALUATION
# =========================
def extract_spans(seq):
    spans, start, cur = set(), None, None
    for i, lid in enumerate(seq):
        tag = BIO_I2L.get(lid, "O")
        if tag.startswith("B-"):
            if start is not None:
                spans.add((start, i - 1, cur))
            start, cur = i, tag[2:]
        elif tag.startswith("I-") and cur == tag[2:]:
            continue
        else:
            if start is not None:
                spans.add((start, i - 1, cur))
            start, cur = None, None
    if start is not None:
        spans.add((start, len(seq) - 1, cur))
    return spans


def evaluate(model, dl):
    model.eval()
    pred_spans, gold_spans = [], []
    sent_preds, sent_golds = [], []
    glob_preds, glob_golds = [], []

    with torch.no_grad():
        for b in dl:
            ids, mask, bio, s_mask, s_sent, glob = [
                b[k].to(DEVICE)
                for k in ["ids", "mask", "bio", "span_mask", "span_sent", "global"]
            ]
            _, bio_p, s_log, g_log = model(ids, mask, span_mask=s_mask)

            for i, (p_seq, g_seq) in enumerate(zip(bio_p, bio.tolist())):
                vl = int(mask[i].sum())
                pred_spans.append(extract_spans(p_seq[:vl]))
                gold_spans.append(extract_spans(g_seq[:vl]))

            valid_span = (s_sent != -100)
            if valid_span.any():
                sent_preds.extend(s_log.argmax(-1)[valid_span].cpu().tolist())
                sent_golds.extend(s_sent[valid_span].cpu().tolist())

            valid_glob = (glob != -1)
            if valid_glob.any():
                glob_preds.extend(g_log.argmax(-1)[valid_glob].cpu().tolist())
                glob_golds.extend(glob[valid_glob].cpu().tolist())

    tp  = sum(len(p & g) for p, g in zip(pred_spans, gold_spans))
    fp  = sum(len(p - g) for p, g in zip(pred_spans, gold_spans))
    fn  = sum(len(g - p) for p, g in zip(pred_spans, gold_spans))
    span_f1 = 2 * tp / (2 * tp + fp + fn + 1e-9)

    sent_f1 = f1_score(sent_golds, sent_preds, average="macro", zero_division=0) if sent_golds else 0.0
    glob_f1 = f1_score(glob_golds, glob_preds, average="macro", zero_division=0) if glob_golds else 0.0

    composite = 0.5 * span_f1 + 0.3 * sent_f1 + 0.2 * glob_f1
    return composite, span_f1, sent_f1, glob_f1

# =========================
# TRAINING
# =========================
def train():
    set_seed()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    print("Loading data...")
    train_ds = ABSADataset(TRAIN_FILE, tokenizer)
    val_ds   = ABSADataset(VAL_FILE,   tokenizer)
    train_dl = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,  num_workers=2, pin_memory=True)
    val_dl   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False, num_workers=2, pin_memory=True)
    print(f"Train: {len(train_ds)} records | Val: {len(val_ds)} records")

    model = ABSAModel().to(DEVICE)

    opt = AdamW([
        {"params": model.backbone.parameters(),
         "lr": LR_BACKBONE, "weight_decay": 0.01},
        {"params": [p for n, p in model.named_parameters() if "backbone" not in n],
         "lr": LR_HEADS,    "weight_decay": 0.0},
    ])

    total_steps  = EPOCHS * len(train_dl)
    warmup_steps = int(total_steps * WARMUP_RATIO)
    scheduler    = get_linear_schedule_with_warmup(opt, warmup_steps, total_steps)

    best_f1, patience_cnt = 0.0, 0

    # CSV log
    csv_file = open(CSV_LOG, "w", newline="", encoding="utf-8")
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(["epoch", "phase", "train_loss", "span_f1", "sent_f1", "glob_f1", "composite", "is_best"])

    print(f"Device: {DEVICE} | Steps: {total_steps} | Warmup: {warmup_steps}")
    print(f"Phase 1: epoch 1-{PHASE1_EPOCHS} (BIO+Global only)")
    print(f"Phase 2: epoch {PHASE1_EPOCHS+1}-{EPOCHS} (full loss)\n")

    for ep in range(1, EPOCHS + 1):
        model.train()
        total_loss = 0.0
        in_phase1  = (ep <= PHASE1_EPOCHS)
        phase_tag  = "BIO" if in_phase1 else "FULL"

        pbar = tqdm(train_dl, desc=f"Epoch {ep:02d}/{EPOCHS} [{phase_tag}]")
        for b in pbar:
            ids, mask, bio, span_mask, span_sent, g = [
                b[k].to(DEVICE)
                for k in ["ids", "mask", "bio", "span_mask", "span_sent", "global"]
            ]
            opt.zero_grad()

            if in_phase1:
                # Phase 1: skip span computation entirely to save VRAM
                crf_l, _, _, g_logits = model(ids, mask, span_mask=None, bio=bio)
                l_s    = torch.tensor(0.0, device=DEVICE)
                l_cons = torch.tensor(0.0, device=DEVICE)
            else:
                crf_l, _, s_logits, g_logits = model(ids, mask, span_mask, bio)

                # Span sentiment loss (ignore_index handles -100 padding slots)
                l_s = F.cross_entropy(
                    s_logits.view(-1, N_SENT), span_sent.view(-1), ignore_index=-100
                )

                # Consistency loss: span avg ≈ global
                valid_mask = (span_sent != -100).float()
                if valid_mask.sum() > 0:
                    span_avg = (s_logits * valid_mask.unsqueeze(-1)).sum(1) / \
                               valid_mask.sum(1, keepdim=True).clamp(min=1)
                    l_cons = F.kl_div(
                        F.log_softmax(span_avg, dim=-1),
                        F.softmax(g_logits.detach(), dim=-1),
                        reduction="batchmean",
                    )
                else:
                    l_cons = torch.tensor(0.0, device=DEVICE)

            valid_g = (g != -1)
            l_g = F.cross_entropy(g_logits[valid_g], g[valid_g]) if valid_g.any() \
                  else torch.tensor(0.0, device=DEVICE)

            loss = LAMBDA_BIO * crf_l + LAMBDA_GLOBAL * l_g + LAMBDA_SENT * l_s + LAMBDA_CONS * l_cons

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            scheduler.step()

            total_loss += loss.item()
            pbar.set_postfix({
                "loss": f"{loss.item():.4f}",
                "lr":   f"{scheduler.get_last_lr()[0]:.2e}",
            })

        composite, span_f1, sent_f1, glob_f1 = evaluate(model, val_dl)
        avg_loss = total_loss / len(train_dl)
        print(
            f"Ep {ep:02d} | loss={avg_loss:.4f} | "
            f"span={span_f1:.4f}  sent={sent_f1:.4f}  glob={glob_f1:.4f} | "
            f"composite={composite:.4f}"
        )

        # Reset early-stop at phase boundary — phase 2 needs a fresh start
        if ep == PHASE1_EPOCHS:
            csv_writer.writerow([ep, "phase1", f"{avg_loss:.4f}", f"{span_f1:.4f}", f"{sent_f1:.4f}", f"{glob_f1:.4f}", f"{composite:.4f}", ""])
            csv_file.flush()
            best_f1, patience_cnt = 0.0, 0
            print(f"--- Phase 2 start: early-stop counter reset ---")
            continue

        is_best = composite > best_f1
        if is_best:
            best_f1, patience_cnt = composite, 0
            torch.save(model.state_dict(), MODEL_SAVE)
            print(f"  ⭐ Saved best model  (composite={best_f1:.4f})")
        else:
            patience_cnt += 1

        phase_label = "phase1" if in_phase1 else "phase2"
        csv_writer.writerow([ep, phase_label, f"{avg_loss:.4f}", f"{span_f1:.4f}", f"{sent_f1:.4f}", f"{glob_f1:.4f}", f"{composite:.4f}", "best" if is_best else ""])
        csv_file.flush()

        if patience_cnt >= PATIENCE:
            print(f"Early stopping at epoch {ep}.")
            break

    csv_file.close()
    print(f"\nDone. Best composite F1: {best_f1:.4f}")
    print(f"Log saved to {CSV_LOG}")


if __name__ == "__main__":
    train()
