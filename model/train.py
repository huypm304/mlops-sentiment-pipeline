# =============================================================================
# ABSA v5 - A100 Optimized | Fixed Evaluation Pipeline
# Fixes:
#   [Critical] sent_f1 dùng span matching thay vì index alignment
#   [Major]    build_span_mask_from_pred clip context theo neighbor spans
#   [Major]    composite metric dùng sent_f1 đúng → best checkpoint đúng
#   [Minor]    torch.compile tách khỏi checkpoint, resume-safe
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
MODEL_NAME      = "Fsoft-AIC/videberta-base"
TRAIN_FILE      = "/content/data_train_v5.jsonl"
VAL_FILE        = "/content/val_data.jsonl"
CHECKPOINT_SAVE = "checkpoint_v5.pt"
MODEL_SAVE      = "best_model_v5.pt"
CSV_LOG         = "train_log_v5.csv"

MAX_LEN        = 224
BATCH_SIZE     = 16
EPOCHS         = 30
PATIENCE       = 6
PHASE1_EPOCHS  = 5
MAX_OPS        = 8
VAL_BATCH_MULT = 2
NUM_WORKERS    = min(4, os.cpu_count() or 2)
PREFETCH_FACTOR = 2

LR_BACKBONE    = 8e-6
LR_HEADS       = 2e-5
WARMUP_RATIO   = 0.1
DROPOUT_RATE   = 0.3
CONTEXT_WINDOW = 5

LAMBDA_BIO     = 1.5
LAMBDA_SENT    = 1.0
LAMBDA_GLOBAL  = 0.5
LAMBDA_CONS    = 0.1

# Ngưỡng IoU để coi predicted span match gold span
SPAN_MATCH_IOU = 0.5

DEVICE   = torch.device("cuda" if torch.cuda.is_available() else "cpu")
USE_BF16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
ASPECTS  = ["Fashion", "Electronics", "General", "Service", "Ship", "Price", "App"]


def get_runtime_profile():
    if not torch.cuda.is_available():
        return {
            "gpu_name": "cpu",
            "batch_size": 4,
            "val_batch_mult": 1,
            "num_workers": 2,
            "prefetch_factor": 2,
            "use_compile": False,
            "max_len": MAX_LEN,
        }

    gpu_name = torch.cuda.get_device_name(0).lower()
    if "t4" in gpu_name:
        return {
            "gpu_name": gpu_name,
            "batch_size": 16,
            "val_batch_mult": 2,
            "num_workers": min(2, os.cpu_count() or 2),
            "prefetch_factor": 2,
            "use_compile": False,
            "max_len": MAX_LEN,
        }
    if "a100" in gpu_name:
        return {
            "gpu_name": gpu_name,
            "batch_size": 32,
            "val_batch_mult": 4,
            "num_workers": min(8, os.cpu_count() or 4),
            "prefetch_factor": 4,
            "use_compile": True,
            "max_len": 256,
        }
    return {
        "gpu_name": gpu_name,
        "batch_size": BATCH_SIZE,
        "val_batch_mult": VAL_BATCH_MULT,
        "num_workers": NUM_WORKERS,
        "prefetch_factor": PREFETCH_FACTOR,
        "use_compile": False,
        "max_len": MAX_LEN,
    }

