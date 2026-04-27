import argparse
import csv
import json
import os
import random
import subprocess
import sys
import unicodedata
import warnings
from contextlib import nullcontext
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.metrics import confusion_matrix, f1_score
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from tqdm.auto import tqdm
from torch.optim.lr_scheduler import OneCycleLR
from transformers import AutoModel, AutoTokenizer

warnings.filterwarnings("ignore", message=".*lr_scheduler.step.*before.*optimizer.step.*")

os.environ.setdefault("TRITON_INTERPRET", "1")
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")


def install_deps():
    try:
        from peft import LoraConfig as _LoraConfig  # noqa: F401
        from torchcrf import CRF as _CRF  # noqa: F401
    except ImportError:
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "pyvi",
                "pytorch-crf",
                "transformers",
                "scikit-learn",
                "peft",
                "accelerate",
                "-q",
            ]
        )


install_deps()

from peft import LoraConfig, TaskType, get_peft_model
from torchcrf import CRF


if "__file__" in globals():
    REPO_ROOT = Path(__file__).resolve().parents[1]
else:
    REPO_ROOT = Path.cwd()

DEFAULT_TRAIN_FILE = Path("/kaggle/input/datasets/minhhuy304/data-absav2/data_train_v6_final.jsonl")
DEFAULT_VAL_FILE = Path("/kaggle/input/datasets/minhhuy304/data-absav2/val_data.jsonl")
DEFAULT_OUTPUT_DIR = Path("/kaggle/working/v7_lora_run")

ASPECTS = ["Fashion", "Electronics", "General", "Service", "Ship", "Price", "App"]
N_SENT = 3


def build_bio_labels():
    labels = ["O"]
    for aspect in ASPECTS:
        labels.extend([f"B-{aspect}", f"I-{aspect}"])
    return labels, {label: idx for idx, label in enumerate(labels)}, {idx: label for idx, label in enumerate(labels)}


BIO_LABELS, BIO_L2I, BIO_I2L = build_bio_labels()
N_BIO = len(BIO_LABELS)


def nfc(text):
    return unicodedata.normalize("NFC", text)


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


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


def compute_clause_aware_window(tmin, tmax, op_idx, span_token_lists, offsets, text, seq_len, max_context_window):
    low = max(tmin - max_context_window, 1)
    high = min(tmax + max_context_window, seq_len - 1)
    stop_tokens = {",", ".", "!", "?", ";", ":"}
    boundary_tokens = {"nhưng", "tuy", "dù", "mà", "song", "còn", "tuy_nhiên", "thế_mà", "thế_nhưng"}

    if op_idx > 0:
        low = max(low, max(span_token_lists[op_idx - 1]) + 1)
    if op_idx < len(span_token_lists) - 1:
        high = min(high, min(span_token_lists[op_idx + 1]) - 1)

    for cursor in range(tmin - 1, low - 1, -1):
        if 0 < cursor < seq_len:
            char_start, char_end = int(offsets[cursor][0]), int(offsets[cursor][1])
            token_text = text[char_start:char_end].lower().strip()
            if token_text in stop_tokens:
                low = cursor + 1
                break

    for cursor in range(tmax + 1, high + 1):
        if 0 < cursor < seq_len:
            char_start, char_end = int(offsets[cursor][0]), int(offsets[cursor][1])
            token_text = text[char_start:char_end].lower().strip()
            if token_text in stop_tokens or token_text in boundary_tokens:
                high = cursor - 1
                break

    return low, high


def autocast_context(device):
    if device.type == "cuda":
        return torch.autocast(device_type="cuda", dtype=torch.float16)
    return nullcontext()


def label_names_for_sentiment():
    return ["NEG", "POS", "NEU"]


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


def save_confusion_matrices(path, epoch, phase_name, matrices, is_best):
    payload = {
        "epoch": epoch,
        "phase": phase_name,
        "is_best": is_best,
        "matrices": matrices,
    }
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def detect_lora_target_modules(base_model):
    # Priority-ordered groups: prefer _proj variants over bare names to avoid
    # double-application when both "value_proj" and "value" match the same layer.
    # DeBERTa uses disentangled attention (Q, K, V all contribute to position+content
    # interaction), so we target all three projection families.
    candidate_groups = [
        ["query_proj", "query"],
        ["key_proj", "key"],
        ["value_proj", "value"],
    ]
    hits = []
    for candidates in candidate_groups:
        for candidate in candidates:
            for module_name, _module in base_model.named_modules():
                if module_name.endswith(candidate):
                    hits.append(candidate)
                    break  # take first matching candidate in this group only
            else:
                continue
            break  # stop trying other names in this group once one matched
    if not hits:
        raise ValueError("Could not detect suitable LoRA target modules in the ViDeBERTa backbone.")
    return hits


