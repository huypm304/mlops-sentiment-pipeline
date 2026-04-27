import argparse
import csv
import glob
import json
import os
import random
import subprocess
import sys
import unicodedata
from contextlib import nullcontext
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.metrics import confusion_matrix, f1_score
from torch.optim import AdamW
from torch.optim.lr_scheduler import OneCycleLR
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from tqdm.auto import tqdm
from transformers import AutoModel, AutoTokenizer

os.environ.setdefault("TRITON_INTERPRET", "1")
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")


def install_deps():
    try:
        from torchcrf import CRF as _CRF  # noqa: F401
    except ImportError:
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "pytorch-crf",
                "transformers",
                "scikit-learn",
                "-q",
            ]
        )


install_deps()

from torchcrf import CRF

ASPECTS = ["Fashion", "Electronics", "General", "Service", "Ship", "Price", "App"]
N_SENT = 3


def build_bio_labels():
    labels = ["O"]
    for aspect in ASPECTS:
        labels.extend([f"B-{aspect}", f"I-{aspect}"])
    l2i = {label: idx for idx, label in enumerate(labels)}
    i2l = {idx: label for idx, label in enumerate(labels)}
    return labels, l2i, i2l


BIO_LABELS, BIO_L2I, BIO_I2L = build_bio_labels()
N_BIO = len(BIO_LABELS)


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def autocast_context(device):
    if device.type == "cuda":
        return torch.autocast(device_type="cuda", dtype=torch.float16)
    return nullcontext()


def is_gold_contrast(span_sent_tensor):
    values = span_sent_tensor[span_sent_tensor != -100]
    return len(values) >= 2 and len(values.unique()) >= 2


def extract_spans(seq):
    spans = set()
    start = None
    current_aspect = None
    for idx, label_id in enumerate(seq):
        tag = BIO_I2L.get(label_id, "O")
        if tag.startswith("B-"):
            if start is not None:
                spans.add((start, idx - 1, current_aspect))
            start = idx
            current_aspect = tag[2:]
        elif not (tag.startswith("I-") and current_aspect == tag[2:]):
            if start is not None:
                spans.add((start, idx - 1, current_aspect))
            start = None
            current_aspect = None
    if start is not None:
        spans.add((start, len(seq) - 1, current_aspect))
    return spans


def compute_window(tmin, tmax, op_idx, span_token_lists, seq_len, max_context_window):
    low = max(tmin - max_context_window, 1)
    high = min(tmax + max_context_window, seq_len - 1)
    if op_idx > 0:
        low = max(low, max(span_token_lists[op_idx - 1]) + 1)
    if op_idx < len(span_token_lists) - 1:
        high = min(high, min(span_token_lists[op_idx + 1]) - 1)
    return low, high


def confusion_payload(gold, pred, labels, label_names):
    matrix = confusion_matrix(gold, pred, labels=labels).tolist() if gold and pred else []
    normalized = []
    if matrix:
        for row in matrix:
            row_sum = sum(row)
            normalized.append([round(value / row_sum, 6) if row_sum else 0.0 for value in row])
    return {
        "labels": label_names,
        "raw": matrix,
        "normalized": normalized,
        "support": len(gold),
    }


def resolve_kaggle_path(path: Path, filename_hint: str) -> Path:
    if path.exists():
        return path
    candidates = glob.glob(f"/kaggle/input/**/{filename_hint}", recursive=True)
    if candidates:
        return Path(candidates[0])
    return path


def extract_ops(record):
    if "triplets" in record:
        for t in record.get("triplets", []):
            aspect = t.get("aspect")
            sentiment = t.get("sentiment")
            span = t.get("target_span")
            if aspect not in ASPECTS or sentiment not in {0, 1, 2}:
                continue
            if not isinstance(span, list) or len(span) != 2:
                continue
            start, end = int(span[0]), int(span[1])
            if end <= start:
                continue
            yield start, end, aspect, sentiment
    elif "opinions" in record:
        for o in record.get("opinions", []):
            aspect = o.get("aspect")
            sentiment = o.get("sentiment")
            start = o.get("start", -1)
            end = o.get("end", -1)
            if aspect not in ASPECTS or sentiment not in {0, 1, 2}:
                continue
            if not isinstance(start, int) or not isinstance(end, int) or end <= start:
                continue
            yield start, end, aspect, sentiment