# =========================
# LABEL & UTILS
# =========================
def build_bio():
    labels = ["O"]
    for a in ASPECTS:
        labels += [f"B-{a}", f"I-{a}"]
    l2i = {l: i for i, l in enumerate(labels)}
    i2l = {i: l for i, l in enumerate(labels)}
    return labels, l2i, i2l

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
        self.max_len = max_len
        if not os.path.exists(file):
            print(f"Warning: File not found at {file}")
            return

        with open(file, encoding="utf-8") as f:
            lines = f.readlines()

        print(f"  Pre-tokenizing {len(lines)} records...")
        for line in lines:
            rec  = json.loads(line)
            text = nfc(rec["text"])

            enc = tokenizer(
                text,
                max_length=self.max_len,
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

            valid_ops.sort(key=lambda x: x[0][0])

            for op_idx, (tokens, asp, sent) in enumerate(valid_ops[:MAX_OPS]):
                for k, i in enumerate(tokens):
                    tag = f"B-{asp}" if k == 0 else f"I-{asp}"
                    if tag in BIO_L2I:
                        bio[i] = BIO_L2I[tag]

                tmin, tmax = min(tokens), max(tokens)

                lo = tmin - CONTEXT_WINDOW
                if op_idx > 0:
                    prev_end = max(valid_ops[op_idx - 1][0])
                    lo = max(lo, prev_end + 1)
                lo = max(lo, 1)

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
                "ids":       torch.tensor(enc["input_ids"],      dtype=torch.long),
                "mask":      torch.tensor(enc["attention_mask"], dtype=torch.long),
                "bio":       torch.tensor(bio,                   dtype=torch.long),
                "span_mask": span_mask,
                "span_sent": span_sent,
                "global":    torch.tensor(rec.get("global_sentiment", -1), dtype=torch.long),
            })

    def __len__(self):        return len(self.items)
    def __getitem__(self, i): return self.items[i]

# =========================
# MODEL
# =========================
class AttentionPooling(nn.Module):
    def __init__(self, hidden):
        super().__init__()
        self.fc = nn.Linear(hidden, 1)

    def forward(self, x, mask):
        score = self.fc(x).squeeze(-1).masked_fill(mask == 0, -1e9)
        w     = torch.softmax(score, dim=-1)
        return (x * w.unsqueeze(-1)).sum(dim=2)


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
        out       = self.backbone(ids, attention_mask=mask)
        seq       = self.dropout(out.last_hidden_state)
        cls       = self.dropout(seq[:, 0])
        emissions = self.bio_head(seq)
        mask_bool = mask.bool()

        crf_loss = None
        if bio is not None:
            crf_loss = -self.crf(emissions, bio, mask=mask_bool, reduction="mean")

        bio_pred      = self.crf.decode(emissions, mask=mask_bool)
        global_logits = self.global_head(cls)

        span_logits = None
        if span_mask is not None:
            B, L, H   = seq.shape
            M         = span_mask.shape[1]
            seq_exp   = seq.unsqueeze(1).expand(B, M, L, H)
            span_repr = self.span_attn(seq_exp, span_mask)
            span_logits = self.sent_head(span_repr)

        return crf_loss, bio_pred, span_logits, global_logits

# =========================
# SPAN UTILS
# =========================
def extract_spans(seq):
    """Parse BIO sequence → set of (start, end, aspect)."""
    spans, start, cur = set(), None, None
    for i, lid in enumerate(seq):
        tag = BIO_I2L.get(lid, "O")
        if tag.startswith("B-"):
            if start is not None:
                spans.add((start, i - 1, cur))
            start, cur = i, tag[2:]
        elif tag.startswith("I-") and cur and cur == tag[2:]:
            pass
        else:
            if start is not None:
                spans.add((start, i - 1, cur))
            start, cur = None, None
    if start is not None:
        spans.add((start, len(seq) - 1, cur))
    return spans


def build_span_mask_from_pred(bio_preds, seq_len, device):
    """
    Tạo span_mask từ predicted BIO.
    Context window được clip theo neighbor spans — đồng nhất với dataset builder.
    Fix [Major]: thêm neighbor-aware clipping.
    """
    B = len(bio_preds)
    span_mask = torch.zeros(B, MAX_OPS, seq_len, device=device)

    for b, seq in enumerate(bio_preds):
        # Thu thập tất cả spans trước để biết neighbor
        pred_spans = sorted(extract_spans(seq))   # list of (tmin, tmax, asp)

        for op_idx, (tmin, tmax, _) in enumerate(pred_spans[:MAX_OPS]):
            lo = tmin - CONTEXT_WINDOW
            if op_idx > 0:
                prev_tmax = pred_spans[op_idx - 1][1]
                lo = max(lo, prev_tmax + 1)
            lo = max(lo, 1)

            hi = tmax + CONTEXT_WINDOW
            if op_idx < len(pred_spans) - 1:
                next_tmin = pred_spans[op_idx + 1][0]
                hi = min(hi, next_tmin - 1)
            hi = min(hi, seq_len - 1)

            if lo <= hi:
                span_mask[b, op_idx, lo:hi + 1] = 1.0

    return span_mask