class ABSADataset(Dataset):
    def __init__(self, file_path, tokenizer, max_len, max_ops, max_context_window):
        self.items = []
        with open(file_path, encoding="utf-8") as handle:
            lines = handle.readlines()

        print(f"Pre-tokenizing {len(lines)} records from {file_path}...")

        for line in lines:
            record = json.loads(line)
            text = nfc(record["text"])
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
            valid_ops = []

            for opinion in record.get("opinions", []):
                start = opinion.get("start", -1)
                end = opinion.get("end", -1)
                aspect = opinion.get("aspect", "")
                sentiment = opinion.get("sentiment", -1)
                if not aspect or sentiment == -1:
                    continue

                tokens = [
                    idx
                    for idx, (char_start, char_end) in enumerate(offsets)
                    if not special_mask[idx] and max(char_start, start) < min(char_end, end)
                ]
                if tokens:
                    valid_ops.append((tokens, aspect, sentiment))

            valid_ops.sort(key=lambda item: item[0][0])
            sliced_ops = valid_ops[:max_ops]
            span_token_lists = [item[0] for item in sliced_ops]

            for opinion_idx, (tokens, aspect, sentiment) in enumerate(sliced_ops):
                for token_offset, token_idx in enumerate(tokens):
                    bio[token_idx] = BIO_L2I[f"B-{aspect}" if token_offset == 0 else f"I-{aspect}"]

                low, high = compute_clause_aware_window(
                    min(tokens),
                    max(tokens),
                    opinion_idx,
                    span_token_lists,
                    offsets,
                    text,
                    seq_len,
                    max_context_window,
                )
                for token_idx in range(low, high + 1):
                    if not special_mask[token_idx]:
                        span_mask[opinion_idx, token_idx] = 1.0
                span_sent[opinion_idx] = sentiment

            self.items.append(
                {
                    "ids": torch.tensor(encoding["input_ids"]),
                    "mask": torch.tensor(encoding["attention_mask"]),
                    "offsets": torch.tensor(offsets),
                    "spec_mask": torch.tensor(special_mask, dtype=torch.bool),
                    "bio": torch.tensor(bio),
                    "span_mask": span_mask,
                    "span_sent": span_sent,
                    "text": text,
                    "global": torch.tensor(record.get("global_sentiment", -1)),
                }
            )

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        return self.items[index]


