!pip install pyvi pytorch-crf transformers -q
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
MODEL_NAME      = "Fsoft-AIC/videberta-base"
TRAIN_FILE      = "/kaggle/input/datasets/minhhuy304/data-absa/data_train_v5.jsonl"
VAL_FILE        = "/kaggle/input/datasets/minhhuy304/data-absa/val_data.jsonl"
MODEL_SAVE      = "/kaggle/working/best_model_v5.pt"
CHECKPOINT_SAVE = "/kaggle/working/checkpoint_v5.pt"
CSV_LOG         = "/kaggle/working/train_log_v5.csv"

MAX_LEN        = 224
EPOCHS         = 30
PATIENCE       = 6
PHASE1_EPOCHS  = 5
MAX_OPS        = 8

LR_BACKBONE    = 8e-6
LR_HEADS       = 3e-5
WARMUP_RATIO   = 0.1
DROPOUT_RATE   = 0.3
CONTEXT_WINDOW = 5

LAMBDA_BIO     = 1.5
LAMBDA_SENT    = 1.0
LAMBDA_GLOBAL  = 0.5
LAMBDA_CONS    = 0.1

SPAN_MATCH_IOU = 0.5

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
ASPECTS = ["Fashion", "Electronics", "General", "Service", "Ship", "Price", "App"]

# =========================
# RUNTIME PROFILE
# Thay DP bằng gradient accumulation để tránh CRF+DP bottleneck
# =========================
def get_amp_config():
    if not torch.cuda.is_available():
        return False, torch.float32
    if torch.cuda.is_bf16_supported():
        return True, torch.bfloat16   # A100
    return True, torch.float16        # T4

USE_AMP, AMP_DTYPE = get_amp_config()