def match_pred_to_gold(pred_spans, gold_spans, iou_threshold=SPAN_MATCH_IOU):
    """
    Match predicted spans → gold spans theo token-level IoU.
    Trả về list (pred_asp, gold_sent) cho các cặp matched.

    Fix [Critical]: thay vì align theo index, dùng IoU matching để
    sent_f1 phản ánh end-to-end inference thật.
    """
    matched = []
    used_gold = set()

    for p_start, p_end, p_asp in pred_spans:
        p_set = set(range(p_start, p_end + 1))
        best_iou, best_gold = 0.0, None

        for g_idx, (g_start, g_end, g_asp, g_sent) in enumerate(gold_spans):
            if g_idx in used_gold:
                continue
            if g_asp != p_asp:          # aspect phải khớp
                continue
            g_set  = set(range(g_start, g_end + 1))
            inter  = len(p_set & g_set)
            union  = len(p_set | g_set)
            iou    = inter / union if union > 0 else 0.0
            if iou > best_iou:
                best_iou, best_gold = iou, g_idx

        if best_iou >= iou_threshold and best_gold is not None:
            matched.append((p_start, p_end, p_asp, gold_spans[best_gold][3]))
            used_gold.add(best_gold)

    return matched   # list of (p_start, p_end, p_asp, gold_sent)

# =========================
# CHECKPOINT
# =========================
def save_checkpoint(epoch, model, opt, scheduler, best_f1, patience_cnt, path):
    # Unwrap compiled model trước khi save để resume-safe trên runtime khác
    # Fix [Minor]: tách compile state khỏi checkpoint
    raw = model._orig_mod if hasattr(model, "_orig_mod") else model
    torch.save({
        "epoch":        epoch,
        "model_state":  raw.state_dict(),
        "opt_state":    opt.state_dict(),
        "sched_state":  scheduler.state_dict(),
        "best_f1":      best_f1,
        "patience_cnt": patience_cnt,
    }, path)


def load_checkpoint(path, model, opt, scheduler):
    if not os.path.exists(path):
        print("Không tìm thấy checkpoint — train từ đầu.")
        return 1, 0.0, 0

    ckpt = torch.load(path, map_location=DEVICE)
    raw  = model._orig_mod if hasattr(model, "_orig_mod") else model
    raw.load_state_dict(ckpt["model_state"])
    if ckpt.get("opt_state"):
        opt.load_state_dict(ckpt["opt_state"])
    if ckpt.get("sched_state"):
        scheduler.load_state_dict(ckpt["sched_state"])

    print(f"Resume từ epoch {ckpt['epoch']} | best_f1={ckpt['best_f1']:.4f} | patience={ckpt['patience_cnt']}")
    return ckpt["epoch"] + 1, ckpt["best_f1"], ckpt["patience_cnt"]