class ABSAModel(nn.Module):
    def __init__(self, model_name, max_ops, lora_r, lora_alpha, lora_dropout, lora_target_modules=None):
        super().__init__()
        self.max_ops = max_ops
        base_backbone = AutoModel.from_pretrained(model_name)
        if lora_target_modules is None:
            lora_target_modules = detect_lora_target_modules(base_backbone)
        self.lora_target_modules = lora_target_modules
        lora_config = LoraConfig(
            task_type=TaskType.FEATURE_EXTRACTION,
            r=lora_r,
            lora_alpha=lora_alpha,
            lora_dropout=lora_dropout,
            bias="none",
            target_modules=lora_target_modules,
        )
        self.backbone = get_peft_model(base_backbone, lora_config)
        hidden_size = self.backbone.config.hidden_size
        self.dropout = nn.Dropout(0.3)
        self.bio_head = nn.Linear(hidden_size, N_BIO)
        self.crf = CRF(N_BIO, batch_first=True)
        self.fc_pool = nn.Linear(hidden_size, 1)
        self.sent_head = nn.Sequential(nn.Dropout(0.2), nn.Linear(hidden_size, N_SENT))
        self.global_head = nn.Linear(hidden_size, N_SENT)

    def forward(self, ids, mask, span_mask=None, bio=None, cached_seq=None):
        sequence = self.dropout(self.backbone(ids, attention_mask=mask).last_hidden_state) if cached_seq is None else cached_seq
        emissions = self.bio_head(sequence)
        crf_loss = -self.crf(emissions, bio, mask=mask.bool(), reduction="mean") if bio is not None else None

        sentiment_logits = None
        if span_mask is not None:
            batch_size, seq_len, hidden_size = sequence.shape
            expanded_sequence = sequence.unsqueeze(1).expand(batch_size, self.max_ops, seq_len, hidden_size)
            pool_scores = self.fc_pool(expanded_sequence).squeeze(-1).masked_fill(span_mask == 0, -1e4)
            attn = torch.softmax(pool_scores, dim=-1).unsqueeze(-1)
            pooled = (expanded_sequence * attn).sum(dim=2)
            sentiment_logits = self.sent_head(pooled)

        global_logits = self.global_head(sequence[:, 0])
        return crf_loss, emissions, sentiment_logits, global_logits, sequence

    def task_head_state_dict(self):
        return {
            "bio_head": self.bio_head.state_dict(),
            "crf": self.crf.state_dict(),
            "fc_pool": self.fc_pool.state_dict(),
            "sent_head": self.sent_head.state_dict(),
            "global_head": self.global_head.state_dict(),
            "lora_target_modules": self.lora_target_modules,
        }

    def save_trainable(self, save_dir, tokenizer=None, metadata=None):
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        adapter_dir = save_dir / "adapter"
        self.backbone.save_pretrained(adapter_dir)
        if tokenizer is not None:
            tokenizer.save_pretrained(adapter_dir)
        torch.save(self.task_head_state_dict(), save_dir / "task_heads.pt")
        if metadata is not None:
            with open(save_dir / "metadata.json", "w", encoding="utf-8") as handle:
                json.dump(metadata, handle, ensure_ascii=False, indent=2)


def contrast_loss_fn(sentiment_logits, span_sent, global_sentiment, contrast_margin, device):
    loss = torch.tensor(0.0, device=device)
    sample_count = 0
    for batch_idx in range(sentiment_logits.shape[0]):
        if not is_gold_contrast(span_sent[batch_idx]):
            continue
        valid_idx = (span_sent[batch_idx] != -100).nonzero().flatten()
        if valid_idx.numel() < 2:
            continue

        logits = sentiment_logits[batch_idx][valid_idx]
        labels = span_sent[batch_idx][valid_idx]
        pair_loss = torch.tensor(0.0, device=device)
        pair_count = 0
        for left in range(valid_idx.numel()):
            for right in range(left + 1, valid_idx.numel()):
                if labels[left] != labels[right]:
                    similarity = F.cosine_similarity(logits[left].unsqueeze(0), logits[right].unsqueeze(0)).squeeze()
                    pair_loss += F.relu(similarity - contrast_margin)
                    pair_count += 1

        if pair_count > 0:
            weight = 2.0 if global_sentiment[batch_idx].item() == 2 else 1.0
            loss += weight * (pair_loss / pair_count)
            sample_count += 1

    return loss / max(sample_count, 1)