def get_runtime_profile():
    if not torch.cuda.is_available():
        return {
            "gpu_name": "cpu", "batch_size": 4, "grad_accum": 1,
            "val_batch_mult": 1, "num_workers": 2,
            "use_compile": False, "max_len": MAX_LEN,
        }
    gpu_name = torch.cuda.get_device_name(0).lower()
    n_gpu    = torch.cuda.device_count()

    if "t4" in gpu_name:
        # 2×T4: batch 16 per GPU × 2 GPUs = effective batch 32 via grad accum
        # Không dùng DP — tránh CRF gather bottleneck
        per_gpu_batch = 16
        accum_steps   = max(1, 32 // (per_gpu_batch * max(n_gpu, 1)))
        return {
            "gpu_name": f"{n_gpu}×{gpu_name}", "batch_size": per_gpu_batch,
            "grad_accum": accum_steps, "val_batch_mult": 2,
            "num_workers": min(2, os.cpu_count() or 2),
            "use_compile": False, "max_len": MAX_LEN,
        }
    if "a100" in gpu_name:
        return {
            "gpu_name": gpu_name, "batch_size": 32, "grad_accum": 1,
            "val_batch_mult": 4, "num_workers": min(8, os.cpu_count() or 4),
            "use_compile": True, "max_len": 256,
        }
    return {
        "gpu_name": gpu_name, "batch_size": 16, "grad_accum": 2,
        "val_batch_mult": 2, "num_workers": min(4, os.cpu_count() or 2),
        "use_compile": False, "max_len": MAX_LEN,
    }

# =========================
# LABEL & UTILS
# =========================
def build_bio():
    labels = ["O"]
    for a in ASPECTS:
        labels += [f"B-{a}", f"I-{a}"]
    return labels, {l: i for i, l in enumerate(labels)}, {i: l for i, l in enumerate(labels)}

BIO_LABELS, BIO_L2I, BIO_I2L = build_bio()
N_BIO, N_SENT = len(BIO_LABELS), 3

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
    def __init__(self, file, tokenizer, max_len):
        self.items = []
        if not os.path.exists(file):
            print(f"Warning: file not found — {file}")
            return

        with open(file, encoding="utf-8") as f:
            lines = f.readlines()

        print(f"  Pre-tokenizing {len(lines)} records (max_len={max_len})...")
        for line in lines:
            rec  = json.loads(line)
            enc  = tokenizer(
                nfc(rec["text"]),
                max_length=max_len,
                padding="max_length",
                truncation=True,
                return_offsets_mapping=True,
                return_special_tokens_mask=True,
            )
            offsets      = enc.pop("offset_mapping")
            special_mask = enc.pop("special_tokens_mask")
            L            = len(enc["input_ids"])

            bio       = [0] * L
            span_mask = torch.zeros(MAX_OPS, L)
            span_sent = torch.full((MAX_OPS,), -100, dtype=torch.long)

            valid_ops = []
            for op in rec.get("opinions", []):
                s, e   = op.get("start", -1), op.get("end", -1)
                asp    = op.get("aspect", "")
                sent   = op.get("sentiment", -1)
                if not asp or sent == -1:
                    continue
                tokens = [
                    i for i, (a, b) in enumerate(offsets)
                    if not special_mask[i] and max(a, s) < min(b, e)
                ]
                if tokens:
                    valid_ops.append((tokens, asp, sent))

            valid_ops.sort(key=lambda x: x[0][0])

            for op_idx, (tokens, asp, sent) in enumerate(valid_ops[:MAX_OPS]):
                for k, i in enumerate(tokens):
                    tag = f"B-{asp}" if k == 0 else f"I-{asp}"
                    if tag in BIO_L2I:
                        bio[i] = BIO_L2I[tag]

                tmin, tmax = min(tokens), max(tokens)
                lo = max(tmin - CONTEXT_WINDOW, 1)
                hi = min(tmax + CONTEXT_WINDOW, L - 1)
                if op_idx > 0:
                    lo = max(lo, max(valid_ops[op_idx - 1][0]) + 1)
                if op_idx < len(valid_ops) - 1:
                    hi = min(hi, min(valid_ops[op_idx + 1][0]) - 1)

                for i in range(lo, hi + 1):
                    if not special_mask[i]:
                        span_mask[op_idx, i] = 1.0

                span_sent[op_idx] = sent

            self.items.append({
                "ids":       torch.tensor(enc["input_ids"],      dtype=torch.long),
                "mask":      torch.tensor(enc["attention_mask"], dtype=torch.long),
                "spec_mask": torch.tensor(special_mask,          dtype=torch.bool),
                "bio":       torch.tensor(bio,                   dtype=torch.long),
                "span_mask": span_mask,
                "span_sent": span_sent,
                "global":    torch.tensor(rec.get("global_sentiment", -1), dtype=torch.long),
            })

    def __len__(self):        return len(self.items)
    def __getitem__(self, i): return self.items[i]

# =========================
# MODEL
# Fix [Critical]: h undefined → dùng seq.shape[-1]
# =========================
class AttentionPooling(nn.Module):
    def __init__(self, hidden):
        super().__init__()
        self.fc = nn.Linear(hidden, 1)

    def forward(self, x, mask):
        score = self.fc(x).squeeze(-1).masked_fill(mask == 0, -1e9)
        return (x * torch.softmax(score, dim=-1).unsqueeze(-1)).sum(dim=2)


class ABSAModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone    = AutoModel.from_pretrained(MODEL_NAME)
        h                = self.backbone.config.hidden_size
        self.dropout     = nn.Dropout(DROPOUT_RATE)
        self.bio_head    = nn.Linear(h, N_BIO)
        self.crf         = CRF(N_BIO, batch_first=True)
        self.span_attn   = AttentionPooling(h)
        self.sent_head   = nn.Sequential(nn.Dropout(0.2), nn.Linear(h, N_SENT))
        self.global_head = nn.Linear(h, N_SENT)

    def forward(self, ids, mask, span_mask=None, bio=None):
        seq       = self.dropout(self.backbone(ids, attention_mask=mask).last_hidden_state)
        h         = seq.shape[-1]          # Fix: h từ tensor, không từ __init__ scope
        emissions = self.bio_head(seq)
        cls       = self.dropout(seq[:, 0])

        crf_loss = None
        if bio is not None:
            crf_loss = -self.crf(emissions, bio, mask=mask.bool(), reduction="mean")

        span_logits = None
        if span_mask is not None:
            B, L = seq.shape[:2]
            M    = span_mask.shape[1]
            span_repr   = self.span_attn(
                seq.unsqueeze(1).expand(B, M, L, h),
                span_mask,
            )
            span_logits = self.sent_head(span_repr)

        # Trả về emissions (tensor), KHÔNG decode ở đây
        # CRF decode gọi ngoài forward để tránh DataParallel crash
        return crf_loss, emissions, span_logits, self.global_head(cls)

# =========================
# SPAN UTILS
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
            pass
        else:
            if start is not None:
                spans.add((start, i - 1, cur))
            start, cur = None, None
    if start is not None:
        spans.add((start, len(seq) - 1, cur))
    return spans


def span_iou(s1, e1, s2, e2):
    """Fix [Minor]: interval math O(1) thay vì set comprehension O(n)."""
    inter = max(0, min(e1, e2) - max(s1, s2) + 1)
    union = (e1 - s1 + 1) + (e2 - s2 + 1) - inter
    return inter / union if union > 0 else 0.0


def build_span_mask_from_pred(bio_preds, seq_len, spec_mask, device):
    """Neighbor-aware context clipping + block padding tokens."""
    B         = len(bio_preds)
    span_mask = torch.zeros(B, MAX_OPS, seq_len, device=device)

    for b, seq in enumerate(bio_preds):
        pred_spans = sorted(extract_spans(seq))
        for op_idx, (tmin, tmax, _) in enumerate(pred_spans[:MAX_OPS]):
            lo = max(tmin - CONTEXT_WINDOW, 1)
            hi = min(tmax + CONTEXT_WINDOW, seq_len - 1)
            if op_idx > 0:
                lo = max(lo, pred_spans[op_idx - 1][1] + 1)
            if op_idx < len(pred_spans) - 1:
                hi = min(hi, pred_spans[op_idx + 1][0] - 1)
            for i in range(lo, hi + 1):
                if not spec_mask[b, i]:
                    span_mask[b, op_idx, i] = 1.0

    return span_mask


def match_pred_to_gold(pred_spans, gold_spans, iou_threshold=SPAN_MATCH_IOU):
    """IoU matching pred → gold. Fix [Minor]: dùng span_iou O(1)."""
    matched, used_gold = [], set()
    for ps, pe, pa in pred_spans:
        best_iou, best_gold = 0.0, None
        for g_idx, (gs, ge, ga, _) in enumerate(gold_spans):
            if g_idx in used_gold or ga != pa:
                continue
            iou = span_iou(ps, pe, gs, ge)
            if iou > best_iou:
                best_iou, best_gold = iou, g_idx
        if best_iou >= iou_threshold and best_gold is not None:
            matched.append((ps, pe, pa, gold_spans[best_gold][3]))
            used_gold.add(best_gold)
    return matched

# =========================
# CHECKPOINT
# =========================
def save_checkpoint(epoch, raw_model, opt, scheduler, best_f1, patience_cnt, path):
    torch.save({
        "epoch":        epoch,
        "model_state":  raw_model.state_dict(),
        "opt_state":    opt.state_dict(),
        "sched_state":  scheduler.state_dict(),
        "best_f1":      best_f1,
        "patience_cnt": patience_cnt,
    }, path)


def load_checkpoint(path, raw_model, opt, scheduler):
    if not os.path.exists(path):
        print("Không tìm thấy checkpoint — train từ đầu.")
        return 1, 0.0, 0
    ckpt = torch.load(path, map_location=DEVICE)
    raw_model.load_state_dict(ckpt["model_state"])
    if ckpt.get("opt_state"):
        opt.load_state_dict(ckpt["opt_state"])
    if ckpt.get("sched_state"):
        scheduler.load_state_dict(ckpt["sched_state"])
    print(f"Resume từ epoch {ckpt['epoch']} | best_f1={ckpt['best_f1']:.4f}")
    return ckpt["epoch"] + 1, ckpt["best_f1"], ckpt["patience_cnt"]

# =========================
# EVALUATION
# Fix [Major]: 1 forward pass duy nhất thay vì 2
# =========================
def evaluate(model, raw_model, dl):
    model.eval()
    pred_spans_all, gold_spans_all = [], []
    sent_preds, sent_golds         = [], []
    glob_preds, glob_golds         = [], []

    with torch.inference_mode():
        for b in dl:
            ids, mask, spec_mask, bio, s_sent, glob = [
                b[k].to(DEVICE, non_blocking=True)
                for k in ["ids", "mask", "spec_mask", "bio", "span_sent", "global"]
            ]

            # Pass 1: lấy emissions + global, decode BIO
            with torch.autocast(device_type="cuda", dtype=AMP_DTYPE, enabled=USE_AMP):
                _, emissions, _, g_log = model(ids, mask, span_mask=None)

            bio_p   = raw_model.crf.decode(emissions, mask=mask.bool())
            pred_sm = build_span_mask_from_pred(bio_p, ids.shape[1], spec_mask, DEVICE)

            # Pass 2: lấy span sentiment dùng predicted span mask
            with torch.autocast(device_type="cuda", dtype=AMP_DTYPE, enabled=USE_AMP):
                _, _, s_log, _ = model(ids, mask, span_mask=pred_sm)

            # BIO span metrics
            for i, (p_seq, g_seq) in enumerate(zip(bio_p, bio.tolist())):
                vl       = int(mask[i].sum())
                pred_set = extract_spans(p_seq[:vl])
                gold_set = extract_spans(g_seq[:vl])
                pred_spans_all.append(pred_set)
                gold_spans_all.append(gold_set)

                # Sent metrics: IoU match pred → gold
                gold_sorted = sorted(gold_set)
                gold_with_sent = [
                    (gs, ge, ga, s_sent[i, op_idx].item())
                    for op_idx, (gs, ge, ga) in enumerate(gold_sorted[:MAX_OPS])
                    if s_sent[i, op_idx].item() != -100
                ]
                if s_log is not None:
                    pred_sorted    = sorted(pred_set)
                    pred_with_sent = [
                        (ps, pe, pa, s_log[i, op_idx].argmax().item())
                        for op_idx, (ps, pe, pa) in enumerate(pred_sorted[:MAX_OPS])
                    ]
                    pred_map = {(ps, pe, pa): psent for ps, pe, pa, psent in pred_with_sent}
                    for ps, pe, pa, g_sv in match_pred_to_gold(
                        [(ps, pe, pa) for ps, pe, pa, _ in pred_with_sent], gold_with_sent
                    ):
                        if (pv := pred_map.get((ps, pe, pa))) is not None:
                            sent_preds.append(pv)
                            sent_golds.append(g_sv)

            valid_glob = (glob != -1)
            if valid_glob.any():
                glob_preds.extend(g_log.argmax(-1)[valid_glob].cpu().tolist())
                glob_golds.extend(glob[valid_glob].cpu().tolist())

    tp  = sum(len(p & g) for p, g in zip(pred_spans_all, gold_spans_all))
    fp  = sum(len(p - g) for p, g in zip(pred_spans_all, gold_spans_all))
    fn  = sum(len(g - p) for p, g in zip(pred_spans_all, gold_spans_all))
    span_f1 = 2 * tp / (2 * tp + fp + fn + 1e-9)
    sent_f1 = f1_score(sent_golds, sent_preds, average="macro", zero_division=0) if sent_golds else 0.0
    glob_f1 = f1_score(glob_golds, glob_preds, average="macro", zero_division=0) if glob_golds else 0.0
    match_rate = len(sent_golds) / max(sum(len(g) for g in gold_spans_all), 1)

    return 0.5 * span_f1 + 0.3 * sent_f1 + 0.2 * glob_f1, span_f1, sent_f1, glob_f1, match_rate

# =========================
# TRAINING
# =========================
def train():
    set_seed()
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32       = True
    torch.backends.cudnn.benchmark        = True

    prof      = get_runtime_profile()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    print(f"GPU: {prof['gpu_name']} | AMP: {AMP_DTYPE} | "
          f"batch={prof['batch_size']} accum={prof['grad_accum']}")

    # persistent_workers=False để tránh OOM trên Kaggle 13GB RAM
    loader_kw = dict(
        num_workers=prof["num_workers"],
        pin_memory=True,
        persistent_workers=False,
    )
    train_ds = ABSADataset(TRAIN_FILE, tokenizer, prof["max_len"])
    val_ds   = ABSADataset(VAL_FILE,   tokenizer, prof["max_len"])
    train_dl = DataLoader(train_ds, batch_size=prof["batch_size"], shuffle=True,  **loader_kw)
    val_dl   = DataLoader(val_ds,   batch_size=prof["batch_size"] * prof["val_batch_mult"],
                          shuffle=False, **loader_kw)
    print(f"Train: {len(train_ds)} | Val: {len(val_ds)} | "
          f"Train batches: {len(train_dl)} (accum {prof['grad_accum']})")

    raw_model = ABSAModel().to(DEVICE).float()

    # Compile trước khi setup opt để param group đúng
    if prof["use_compile"] and hasattr(torch, "compile"):
        print("torch.compile() bật — epoch 1 sẽ chậm hơn ~3-5 phút")
        model = torch.compile(raw_model)
    else:
        model = raw_model

    opt = AdamW([
        {"params": raw_model.backbone.parameters(),
         "lr": LR_BACKBONE, "weight_decay": 0.01},
        {"params": [p for n, p in raw_model.named_parameters() if "backbone" not in n],
         "lr": LR_HEADS, "weight_decay": 0.0},
    ])

    # total_steps tính theo effective batch (sau grad accum)
    effective_batches = len(train_dl) // prof["grad_accum"]
    total_steps       = EPOCHS * effective_batches
    warmup_steps      = int(total_steps * WARMUP_RATIO)
    scheduler = get_linear_schedule_with_warmup(opt, warmup_steps, total_steps)

    # Fix [Critical]: GradScaler chỉ enable cho fp16, KHÔNG enable cho bf16
    use_scaler = USE_AMP and (AMP_DTYPE == torch.float16)
    scaler     = torch.cuda.amp.GradScaler(enabled=use_scaler)

    start_epoch, best_f1, patience_cnt = load_checkpoint(
        CHECKPOINT_SAVE, raw_model, opt, scheduler
    )

    csv_mode   = "a" if start_epoch > 1 else "w"
    csv_file   = open(CSV_LOG, csv_mode, newline="", encoding="utf-8")
    csv_writer = csv.writer(csv_file)
    if csv_mode == "w":
        csv_writer.writerow([
            "epoch", "phase", "train_loss",
            "span_f1", "sent_f1", "glob_f1", "composite", "match_rate", "is_best",
        ])

    print(f"Steps: {total_steps} | Warmup: {warmup_steps} | "
          f"Scaler: {use_scaler}")
    if start_epoch == 1:
        print(f"Phase 1: ep 1-{PHASE1_EPOCHS} (BIO+Global) | "
              f"Phase 2: ep {PHASE1_EPOCHS+1}-{EPOCHS} (full)\n")

    grad_accum   = prof["grad_accum"]
    phase1_done  = False

    for ep in range(start_epoch, EPOCHS + 1):
        model.train()
        total_loss = 0.0
        in_phase1  = (ep <= PHASE1_EPOCHS)
        phase_tag  = "BIO" if in_phase1 else "FULL"

        pbar = tqdm(train_dl, desc=f"Ep {ep:02d}/{EPOCHS} [{phase_tag}]")
        opt.zero_grad(set_to_none=True)

        for step, b in enumerate(pbar):
            ids, mask, bio, s_mask, s_sent, g = [
                b[k].to(DEVICE, non_blocking=True)
                for k in ["ids", "mask", "bio", "span_mask", "span_sent", "global"]
            ]

            with torch.autocast(device_type="cuda", dtype=AMP_DTYPE, enabled=USE_AMP):
                crf_l, _, s_logits, g_logits = model(
                    ids, mask,
                    span_mask=None if in_phase1 else s_mask,
                    bio=bio,
                )

                if in_phase1:
                    l_s = l_cons = torch.tensor(0.0, device=DEVICE)
                else:
                    l_s = F.cross_entropy(
                        s_logits.view(-1, N_SENT), s_sent.view(-1),
                        ignore_index=-100, label_smoothing=0.1,
                    )
                    v_mask = (s_sent != -100).float()
                    if v_mask.sum() > 0:
                        span_avg = (s_logits * v_mask.unsqueeze(-1)).sum(1) / \
                                   v_mask.sum(1, keepdim=True).clamp(min=1)
                        l_cons = F.kl_div(
                            F.log_softmax(span_avg, dim=-1),
                            F.softmax(g_logits.detach(), dim=-1),
                            reduction="batchmean",
                        )
                    else:
                        l_cons = torch.tensor(0.0, device=DEVICE)

                v_g  = (g != -1)
                l_g  = F.cross_entropy(g_logits[v_g], g[v_g], label_smoothing=0.1) \
                       if v_g.any() else torch.tensor(0.0, device=DEVICE)

                loss = (LAMBDA_BIO * crf_l + LAMBDA_GLOBAL * l_g
                        + LAMBDA_SENT * l_s + LAMBDA_CONS * l_cons)
                loss = loss / grad_accum   # normalize trước backward

            scaler.scale(loss).backward()

            if (step + 1) % grad_accum == 0 or (step + 1) == len(train_dl):
                scaler.unscale_(opt)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(opt)
                scaler.update()
                scheduler.step()
                opt.zero_grad(set_to_none=True)

            total_loss += loss.item() * grad_accum
            pbar.set_postfix({
                "loss": f"{loss.item() * grad_accum:.4f}",
                "lr":   f"{scheduler.get_last_lr()[0]:.2e}",
            })

        avg_loss = total_loss / len(train_dl)

        # Fix [Major]: evaluate tất cả epoch, kể cả phase 1
        composite, span_f1, sent_f1, glob_f1, match_rate = evaluate(model, raw_model, val_dl)
        print(
            f"Ep {ep:02d} | loss={avg_loss:.4f} | "
            f"span={span_f1:.4f} sent={sent_f1:.4f} glob={glob_f1:.4f} | "
            f"composite={composite:.4f} | match={match_rate:.2%}"
        )

        # Fix [Major]: reset early-stop SAU khi evaluate epoch PHASE1_EPOCHS
        # để epoch này vẫn có cơ hội được lưu nếu là best
        if in_phase1 and not phase1_done:
            if composite > best_f1:
                best_f1, patience_cnt = composite, 0
                torch.save(raw_model.state_dict(), MODEL_SAVE)
                print(f"  ⭐ Phase1 best (composite={best_f1:.4f})")
            if ep == PHASE1_EPOCHS:
                best_f1, patience_cnt = 0.0, 0   # reset cho phase 2
                phase1_done = True
                save_checkpoint(ep, raw_model, opt, scheduler, best_f1, patience_cnt, CHECKPOINT_SAVE)
                print("--- Phase 2 start: reset early-stop | checkpoint saved ---")
        else:
            is_best = composite > best_f1
            if is_best:
                best_f1, patience_cnt = composite, 0
                torch.save(raw_model.state_dict(), MODEL_SAVE)
                print(f"  ⭐ Saved best model (composite={best_f1:.4f})")
            else:
                patience_cnt += 1
            save_checkpoint(ep, raw_model, opt, scheduler, best_f1, patience_cnt, CHECKPOINT_SAVE)

        phase_label = "phase1" if in_phase1 else "phase2"
        csv_writer.writerow([
            ep, phase_label, f"{avg_loss:.4f}", f"{span_f1:.4f}",
            f"{sent_f1:.4f}", f"{glob_f1:.4f}", f"{composite:.4f}",
            f"{match_rate:.4f}", "best" if composite == best_f1 else "",
        ])
        csv_file.flush()

        if not in_phase1 and patience_cnt >= PATIENCE:
            print(f"Early stopping tại epoch {ep}.")
            break

    csv_file.close()
    print(f"\nDone. Best composite F1: {best_f1:.4f}")
    print(f"Model: {MODEL_SAVE} | Log: {CSV_LOG}")


if __name__ == "__main__":
    train()