# =========================
# EVALUATION — end-to-end pipeline
# =========================
def evaluate(model, dl):
    model.eval()

    # BIO span detection metrics
    pred_spans_all, gold_spans_all = [], []

    # sent_f1: chỉ tính trên matched spans (IoU ≥ threshold)
    sent_preds, sent_golds = [], []

    # global metrics
    glob_preds, glob_golds = [], []

    with torch.inference_mode():
        for b in dl:
            ids, mask, bio, s_mask, s_sent, glob = [
                b[k].to(DEVICE, non_blocking=True)
                for k in ["ids", "mask", "bio", "span_mask", "span_sent", "global"]
            ]

            with torch.autocast(device_type="cuda", dtype=torch.bfloat16, enabled=USE_BF16):
                _, bio_p, _, g_log = model(ids, mask, span_mask=None)

            # Build predicted span mask với neighbor-aware clipping
            pred_sm = build_span_mask_from_pred(bio_p, ids.shape[1], DEVICE)

            with torch.autocast(device_type="cuda", dtype=torch.bfloat16, enabled=USE_BF16):
                _, _, s_log, g_log = model(ids, mask, span_mask=pred_sm)

            for i, (p_seq, g_seq) in enumerate(zip(bio_p, bio.tolist())):
                vl         = int(mask[i].sum())
                pred_set   = extract_spans(p_seq[:vl])
                gold_set   = extract_spans(g_seq[:vl])
                pred_spans_all.append(pred_set)
                gold_spans_all.append(gold_set)

                # Xây gold_spans có kèm sentiment để matching
                # Lấy từ s_sent theo op_idx tương ứng với gold BIO order
                gold_sorted = sorted(gold_set)    # (start, end, asp) đã sort theo start
                gold_with_sent = []
                for op_idx, (gs, ge, ga) in enumerate(gold_sorted[:MAX_OPS]):
                    gs_val = s_sent[i, op_idx].item()
                    if gs_val != -100:
                        gold_with_sent.append((gs, ge, ga, gs_val))

                # predicted spans sorted theo start (đồng bộ với span_mask order)
                pred_sorted = sorted(pred_set)

                # Lấy predicted sentiment từ s_log theo op_idx
                pred_with_sent = []
                if s_log is not None:
                    for op_idx, (ps, pe, pa) in enumerate(pred_sorted[:MAX_OPS]):
                        p_sent = s_log[i, op_idx].argmax().item()
                        pred_with_sent.append((ps, pe, pa, p_sent))

                # IoU matching: pred → gold
                matched = match_pred_to_gold(
                    [(ps, pe, pa) for ps, pe, pa, _ in pred_with_sent],
                    gold_with_sent,
                )
                # Thu thập pred/gold sentiment cho matched pairs
                pred_sent_map = {(ps, pe, pa): psent for ps, pe, pa, psent in pred_with_sent}
                for ps, pe, pa, g_sent_val in matched:
                    p_sent_val = pred_sent_map.get((ps, pe, pa))
                    if p_sent_val is not None:
                        sent_preds.append(p_sent_val)
                        sent_golds.append(g_sent_val)

            valid_glob = (glob != -1)
            if valid_glob.any():
                glob_preds.extend(g_log.argmax(-1)[valid_glob].cpu().tolist())
                glob_golds.extend(glob[valid_glob].cpu().tolist())

    # BIO span F1
    tp  = sum(len(p & g) for p, g in zip(pred_spans_all, gold_spans_all))
    fp  = sum(len(p - g) for p, g in zip(pred_spans_all, gold_spans_all))
    fn  = sum(len(g - p) for p, g in zip(pred_spans_all, gold_spans_all))
    span_f1 = 2 * tp / (2 * tp + fp + fn + 1e-9)

    # sent_f1: chỉ trên matched spans — phản ánh end-to-end thật
    sent_f1 = f1_score(sent_golds, sent_preds, average="macro", zero_division=0) \
              if sent_golds else 0.0

    glob_f1 = f1_score(glob_golds, glob_preds, average="macro", zero_division=0) \
              if glob_golds else 0.0

    # Log thêm số matched để monitor
    match_rate = len(sent_golds) / max(sum(len(g) for g in gold_spans_all), 1)

    composite = 0.5 * span_f1 + 0.3 * sent_f1 + 0.2 * glob_f1
    return composite, span_f1, sent_f1, glob_f1, match_rate