class ABSADataset(Dataset):
    def __init__(self, file_path: Path, tokenizer, max_len: int, max_ops: int, max_context_window: int):
        self.items = []
        with open(file_path, encoding="utf-8") as handle:
            lines = handle.readlines()

        print(f"Pre-tokenizing {len(lines)} records from {file_path}...")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            text = nfc(record.get("text", ""))
            encoding = tokenizer(
                text,
                max_length=max_len,
                padding="max_length",
                truncation=True,
                return_offsets_mapping=True,
                return_special_tokens_mask=True,
            )
            offsets = encoding.pop("offset_mapping")
            special_mask = encoding.pop("special_tokens_mask")
            seq_len = len(encoding["input_ids"])

            bio = [0] * seq_len
            span_mask = torch.zeros(max_ops, seq_len)
            span_sent = torch.full((max_ops,), -100, dtype=torch.long)
            span_aspect = torch.full((max_ops,), len(ASPECTS), dtype=torch.long)
            valid_ops = []

            for start, end, aspect, sentiment in extract_ops(record):
                tokens = [
                    idx
                    for idx, (char_start, char_end) in enumerate(offsets)
                    if not special_mask[idx] and max(char_start, start) < min(char_end, end)
                ]
                if tokens:
                    valid_ops.append((tokens, aspect, sentiment))

            valid_ops.sort(key=lambda item: item[0][0])
            valid_ops = valid_ops[:max_ops]
            span_token_lists = [item[0] for item in valid_ops]

            for op_idx, (tokens, aspect, sentiment) in enumerate(valid_ops):
                span_aspect[op_idx] = ASPECTS.index(aspect)
                for token_idx_offset, token_idx in enumerate(tokens):
                    bio[token_idx] = BIO_L2I[f"B-{aspect}" if token_idx_offset == 0 else f"I-{aspect}"]
                low, high = compute_window(min(tokens), max(tokens), op_idx, span_token_lists, seq_len, max_context_window)
                for token_idx in range(low, high + 1):
                    if not special_mask[token_idx]:
                        span_mask[op_idx, token_idx] = 1.0
                span_sent[op_idx] = sentiment

            self.items.append(
                {
                    "ids": torch.tensor(encoding["input_ids"]),
                    "mask": torch.tensor(encoding["attention_mask"]),
                    "spec_mask": torch.tensor(special_mask, dtype=torch.bool),
                    "bio": torch.tensor(bio),
                    "span_mask": span_mask,
                    "span_sent": span_sent,
                    "span_aspect": span_aspect,
                    "global": torch.tensor(record.get("global_sentiment", -1)),
                }
            )

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        return self.items[idx]


class ABSAModel(nn.Module):
    def __init__(self, model_name: str, max_ops: int):
        super().__init__()
        self.max_ops = max_ops
        self.backbone = AutoModel.from_pretrained(model_name)
        hidden_size = self.backbone.config.hidden_size
        self.dropout = nn.Dropout(0.3)
        self.bio_head = nn.Linear(hidden_size, N_BIO)
        self.crf = CRF(N_BIO, batch_first=True)
        self.fc_pool = nn.Linear(hidden_size, 1)
        self.aspect_embed = nn.Embedding(len(ASPECTS) + 1, hidden_size, padding_idx=len(ASPECTS))
        self.aspect_scale = nn.Parameter(torch.tensor(0.5))
        self.sent_head = nn.Sequential(nn.Dropout(0.2), nn.Linear(hidden_size, N_SENT))
        self.global_head = nn.Linear(hidden_size, N_SENT)

    def forward(self, ids, mask, span_mask=None, bio=None, cached_seq=None, span_aspect=None):
        sequence = self.dropout(self.backbone(ids, attention_mask=mask).last_hidden_state) if cached_seq is None else cached_seq
        emissions = self.bio_head(sequence)
        crf_loss = -self.crf(emissions.float(), bio, mask=mask.bool(), reduction="mean") if bio is not None else None

        sentiment_logits = None
        if span_mask is not None:
            batch_size, seq_len, hidden_size = sequence.shape
            expanded_sequence = sequence.unsqueeze(1).expand(batch_size, self.max_ops, seq_len, hidden_size)
            pool_scores = self.fc_pool(expanded_sequence).squeeze(-1).masked_fill(span_mask == 0, -1e4)
            attn = torch.softmax(pool_scores, dim=-1).unsqueeze(-1)
            pooled = (expanded_sequence * attn).sum(dim=2)
            if span_aspect is not None:
                pooled = pooled + self.aspect_scale * self.aspect_embed(span_aspect)
            sentiment_logits = self.sent_head(pooled)

        global_logits = self.global_head(sequence[:, 0])
        return crf_loss, emissions, sentiment_logits, global_logits, sequence