def evaluate(model, dataloader, device, max_ops, max_context_window, span_match_iou):
    model.eval()
    predicted_spans_all = []
    gold_spans_all = []
    sentiment_pred = []
    sentiment_gold = []
    global_pred = []
    global_gold = []
    bio_pred_all = []
    bio_gold_all = []

    with torch.inference_mode():
        for batch in dataloader:
            ids = batch["ids"].to(device)
            mask = batch["mask"].to(device)
            spec_mask = batch["spec_mask"].to(device)
            bio = batch["bio"].to(device)
            span_sent = batch["span_sent"].to(device)
            global_sent = batch["global"].to(device)

            with autocast_context(device):
                _, emissions, _, global_logits, cached_seq = model(ids, mask)

            bio_pred = model.crf.decode(emissions, mask=mask.bool())
            pred_span_mask = torch.zeros(ids.shape[0], max_ops, ids.shape[1], device=device)

            for row_idx, seq in enumerate(bio_pred):
                predicted_spans = sorted(extract_spans(seq))
                span_token_lists = [list(range(start, end + 1)) for start, end, _ in predicted_spans[:max_ops]]
                for span_idx, (start, end, _) in enumerate(predicted_spans[:max_ops]):
                    low, high = compute_clause_aware_window(
                        start,
                        end,
                        span_idx,
                        span_token_lists,
                        batch["offsets"][row_idx],
                        batch["text"][row_idx],
                        ids.shape[1],
                        max_context_window,
                    )
                    for token_idx in range(low, high + 1):
                        if not spec_mask[row_idx, token_idx]:
                            pred_span_mask[row_idx, span_idx, token_idx] = 1.0

            with autocast_context(device):
                _, _, sentiment_logits, _, _ = model(ids, mask, span_mask=pred_span_mask, cached_seq=cached_seq)

            for row_idx in range(ids.shape[0]):
                valid_length = int(mask[row_idx].sum())
                predicted_set = extract_spans(bio_pred[row_idx][:valid_length])
                gold_set = extract_spans(bio[row_idx].tolist()[:valid_length])
                predicted_spans_all.append(predicted_set)
                gold_spans_all.append(gold_set)

                valid_token_mask = (~spec_mask[row_idx][:valid_length]).cpu().tolist()
                gold_bio_seq = bio[row_idx][:valid_length].cpu().tolist()
                pred_bio_seq = bio_pred[row_idx][:valid_length]
                for keep_token, gold_label, pred_label in zip(valid_token_mask, gold_bio_seq, pred_bio_seq):
                    if keep_token:
                        bio_gold_all.append(gold_label)
                        bio_pred_all.append(pred_label)

                gold_span_sentiments = [
                    span_sent[row_idx, slot].item() for slot in range(max_ops) if span_sent[row_idx, slot] != -100
                ]
                sorted_gold_spans = sorted(gold_set)
                gold_with_sent = [
                    (start, end, aspect, gold_span_sentiments[idx])
                    for idx, (start, end, aspect) in enumerate(sorted_gold_spans[: len(gold_span_sentiments)])
                ]

                predicted_spans = sorted([(start, end, aspect) for start, end, aspect in predicted_set])[:max_ops]
                for span_idx, (pred_start, pred_end, pred_aspect) in enumerate(predicted_spans):
                    best_iou = 0.0
                    best_sentiment = None
                    for gold_start, gold_end, gold_aspect, gold_sentiment in gold_with_sent:
                        if gold_aspect != pred_aspect:
                            continue
                        intersection = max(0, min(pred_end, gold_end) - max(pred_start, gold_start) + 1)
                        union = (pred_end - pred_start + 1) + (gold_end - gold_start + 1) - intersection
                        iou = intersection / union if union > 0 else 0.0
                        if iou > best_iou:
                            best_iou = iou
                            best_sentiment = gold_sentiment
                    if best_iou >= span_match_iou and sentiment_logits is not None:
                        sentiment_pred.append(sentiment_logits[row_idx, span_idx].argmax().item())
                        sentiment_gold.append(best_sentiment)

            if (global_sent != -1).any():
                global_pred.extend(global_logits.argmax(-1)[global_sent != -1].cpu().tolist())
                global_gold.extend(global_sent[global_sent != -1].cpu().tolist())

    true_positive = sum(len(predicted & gold) for predicted, gold in zip(predicted_spans_all, gold_spans_all))
    false_positive = sum(len(predicted - gold) for predicted, gold in zip(predicted_spans_all, gold_spans_all))
    false_negative = sum(len(gold - predicted) for predicted, gold in zip(predicted_spans_all, gold_spans_all))

    span_f1 = 2 * true_positive / (2 * true_positive + false_positive + false_negative + 1e-9)
    sent_f1 = f1_score(sentiment_gold, sentiment_pred, average="macro", zero_division=0) if sentiment_gold else 0.0
    global_f1 = f1_score(global_gold, global_pred, average="macro", zero_division=0) if global_gold else 0.0
    composite = 0.5 * span_f1 + 0.3 * sent_f1 + 0.2 * global_f1

    confusion_matrices = {
        "bio": confusion_payload(bio_gold_all, bio_pred_all, list(range(N_BIO)), BIO_LABELS),
        "sentiment": confusion_payload(sentiment_gold, sentiment_pred, [0, 1, 2], label_names_for_sentiment()),
        "global": confusion_payload(global_gold, global_pred, [0, 1, 2], label_names_for_sentiment()),
    }

    return {
        "composite": composite,
        "span_f1": span_f1,
        "sent_f1": sent_f1,
        "global_f1": global_f1,
        "confusion_matrices": confusion_matrices,
    }