# =========================
# TRAINING
# =========================
def train():
    set_seed()
    profile = get_runtime_profile()
    batch_size = profile["batch_size"]
    val_batch_mult = profile["val_batch_mult"]
    num_workers = profile["num_workers"]
    prefetch_factor = profile["prefetch_factor"]
    use_compile = profile["use_compile"]
    max_len = profile["max_len"]

    torch.set_float32_matmul_precision("high")
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32       = True
    torch.backends.cudnn.benchmark        = True

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    print("Loading & pre-tokenizing data...")
    train_ds = ABSADataset(TRAIN_FILE, tokenizer, max_len=max_len)
    val_ds   = ABSADataset(VAL_FILE,   tokenizer, max_len=max_len)

    train_dl = DataLoader(
        train_ds, batch_size=batch_size, shuffle=True,
        num_workers=num_workers, pin_memory=True, persistent_workers=(num_workers > 0),
        prefetch_factor=prefetch_factor if num_workers > 0 else None,
    )
    val_dl = DataLoader(
        val_ds, batch_size=batch_size * val_batch_mult, shuffle=False,
        num_workers=num_workers, pin_memory=True, persistent_workers=(num_workers > 0),
        prefetch_factor=prefetch_factor if num_workers > 0 else None,
    )
    print(
        f"Train: {len(train_ds)} | Val: {len(val_ds)} | bf16: {USE_BF16} | "
        f"gpu: {profile['gpu_name']} | batch: {batch_size} | max_len: {max_len} | workers: {num_workers}"
    )

    # Khởi tạo raw model trước compile để checkpoint load đúng
    raw_model = ABSAModel().to(DEVICE).float()

    opt = AdamW([
        {"params": raw_model.backbone.parameters(),
         "lr": LR_BACKBONE, "weight_decay": 0.01},
        {"params": [p for n, p in raw_model.named_parameters() if "backbone" not in n],
         "lr": LR_HEADS, "weight_decay": 0.0},
    ])

    total_steps  = EPOCHS * len(train_dl)
    warmup_steps = int(total_steps * WARMUP_RATIO)
    scheduler    = get_linear_schedule_with_warmup(opt, warmup_steps, total_steps)

    # Load checkpoint vào raw_model trước khi compile
    # Fix [Minor]: compile sau load → tránh mismatch khi resume
    start_epoch, best_f1, patience_cnt = load_checkpoint(
        CHECKPOINT_SAVE, raw_model, opt, scheduler
    )

    # Compile sau khi load xong
    if use_compile and hasattr(torch, "compile"):
        print("Compiling model (epoch 1 sẽ chậm hơn ~3-5 phút do JIT warmup)...")
        model = torch.compile(raw_model)
    else:
        model = raw_model

    csv_mode   = "a" if start_epoch > 1 else "w"
    csv_file   = open(CSV_LOG, csv_mode, newline="", encoding="utf-8")
    csv_writer = csv.writer(csv_file)
    if csv_mode == "w":
        csv_writer.writerow([
            "epoch", "phase", "train_loss",
            "span_f1", "sent_f1", "glob_f1", "composite",
            "match_rate", "is_best",
        ])

    print(f"\nDevice: {DEVICE} | Steps: {total_steps} | Warmup: {warmup_steps}")
    print(f"Batch: {batch_size} | AMP: {'bfloat16' if USE_BF16 else 'float16'} | compile: {use_compile}")
    if start_epoch == 1:
        print(f"Phase 1: epoch 1-{PHASE1_EPOCHS} (BIO+Global)")
        print(f"Phase 2: epoch {PHASE1_EPOCHS+1}-{EPOCHS} (full loss)\n")
    else:
        print(f"Resume từ epoch {start_epoch}\n")

    for ep in range(start_epoch, EPOCHS + 1):
        model.train()
        total_loss = 0.0
        in_phase1  = (ep <= PHASE1_EPOCHS)
        phase_tag  = "BIO" if in_phase1 else "FULL"

        pbar = tqdm(train_dl, desc=f"Ep {ep:02d}/{EPOCHS} [{phase_tag}]")
        for b in pbar:
            ids, mask, bio, span_mask, span_sent, g = [
                b[k].to(DEVICE, non_blocking=True)
                for k in ["ids", "mask", "bio", "span_mask", "span_sent", "global"]
            ]
            opt.zero_grad(set_to_none=True)

            with torch.autocast(device_type="cuda", dtype=torch.bfloat16, enabled=USE_BF16):
                if in_phase1:
                    crf_l, _, _, g_logits = model(ids, mask, span_mask=None, bio=bio)
                    l_s    = torch.tensor(0.0, device=DEVICE)
                    l_cons = torch.tensor(0.0, device=DEVICE)
                else:
                    crf_l, _, s_logits, g_logits = model(ids, mask, span_mask, bio)
                    l_s = F.cross_entropy(
                        s_logits.view(-1, N_SENT), span_sent.view(-1), ignore_index=-100
                    )
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

                loss = (LAMBDA_BIO * crf_l + LAMBDA_GLOBAL * l_g
                        + LAMBDA_SENT * l_s + LAMBDA_CONS * l_cons)

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            scheduler.step()

            total_loss += loss.item()
            pbar.set_postfix({"loss": f"{loss.item():.4f}", "lr": f"{scheduler.get_last_lr()[0]:.2e}"})

        avg_loss = total_loss / len(train_dl)

        # Phase 1 không dùng để chọn best model, nên chỉ eval ở epoch cuối phase 1
        if in_phase1 and ep < PHASE1_EPOCHS:
            print(f"Ep {ep:02d} | loss={avg_loss:.4f} | skip val (phase1 warmup)")
            save_checkpoint(ep, model, opt, scheduler, best_f1, patience_cnt, CHECKPOINT_SAVE)
            csv_writer.writerow([ep, "phase1", f"{avg_loss:.4f}", "", "", "", "", "", ""])
            csv_file.flush()
            continue

        composite, span_f1, sent_f1, glob_f1, match_rate = evaluate(model, val_dl)
        print(
            f"Ep {ep:02d} | loss={avg_loss:.4f} | "
            f"span={span_f1:.4f} sent={sent_f1:.4f} glob={glob_f1:.4f} | "
            f"composite={composite:.4f} | match={match_rate:.2%}"
        )

        if ep == PHASE1_EPOCHS:
            csv_writer.writerow([ep, "phase1", f"{avg_loss:.4f}", f"{span_f1:.4f}",
                                  f"{sent_f1:.4f}", f"{glob_f1:.4f}", f"{composite:.4f}",
                                  f"{match_rate:.4f}", ""])
            csv_file.flush()
            best_f1, patience_cnt = 0.0, 0
            save_checkpoint(ep, model, opt, scheduler, best_f1, patience_cnt, CHECKPOINT_SAVE)
            print(f"--- Phase 2 start: reset early-stop | checkpoint saved ---")
            continue

        is_best = composite > best_f1
        if is_best:
            best_f1, patience_cnt = composite, 0
            torch.save(raw_model.state_dict(), MODEL_SAVE)
            print(f"  ⭐ Saved best model (composite={best_f1:.4f})")
        else:
            patience_cnt += 1

        save_checkpoint(ep, model, opt, scheduler, best_f1, patience_cnt, CHECKPOINT_SAVE)

        phase_label = "phase1" if in_phase1 else "phase2"
        csv_writer.writerow([ep, phase_label, f"{avg_loss:.4f}", f"{span_f1:.4f}",
                              f"{sent_f1:.4f}", f"{glob_f1:.4f}", f"{composite:.4f}",
                              f"{match_rate:.4f}", "best" if is_best else ""])
        csv_file.flush()

        if patience_cnt >= PATIENCE:
            print(f"Early stopping tại epoch {ep}.")
            break

    csv_file.close()
    print(f"\nDone. Best composite F1: {best_f1:.4f}")
    print(f"Model : {MODEL_SAVE} | Log: {CSV_LOG}")


if __name__ == "__main__":
    train()