def focal_sentiment_loss(logits_2d, targets_1d, gamma, weight, device):
    valid = targets_1d != -100
    if not valid.any():
        return torch.tensor(0.0, device=device)
    v_logits = logits_2d[valid].float()
    v_targets = targets_1d[valid]
    ce_per = F.cross_entropy(v_logits, v_targets, weight=weight, reduction="none")
    pt = torch.exp(-ce_per.detach())
    focal_w = (1.0 - pt) ** gamma
    return (focal_w * ce_per).mean()


def contrast_loss_fn(sentiment_logits, span_sent, global_sentiment, contrast_margin, device):
    loss = torch.tensor(0.0, device=device)
    sample_count = 0
    for b_idx in range(sentiment_logits.shape[0]):
        if not is_gold_contrast(span_sent[b_idx]):
            continue
        valid_idx = (span_sent[b_idx] != -100).nonzero().flatten()
        if valid_idx.numel() < 2:
            continue
        logits = F.normalize(sentiment_logits[b_idx][valid_idx], dim=-1)
        labels = span_sent[b_idx][valid_idx]
        pair_loss = torch.tensor(0.0, device=device)
        pair_count = 0
        for i in range(valid_idx.numel()):
            for j in range(i + 1, valid_idx.numel()):
                if labels[i] != labels[j]:
                    sim = F.cosine_similarity(logits[i].unsqueeze(0), logits[j].unsqueeze(0)).squeeze()
                    pair_loss += F.relu(sim - contrast_margin)
                    pair_count += 1
        if pair_count > 0:
            w = 2.0 if global_sentiment[b_idx].item() == 2 else 1.0
            loss += w * (pair_loss / pair_count)
            sample_count += 1
    return loss / max(sample_count, 1)