def save_metrics(csv_path, epoch, phase_name, train_metrics, eval_metrics, is_best):
    csv_exists = csv_path.exists()
    with open(csv_path, "a" if csv_exists else "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
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
                phase_name,
                f"{train_metrics['loss']:.4f}",
                f"{train_metrics['bio_loss']:.4f}",
                f"{train_metrics['sent_loss']:.4f}",
                f"{train_metrics['global_loss']:.4f}",
                f"{train_metrics['consistency_loss']:.4f}",
                f"{train_metrics['contrast_loss']:.4f}",
                f"{eval_metrics['span_f1']:.4f}",
                f"{eval_metrics['sent_f1']:.4f}",
                f"{eval_metrics['global_f1']:.4f}",
                f"{eval_metrics['composite']:.4f}",
                "best" if is_best else "",
            ]
        )


def parse_args():
    parser = argparse.ArgumentParser(description="Train ABSA model with Hybrid LoRA on data_train_v6_final.jsonl")
    parser.add_argument("--train-file", type=Path, default=DEFAULT_TRAIN_FILE)
    parser.add_argument("--val-file", type=Path, default=DEFAULT_VAL_FILE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--model-name", default="Fsoft-AIC/videberta-base")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-len", type=int, default=224)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--patience", type=int, default=7)
    parser.add_argument("--phase1-epochs", type=int, default=3)
    parser.add_argument("--max-ops", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--eval-batch-size", type=int, default=32)
    parser.add_argument("--grad-accum-steps", type=int, default=2)
    parser.add_argument("--num-workers", type=int, default=2)
    parser.add_argument("--lr-lora", type=float, default=5e-5)
    parser.add_argument("--lr-heads", type=float, default=1e-4)
    parser.add_argument("--warmup-ratio", type=float, default=0.1)
    parser.add_argument("--max-context-window", type=int, default=12)
    parser.add_argument("--span-match-iou", type=float, default=0.5)
    parser.add_argument("--contrast-margin", type=float, default=0.15)
    parser.add_argument("--lambda-bio", type=float, default=1.5)
    parser.add_argument("--lambda-sent", type=float, default=1.2)
    parser.add_argument("--lambda-global", type=float, default=0.5)
    parser.add_argument("--lambda-cons", type=float, default=0.0)
    parser.add_argument("--lambda-contrast", type=float, default=0.3)
    parser.add_argument("--contrast-sampler-weight", type=float, default=1.75)
    parser.add_argument("--lora-r", type=int, default=32)
    parser.add_argument("--lora-alpha", type=int, default=64)
    parser.add_argument("--lora-dropout", type=float, default=0.1)
    parser.add_argument("--lora-target-modules", nargs="+", default=None)
    args, unknown = parser.parse_known_args()
    if unknown:
        print(f"Ignoring unknown notebook/kernel args: {unknown}")
    return args


def build_optimizer(model, lr_lora, lr_heads):
    lora_params = []
    head_params = []
    for name, param in model.named_parameters():
        if not param.requires_grad:
            continue
        if "lora_" in name:
            lora_params.append(param)
        else:
            head_params.append(param)
    return AdamW(
        [
            {"params": lora_params, "lr": lr_lora, "weight_decay": 0.01},
            {"params": head_params, "lr": lr_heads, "weight_decay": 0.01},
        ]
    )


def count_parameters(model):
    trainable = sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)
    total = sum(parameter.numel() for parameter in model.parameters())
    return trainable, total


def main():
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    for required_path in [args.train_file, args.val_file]:
        if not required_path.exists():
            raise FileNotFoundError(f"Missing data file: {required_path}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    best_model_dir = args.output_dir / "best_model"
    checkpoint_dir = args.output_dir / "checkpoint"
    metrics_csv_path = args.output_dir / "train_log.csv"
    config_path = args.output_dir / "run_config.json"
    confusion_jsonl_path = args.output_dir / "confusion_matrices.jsonl"
    best_confusion_path = args.output_dir / "best_confusion_matrices.json"
    checkpoint_state_path = args.output_dir / "checkpoint_state.pt"

    with open(config_path, "w", encoding="utf-8") as handle:
        json.dump({key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()}, handle, ensure_ascii=False, indent=2)

    set_seed(args.seed)
    print(f"Device: {device}")
    print(f"Train file: {args.train_file}")
    print(f"Val file: {args.val_file}")
    print(f"Output dir: {args.output_dir}")

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    train_ds = ABSADataset(args.train_file, tokenizer, args.max_len, args.max_ops, args.max_context_window)
    val_ds = ABSADataset(args.val_file, tokenizer, args.max_len, args.max_ops, args.max_context_window)

    sample_weights = [args.contrast_sampler_weight if is_gold_contrast(item["span_sent"]) else 1.0 for item in train_ds.items]
    train_sampler = WeightedRandomSampler(sample_weights, num_samples=len(train_ds), replacement=True)

    train_dl = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        sampler=train_sampler,
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

    model = ABSAModel(
        args.model_name,
        args.max_ops,
        args.lora_r,
        args.lora_alpha,
        args.lora_dropout,
        args.lora_target_modules,
    ).to(device).float()
    model.backbone.print_trainable_parameters()
    print(f"LoRA target modules: {model.lora_target_modules}")
    trainable_params, total_params = count_parameters(model)
    print(f"Trainable params: {trainable_params:,} / {total_params:,}")

    optimizer = build_optimizer(model, args.lr_lora, args.lr_heads)
    optimizer_steps_per_epoch = max(1, (len(train_dl) + args.grad_accum_steps - 1) // args.grad_accum_steps)
    total_optimizer_steps = optimizer_steps_per_epoch * args.epochs
    # pct_start is set to align LR peak with the start of phase2 (epoch phase1_epochs+1).
    # This ensures that sentiment/global/contrast heads begin training at the highest LR
    # rather than on a declining schedule.
    phase2_start_pct = args.phase1_epochs / args.epochs
    scheduler = OneCycleLR(
        optimizer,
        max_lr=[args.lr_lora, args.lr_heads],
        total_steps=total_optimizer_steps,
        pct_start=phase2_start_pct,
        anneal_strategy="cos",
        div_factor=25.0,
        final_div_factor=1e4,
    )
    scaler = torch.amp.GradScaler(enabled=device.type == "cuda")

    best_score = 0.0
    patience = 0

    for epoch in range(1, args.epochs + 1):
        # Phase1: freeze LoRA adapters so only bio_head + CRF are updated.
        # Backbone forward pass still runs (features needed), but no backbone gradient
        # → ~3x faster per phase1 epoch.  Unfreeze at phase2 start.
        if epoch == 1:
            for name, param in model.named_parameters():
                if "lora_" in name:
                    param.requires_grad_(False)
            print("Phase 1: LoRA frozen — training bio_head + CRF only.")
        elif epoch == args.phase1_epochs + 1:
            for name, param in model.named_parameters():
                if "lora_" in name:
                    param.requires_grad_(True)
            print("Phase 2: LoRA unfrozen — training all parameters.")

        model.train()
        in_phase1 = epoch <= args.phase1_epochs
        contrast_scale = min(1.0, (epoch - args.phase1_epochs) / 2.0) if not in_phase1 else 0.0
        progress = tqdm(train_dl, desc=f"Epoch {epoch:02d}")
        optimizer.zero_grad(set_to_none=True)
        running_loss_sums = {
            "loss": 0.0,
            "bio_loss": 0.0,
            "sent_loss": 0.0,
            "global_loss": 0.0,
            "consistency_loss": 0.0,
            "contrast_loss": 0.0,
        }
        step_count = 0

        for step, batch in enumerate(progress, start=1):
            ids = batch["ids"].to(device)
            mask = batch["mask"].to(device)
            bio = batch["bio"].to(device)
            span_mask = batch["span_mask"].to(device)
            span_sent = batch["span_sent"].to(device)
            global_sent = batch["global"].to(device)

            with autocast_context(device):
                crf_loss, _, sentiment_logits, global_logits, _ = model(
                    ids,
                    mask,
                    span_mask=None if in_phase1 else span_mask,
                    bio=bio,
                )

                sent_loss = (
                    F.cross_entropy(
                        sentiment_logits.view(-1, N_SENT),
                        span_sent.view(-1),
                        ignore_index=-100,
                        label_smoothing=0.05,
                    )
                    if not in_phase1
                    else torch.tensor(0.0, device=device)
                )

                global_loss = (
                    F.cross_entropy(global_logits[global_sent != -1], global_sent[global_sent != -1], label_smoothing=0.05)
                    if (global_sent != -1).any()
                    else torch.tensor(0.0, device=device)
                )

                contrast_loss = (
                    contrast_loss_fn(sentiment_logits, span_sent, global_sent, args.contrast_margin, device)
                    if not in_phase1
                    else torch.tensor(0.0, device=device)
                )

                consistency_loss = torch.tensor(0.0, device=device)

                total_loss = (
                    args.lambda_bio * crf_loss
                    + args.lambda_global * global_loss
                    + args.lambda_sent * sent_loss
                    + args.lambda_contrast * contrast_scale * contrast_loss
                ).float() / args.grad_accum_steps

            raw_total_loss = total_loss.item() * args.grad_accum_steps
            running_loss_sums["loss"] += raw_total_loss
            running_loss_sums["bio_loss"] += float(crf_loss.detach().item())
            running_loss_sums["sent_loss"] += float(sent_loss.detach().item())
            running_loss_sums["global_loss"] += float(global_loss.detach().item())
            running_loss_sums["consistency_loss"] += 0.0
            running_loss_sums["contrast_loss"] += float(contrast_loss.detach().item())
            step_count += 1

            scaler.scale(total_loss).backward()

            if step % args.grad_accum_steps == 0 or step == len(train_dl):
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optimizer)
                scaler.update()
                scheduler.step()
                optimizer.zero_grad(set_to_none=True)

            progress.set_postfix({"loss": f"{raw_total_loss:.3f}"})

        train_metrics = {key: value / max(step_count, 1) for key, value in running_loss_sums.items()}
        eval_metrics = evaluate(model, val_dl, device, args.max_ops, args.max_context_window, args.span_match_iou)
        print(
            f"Epoch {epoch} | TrainLoss: {train_metrics['loss']:.4f} | Comp: {eval_metrics['composite']:.4f} | Span: {eval_metrics['span_f1']:.4f} | Sent: {eval_metrics['sent_f1']:.4f} | Glob: {eval_metrics['global_f1']:.4f}"
        )

        is_best = eval_metrics["composite"] > best_score
        if is_best:
            best_score = eval_metrics["composite"]
            patience = 0
            model.save_trainable(
                best_model_dir,
                tokenizer=tokenizer,
                metadata={
                    "epoch": epoch,
                    "phase": "phase1" if in_phase1 else "phase2",
                    "composite": eval_metrics["composite"],
                    "lora_target_modules": model.lora_target_modules,
                },
            )
            with open(best_confusion_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "epoch": epoch,
                        "phase": "phase1" if in_phase1 else "phase2",
                        "composite": eval_metrics["composite"],
                        "matrices": eval_metrics["confusion_matrices"],
                    },
                    handle,
                    ensure_ascii=False,
                    indent=2,
                )
        else:
            patience += 1

        if in_phase1 and epoch == args.phase1_epochs:
            best_score = 0.0
            patience = 0
            print("Phase 2 start: reset early-stop state.")

        model.save_trainable(
            checkpoint_dir,
            tokenizer=None,
            metadata={
                "epoch": epoch,
                "phase": "phase1" if in_phase1 else "phase2",
                "best_score": best_score,
                "lora_target_modules": model.lora_target_modules,
            },
        )
        torch.save(
            {
                "epoch": epoch,
                "optimizer": optimizer.state_dict(),
                "scheduler": scheduler.state_dict(),
                "best_score": best_score,
                "patience": patience,
                "args": {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()},
            },
            checkpoint_state_path,
        )

        save_metrics(metrics_csv_path, epoch, "phase1" if in_phase1 else "phase2", train_metrics, eval_metrics, is_best)
        save_confusion_matrices(
            confusion_jsonl_path,
            epoch,
            "phase1" if in_phase1 else "phase2",
            eval_metrics["confusion_matrices"],
            is_best,
        )

        if not in_phase1 and patience >= args.patience:
            print("Early stopping.")
            break


if __name__ == "__main__":
    main()