def evaluate(model, dataloader, device, max_ops, max_context_window, span_match_iou):
    model.eval()
    pred_spans_all, gold_spans_all = [], []
    sent_pred, sent_gold = [], []
    glob_pred, glob_gold = [], []
    bio_pred_all, bio_gold_all = [], []

    with torch.inference_mode():
        for batch in dataloader:
            ids = batch["ids"].to(device)
            mask = batch["mask"].to(device)
            spec_mask = batch["spec_mask"].to(device)
            bio = batch["bio"].to(device)
            span_sent = batch["span_sent"].to(device)
            span_aspect = batch["span_aspect"].to(device)
            global_sent = batch["global"].to(device)

            with autocast_context(device):
                _, emissions, _, global_logits, cached_seq = model(ids, mask)

            bio_pred = model.crf.decode(emissions, mask=mask.bool())
            pred_span_mask = torch.zeros(ids.shape[0], max_ops, ids.shape[1], device=device)
            pred_span_aspect = torch.full((ids.shape[0], max_ops), len(ASPECTS), dtype=torch.long, device=device)

            for row_idx, seq in enumerate(bio_pred):
                p_spans = sorted(extract_spans(seq))
                span_token_lists = [list(range(s, e + 1)) for s, e, _a in p_spans[:max_ops]]
                for span_idx, (s, e, asp) in enumerate(p_spans[:max_ops]):
                    if asp in ASPECTS:
                        pred_span_aspect[row_idx, span_idx] = ASPECTS.index(asp)
                    low, high = compute_window(s, e, span_idx, span_token_lists, ids.shape[1], max_context_window)
                    for tok in range(low, high + 1):
                        if not spec_mask[row_idx, tok]:
                            pred_span_mask[row_idx, span_idx, tok] = 1.0

            with autocast_context(device):
                _, _, sentiment_logits, _, _ = model(
                    ids,
                    mask,
                    span_mask=pred_span_mask,
                    cached_seq=cached_seq,
                    span_aspect=pred_span_aspect,
                )

            for row_idx in range(ids.shape[0]):
                valid_len = int(mask[row_idx].sum())
                p_set = extract_spans(bio_pred[row_idx][:valid_len])
                g_set = extract_spans(bio[row_idx].tolist()[:valid_len])
                pred_spans_all.append(p_set)
                gold_spans_all.append(g_set)

                valid_token_mask = (~spec_mask[row_idx][:valid_len]).cpu().tolist()
                gold_bio_seq = bio[row_idx][:valid_len].cpu().tolist()
                pred_bio_seq = bio_pred[row_idx][:valid_len]
                for keep_tok, g_l, p_l in zip(valid_token_mask, gold_bio_seq, pred_bio_seq):
                    if keep_tok:
                        bio_gold_all.append(g_l)
                        bio_pred_all.append(p_l)

                gold_sent_list = [span_sent[row_idx, slot].item() for slot in range(max_ops) if span_sent[row_idx, slot] != -100]
                sorted_g = sorted(g_set)
                g_with_sent = [(gs, ge, ga, gold_sent_list[k]) for k, (gs, ge, ga) in enumerate(sorted_g[: len(gold_sent_list)])]

                p_sorted = sorted([(ps, pe, pa) for ps, pe, pa in p_set])[:max_ops]
                for span_idx, (ps, pe, pa) in enumerate(p_sorted):
                    best_iou = 0.0
                    best_sent = None
                    for gs, ge, ga, gsent in g_with_sent:
                        if ga != pa:
                            continue
                        inter = max(0, min(pe, ge) - max(ps, gs) + 1)
                        union = (pe - ps + 1) + (ge - gs + 1) - inter
                        iou = inter / union if union > 0 else 0.0
                        if iou > best_iou:
                            best_iou = iou
                            best_sent = gsent
                    if best_iou >= span_match_iou and sentiment_logits is not None:
                        sent_pred.append(sentiment_logits[row_idx, span_idx].argmax().item())
                        sent_gold.append(best_sent)

            if (global_sent != -1).any():
                glob_pred.extend(global_logits.argmax(-1)[global_sent != -1].cpu().tolist())
                glob_gold.extend(global_sent[global_sent != -1].cpu().tolist())

    tp = sum(len(p & g) for p, g in zip(pred_spans_all, gold_spans_all))
    fp = sum(len(p - g) for p, g in zip(pred_spans_all, gold_spans_all))
    fn = sum(len(g - p) for p, g in zip(pred_spans_all, gold_spans_all))

    span_f1 = 2 * tp / (2 * tp + fp + fn + 1e-9)
    sent_f1 = f1_score(sent_gold, sent_pred, average="macro", zero_division=0) if sent_gold else 0.0

    has_global = len(glob_gold) > 0
    if has_global:
        global_f1 = f1_score(glob_gold, glob_pred, average="macro", zero_division=0)
        composite = 0.5 * span_f1 + 0.3 * sent_f1 + 0.2 * global_f1
    else:
        global_f1 = None
        composite = 0.6 * span_f1 + 0.4 * sent_f1

    confusion_matrices = {
        "bio": confusion_payload(bio_gold_all, bio_pred_all, list(range(N_BIO)), BIO_LABELS),
        "sentiment": confusion_payload(sent_gold, sent_pred, [0, 1, 2], ["NEG", "POS", "NEU"]),
        "global": confusion_payload(glob_gold, glob_pred, [0, 1, 2], ["NEG", "POS", "NEU"]),
    }

    return {
        "composite": composite,
        "span_f1": span_f1,
        "sent_f1": sent_f1,
        "global_f1": global_f1,
        "has_global": has_global,
        "confusion_matrices": confusion_matrices,
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Train ABSA on triplets schema (Kaggle-ready)")
    parser.add_argument("--train-file", type=Path, default=Path("/kaggle/input/absa-data/triplet_data_balanced_neu.jsonl"))
    parser.add_argument("--val-file", type=Path, default=Path("/kaggle/input/absa-data/val_data.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("/kaggle/working/v10_triplet_run"))
    parser.add_argument("--model-name", default="Fsoft-AIC/videberta-base")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-len", type=int, default=224)
    parser.add_argument("--epochs", type=int, default=36)
    parser.add_argument("--patience", type=int, default=8)
    parser.add_argument("--phase1-epochs", type=int, default=4)
    parser.add_argument("--max-ops", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--eval-batch-size", type=int, default=32)
    parser.add_argument("--grad-accum-steps", type=int, default=2)
    parser.add_argument("--num-workers", type=int, default=2)
    parser.add_argument("--lr-backbone", type=float, default=8e-6)
    parser.add_argument("--lr-heads", type=float, default=3e-5)
    parser.add_argument("--max-context-window", type=int, default=20)
    parser.add_argument("--span-match-iou", type=float, default=0.5)
    parser.add_argument("--contrast-margin", type=float, default=0.15)
    parser.add_argument("--lambda-bio", type=float, default=1.5)
    parser.add_argument("--lambda-sent", type=float, default=1.0)
    parser.add_argument("--lambda-global", type=float, default=0.3)
    parser.add_argument("--lambda-cons", type=float, default=0.05)
    parser.add_argument("--lambda-contrast", type=float, default=0.3)
    parser.add_argument("--contrast-sampler-weight", type=float, default=1.5)
    args, unknown = parser.parse_known_args()
    if unknown:
        print(f"Ignoring unknown args: {unknown}")
    return args


def main():
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    args.train_file = resolve_kaggle_path(args.train_file, args.train_file.name)
    args.val_file = resolve_kaggle_path(args.val_file, args.val_file.name)

    if not args.train_file.exists():
        raise FileNotFoundError(f"Missing train file: {args.train_file}")
    if not args.val_file.exists():
        raise FileNotFoundError(f"Missing val file: {args.val_file}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    best_model_path = args.output_dir / "best_model.pt"
    checkpoint_path = args.output_dir / "checkpoint.pt"
    metrics_csv_path = args.output_dir / "train_log.csv"
    confusion_jsonl_path = args.output_dir / "confusion_matrices.jsonl"
    config_path = args.output_dir / "run_config.json"

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump({k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()}, f, ensure_ascii=False, indent=2)

    print(f"Device: {device}")
    print(f"Train: {args.train_file}")
    print(f"Val:   {args.val_file}")
    print(f"Out:   {args.output_dir}")

    set_seed(args.seed)
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    train_ds = ABSADataset(args.train_file, tokenizer, args.max_len, args.max_ops, args.max_context_window)
    val_ds = ABSADataset(args.val_file, tokenizer, args.max_len, args.max_ops, args.max_context_window)

    sent_counts = [0] * N_SENT
    for item in train_ds.items:
        for s in item["span_sent"].tolist():
            if s != -100:
                sent_counts[s] += 1
    total_sent = sum(sent_counts)
    sent_class_weights = torch.clamp(
        torch.tensor([total_sent / (N_SENT * max(c, 1)) for c in sent_counts], dtype=torch.float32, device=device),
        max=3.0,
    )
    print(f"Sent class weights [NEG/POS/NEU]: {[round(x, 3) for x in sent_class_weights.tolist()]}")

    sample_weights = [args.contrast_sampler_weight if is_gold_contrast(item["span_sent"]) else 1.0 for item in train_ds.items]
    sampler = WeightedRandomSampler(sample_weights, num_samples=len(train_ds), replacement=True)

    train_dl = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        sampler=sampler,
        num_workers=args.num_workers,
        pin_memory=device.type == "cuda",
    )
    val_dl = DataLoader(
        val_ds,
        batch_size=args.eval_batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=device.type == "cuda",
    )

    model = ABSAModel(args.model_name, args.max_ops).to(device).float()
    optimizer = AdamW(
        [
            {"params": model.backbone.parameters(), "lr": args.lr_backbone, "weight_decay": 0.01},
            {"params": [p for n, p in model.named_parameters() if "backbone" not in n], "lr": args.lr_heads},
        ]
    )

    steps_per_epoch = max(1, (len(train_dl) + args.grad_accum_steps - 1) // args.grad_accum_steps)
    total_steps = steps_per_epoch * args.epochs
    scheduler = OneCycleLR(
        optimizer,
        max_lr=[args.lr_backbone, args.lr_heads],
        total_steps=total_steps,
        pct_start=args.phase1_epochs / max(args.epochs, 1),
        anneal_strategy="cos",
        div_factor=25.0,
        final_div_factor=1e4,
    )

    scaler = torch.amp.GradScaler(enabled=device.type == "cuda")

    best_score = -1.0
    patience_counter = 0

    for epoch in range(1, args.epochs + 1):
        model.train()
        in_phase1 = epoch <= args.phase1_epochs
        contrast_scale = min(1.0, (epoch - args.phase1_epochs) / 2.0) if not in_phase1 else 0.0
        running = {
            "loss": 0.0,
            "bio_loss": 0.0,
            "sent_loss": 0.0,
            "global_loss": 0.0,
            "consistency_loss": 0.0,
            "contrast_loss": 0.0,
        }
        step_count = 0

        optimizer.zero_grad(set_to_none=True)
        progress = tqdm(train_dl, desc=f"Epoch {epoch:02d}")

        for step, batch in enumerate(progress, start=1):
            ids = batch["ids"].to(device)
            mask = batch["mask"].to(device)
            bio = batch["bio"].to(device)
            span_mask = batch["span_mask"].to(device)
            span_sent = batch["span_sent"].to(device)
            span_aspect = batch["span_aspect"].to(device)
            global_sent = batch["global"].to(device)

            with autocast_context(device):
                crf_loss, _, sentiment_logits, global_logits, _ = model(
                    ids,
                    mask,
                    span_mask=None if in_phase1 else span_mask,
                    bio=bio,
                    span_aspect=None if in_phase1 else span_aspect,
                )

                sent_loss = (
                    focal_sentiment_loss(
                        sentiment_logits.view(-1, N_SENT),
                        span_sent.view(-1),
                        gamma=2.0,
                        weight=sent_class_weights,
                        device=device,
                    )
                    if not in_phase1
                    else torch.tensor(0.0, device=device)
                )

                global_loss = (
                    F.cross_entropy(global_logits[global_sent != -1], global_sent[global_sent != -1], label_smoothing=0.1)
                    if (global_sent != -1).any()
                    else torch.tensor(0.0, device=device)
                )

                contrast_loss = (
                    contrast_loss_fn(sentiment_logits, span_sent, global_sent, args.contrast_margin, device)
                    if not in_phase1
                    else torch.tensor(0.0, device=device)
                )

                if not in_phase1:
                    valid_span_mask = (span_sent != -100).float()
                    valid_global_mask = global_sent != -1
                    if valid_span_mask.sum() > 0 and valid_global_mask.any():
                        span_avg = (sentiment_logits * valid_span_mask.unsqueeze(-1)).sum(1) / valid_span_mask.sum(1, keepdim=True).clamp(min=1)
                        gold_dist = torch.full((global_sent.shape[0], N_SENT), 0.1, device=device)
                        for row_idx in range(global_sent.shape[0]):
                            if global_sent[row_idx] != -1:
                                gold_dist[row_idx, global_sent[row_idx]] = 0.8
                        consistency_loss = F.kl_div(
                            F.log_softmax(span_avg[valid_global_mask], dim=-1),
                            gold_dist[valid_global_mask],
                            reduction="batchmean",
                        )
                    else:
                        consistency_loss = torch.tensor(0.0, device=device)
                else:
                    consistency_loss = torch.tensor(0.0, device=device)

                total_loss = (
                    args.lambda_bio * crf_loss
                    + args.lambda_global * global_loss
                    + args.lambda_sent * sent_loss
                    + args.lambda_cons * consistency_loss
                    + args.lambda_contrast * contrast_scale * contrast_loss
                ).float() / args.grad_accum_steps

            raw_loss = total_loss.item() * args.grad_accum_steps
            running["loss"] += raw_loss
            running["bio_loss"] += float(crf_loss.detach().item())
            running["sent_loss"] += float(sent_loss.detach().item())
            running["global_loss"] += float(global_loss.detach().item())
            running["consistency_loss"] += float(consistency_loss.detach().item())
            running["contrast_loss"] += float(contrast_loss.detach().item())
            step_count += 1

            scaler.scale(total_loss).backward()

            if step % args.grad_accum_steps == 0 or step == len(train_dl):
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optimizer)
                scaler.update()
                scheduler.step()
                optimizer.zero_grad(set_to_none=True)

            progress.set_postfix({"loss": f"{raw_loss:.3f}"})

        train_metrics = {k: v / max(step_count, 1) for k, v in running.items()}
        eval_metrics = evaluate(model, val_dl, device, args.max_ops, args.max_context_window, args.span_match_iou)

        global_f1_str = "N/A" if eval_metrics["global_f1"] is None else f"{eval_metrics['global_f1']:.4f}"
        print(
            f"Epoch {epoch} | TrainLoss: {train_metrics['loss']:.4f} | Comp: {eval_metrics['composite']:.4f} | "
            f"Span: {eval_metrics['span_f1']:.4f} | Sent: {eval_metrics['sent_f1']:.4f} | Glob: {global_f1_str}"
        )

        is_best = eval_metrics["composite"] > best_score
        if is_best:
            best_score = eval_metrics["composite"]
            patience_counter = 0
            torch.save(model.state_dict(), best_model_path)
            print(f"Saved new best model -> {best_model_path} | composite={best_score:.4f}")
        else:
            patience_counter += 1

        if in_phase1 and epoch == args.phase1_epochs:
            best_score = 0.0
            patience_counter = 0
            print("Phase 2 start: reset early-stop state.")

        torch.save(
            {
                "epoch": epoch,
                "model": model.state_dict(),
                "optimizer": optimizer.state_dict(),
                "scheduler": scheduler.state_dict(),
                "best_score": best_score,
                "patience": patience_counter,
                "args": {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()},
            },
            checkpoint_path,
        )

        csv_exists = metrics_csv_path.exists()
        with open(metrics_csv_path, "a" if csv_exists else "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not csv_exists:
                writer.writerow(
                    [
                        "epoch",
                        "phase",
                        "train_loss",
                        "train_bio_loss",
                        "train_sent_loss",
                        "train_global_loss",
                        "train_consistency_loss",
                        "train_contrast_loss",
                        "span_f1",
                        "sent_f1",
                        "glob_f1",
                        "composite",
                        "is_best",
                    ]
                )
            writer.writerow(
                [
                    epoch,
                    "phase1" if in_phase1 else "phase2",
                    f"{train_metrics['loss']:.4f}",
                    f"{train_metrics['bio_loss']:.4f}",
                    f"{train_metrics['sent_loss']:.4f}",
                    f"{train_metrics['global_loss']:.4f}",
                    f"{train_metrics['consistency_loss']:.4f}",
                    f"{train_metrics['contrast_loss']:.4f}",
                    f"{eval_metrics['span_f1']:.4f}",
                    f"{eval_metrics['sent_f1']:.4f}",
                    "N/A" if eval_metrics["global_f1"] is None else f"{eval_metrics['global_f1']:.4f}",
                    f"{eval_metrics['composite']:.4f}",
                    "best" if is_best else "",
                ]
            )

        with open(confusion_jsonl_path, "a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "epoch": epoch,
                        "phase": "phase1" if in_phase1 else "phase2",
                        "is_best": is_best,
                        "matrices": eval_metrics["confusion_matrices"],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

        if not in_phase1 and patience_counter >= args.patience:
            print("Early stopping.")
            break


if __name__ == "__main__":
    main()
