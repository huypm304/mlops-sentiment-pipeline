import argparse
import csv
import json
import math
import os
import random
import re
import subprocess
import sys
import unicodedata
import warnings
from collections import Counter
from contextlib import nullcontext
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.metrics import confusion_matrix, f1_score, precision_recall_fscore_support
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from tqdm.auto import tqdm
from torch.optim.lr_scheduler import LambdaLR
from transformers import AutoModel, AutoTokenizer

warnings.filterwarnings("ignore", message=".*lr_scheduler.step.*before.*optimizer.step.*")

os.environ.setdefault("TRITON_INTERPRET", "1")
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

if torch.cuda.is_available():
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True


def install_deps():
    need_install = False
    try:
        from torchcrf import CRF as _CRF  # noqa: F401
    except ImportError:
        need_install = True

    try:
        import sentencepiece as _spm  # noqa: F401
    except ImportError:
        need_install = True

    if need_install:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install",
             "pyvi", "pytorch-crf", "transformers", "scikit-learn", "sentencepiece", "-q"]
        )


install_deps()
from torchcrf import CRF

if "__file__" in globals():
    REPO_ROOT = Path(__file__).resolve().parents[2]
else:
    REPO_ROOT = Path.cwd()

DEFAULT_TRAIN_FILE = Path("/kaggle/input/datasets/minhhuy304/absa-datav3/train_aug500_boundary200.jsonl")
DEFAULT_VAL_FILE   = Path("/kaggle/input/datasets/minhhuy304/absa-datav3/dev_clean.jsonl")
DEFAULT_OUTPUT_DIR = Path("/kaggle/working/run1a_phobert")

ASPECTS = ["Fashion", "Electronics", "General", "Service", "Ship", "Price", "App"]
N_SENT  = 3


def build_bio_labels():
    labels = ["O"]
    for aspect in ASPECTS:
        labels.extend([f"B-{aspect}", f"I-{aspect}"])
    return labels, {l: i for i, l in enumerate(labels)}, {i: l for i, l in enumerate(labels)}


BIO_LABELS, BIO_L2I, BIO_I2L = build_bio_labels()
N_BIO = len(BIO_LABELS)
TOKENIZE_BATCH_SIZE = 512

CONTRAST_WORDS = {
    "nhưng",
    "tuy",
    "dù",
    "mà",
    "song",
    "còn",
    "tuy nhiên",
    "thế mà",
    "thế nhưng",
}


def overlaps(a_start, a_end, b_start, b_end):
    return max(a_start, b_start) < min(a_end, b_end)


def find_contrast_char_spans(text: str):
    text_l = text.lower()
    spans = []
    for phrase in CONTRAST_WORDS:
        pattern = r"\\b" + re.sub(r"\\s+", r"(?:\\s+|_)", re.escape(phrase)) + r"\\b"
        for m in re.finditer(pattern, text_l):
            spans.append((m.start(), m.end()))
    spans.sort()
    return spans


def nfc(text):
    return unicodedata.normalize("NFC", text)


def set_seed(seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def is_gold_contrast(span_sent_tensor):
    values = span_sent_tensor[span_sent_tensor != -100]
    return len(values) >= 2 and len(values.unique()) >= 2


def extract_spans(seq):
    spans, start, cur = set(), None, None
    for idx, label_id in enumerate(seq):
        tag = BIO_I2L.get(label_id, "O")
        if tag.startswith("B-"):
            if start is not None:
                spans.add((start, idx - 1, cur))
            start, cur = idx, tag[2:]
        elif not (tag.startswith("I-") and cur == tag[2:]):
            if start is not None:
                spans.add((start, idx - 1, cur))
            start, cur = None, None
    if start is not None:
        spans.add((start, len(seq) - 1, cur))
    return spans


def compute_clause_aware_window(tmin, tmax, op_idx, span_token_lists, offsets, text, seq_len, max_context_window):
    low  = max(tmin - max_context_window, 1)
    high = min(tmax + max_context_window, seq_len - 1)
    stop_tokens     = {",", ".", "!", "?", ";", ":", "-", "~", "/"}
    boundary_tokens = {"nhưng", "tuy", "dù", "mà", "song", "còn", "tuy_nhiên", "thế_mà", "thế_nhưng"}

    if op_idx > 0:
        low = max(low, max(span_token_lists[op_idx - 1]) + 1)
    if op_idx < len(span_token_lists) - 1:
        high = min(high, min(span_token_lists[op_idx + 1]) - 1)

    for cursor in range(tmin - 1, low - 1, -1):
        if 0 < cursor < seq_len:
            cs, ce = int(offsets[cursor][0]), int(offsets[cursor][1])
            if text[cs:ce].lower().strip() in stop_tokens | boundary_tokens:
                low = cursor + 1
                break

    for cursor in range(tmax + 1, high + 1):
        if 0 < cursor < seq_len:
            cs, ce = int(offsets[cursor][0]), int(offsets[cursor][1])
            if text[cs:ce].lower().strip() in stop_tokens | boundary_tokens:
                high = cursor - 1
                break

    return low, high


def compute_clause_position(span_start, span_end, offsets_row, text, seq_len):
    contrast_spans = find_contrast_char_spans(text)
    if not contrast_spans:
        return 0

    contrast_token_positions = []
    for idx in range(seq_len):
        cs = int(offsets_row[idx][0])
        ce = int(offsets_row[idx][1])
        if cs == ce:
            continue
        if any(overlaps(cs, ce, ss, se) for ss, se in contrast_spans):
            contrast_token_positions.append(idx)

    if not contrast_token_positions:
        return 0

    contrast_pos = sum(contrast_token_positions) / len(contrast_token_positions)
    center = 0.5 * (span_start + span_end)
    return 1 if center < contrast_pos else 2


def collect_valid_ops(opinions, offsets, spec_mask):
    valid_ops = []
    for opinion in opinions:
        s = opinion.get("start", -1)
        e = opinion.get("end", -1)
        aspect = opinion.get("aspect", "")
        sent = opinion.get("sentiment", -1)
        if not aspect or sent == -1 or aspect not in ASPECTS:
            continue
        tokens = [
            idx for idx, (cs, ce) in enumerate(offsets)
            if not spec_mask[idx] and max(cs, s) < min(ce, e)
        ]
        if tokens:
            valid_ops.append((tokens, aspect, sent))
    valid_ops.sort(key=lambda item: item[0][0])
    return valid_ops


def build_gold_span_targets(text, opinions, offsets, spec_mask, seq_len, max_ops, max_context_window):
    bio = [0] * seq_len
    span_mask = torch.zeros(max_ops, seq_len)
    span_sent = torch.full((max_ops,), -100, dtype=torch.long)
    span_aspect = torch.full((max_ops,), len(ASPECTS), dtype=torch.long)
    span_clause_pos = torch.zeros(max_ops, dtype=torch.long)

    sliced = collect_valid_ops(opinions, offsets, spec_mask)[:max_ops]
    span_tok_lists = [op[0] for op in sliced]

    for op_idx, (tokens, aspect, sent) in enumerate(sliced):
        span_aspect[op_idx] = ASPECTS.index(aspect)
        span_clause_pos[op_idx] = compute_clause_position(min(tokens), max(tokens), offsets, text, seq_len)
        for tok_idx, token_id in enumerate(tokens):
            bio[token_id] = BIO_L2I[f"B-{aspect}" if tok_idx == 0 else f"I-{aspect}"]
        lo, hi = compute_clause_aware_window(
            min(tokens), max(tokens), op_idx, span_tok_lists,
            offsets, text, seq_len, max_context_window,
        )
        for token_id in range(lo, hi + 1):
            if not spec_mask[token_id]:
                span_mask[op_idx, token_id] = 1.0
        span_sent[op_idx] = sent

    return bio, span_mask, span_sent, span_aspect, span_clause_pos


def build_predicted_span_inputs(decoded_seq, offsets_row, spec_mask_row, text, seq_len, max_ops, max_context_window, device):
    predicted_spans = sorted(extract_spans(decoded_seq[:seq_len]))
    total_len = int(offsets_row.shape[0])
    pred_span_mask = torch.zeros(max_ops, total_len, device=device)
    pred_span_aspect = torch.full((max_ops,), len(ASPECTS), dtype=torch.long, device=device)
    pred_clause_pos = torch.zeros(max_ops, dtype=torch.long, device=device)
    span_token_lists = [list(range(start, end + 1)) for start, end, _ in predicted_spans[:max_ops]]

    for span_idx, (start, end, aspect) in enumerate(predicted_spans[:max_ops]):
        if aspect in ASPECTS:
            pred_span_aspect[span_idx] = ASPECTS.index(aspect)
        pred_clause_pos[span_idx] = compute_clause_position(start, end, offsets_row, text, seq_len)
        lo, hi = compute_clause_aware_window(
            start, end, span_idx, span_token_lists,
            offsets_row, text, seq_len, max_context_window,
        )
        for token_id in range(lo, hi + 1):
            if not spec_mask_row[token_id]:
                pred_span_mask[span_idx, token_id] = 1.0

    return set(predicted_spans), pred_span_mask, pred_span_aspect, pred_clause_pos


def build_predicted_span_labels(pred_set, gold_set, gold_sents, max_ops, span_match_iou, device):
    pred_sent = torch.full((max_ops,), -100, dtype=torch.long, device=device)
    sorted_pred = sorted(pred_set)[:max_ops]
    sorted_gold = sorted(gold_set)

    gold_with_s = [
        (s, e, a, gold_sents[i])
        for i, (s, e, a) in enumerate(sorted_gold[:len(gold_sents)])
    ]

    for si, (ps, pe, pa) in enumerate(sorted_pred):
        best_iou, best_sent = 0.0, None
        for gs, ge, ga, gsent in gold_with_s:
            if ga != pa:
                continue
            inter = max(0, min(pe, ge) - max(ps, gs) + 1)
            union = (pe - ps + 1) + (ge - gs + 1) - inter
            iou = inter / union if union > 0 else 0.0
            if iou > best_iou:
                best_iou, best_sent = iou, gsent

        if best_iou >= span_match_iou and best_sent is not None:
            pred_sent[si] = best_sent

    return pred_sent


def autocast_context(device):
    if device.type == "cuda":
        return torch.autocast(device_type="cuda", dtype=torch.float16)
    return nullcontext()


def load_tokenizer(model_name: str):
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)

    if not getattr(tokenizer, "is_fast", False):
        # Some environments return a slow tokenizer for PhoBERT; try converting from slow.
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True, from_slow=True)
        except TypeError:
            # Older transformers may not support `from_slow` in AutoTokenizer.
            pass

    if not getattr(tokenizer, "is_fast", False):
        print(
            f"[WARN] Tokenizer of {model_name} is slow. "
            "Using manual offset mapping fallback for span alignment."
        )

    sample = ["Áo đẹp nhưng giao hàng chậm"]
    try:
        if getattr(tokenizer, "is_fast", False):
            enc = tokenizer(
                sample,
                max_length=32,
                padding="max_length",
                truncation=True,
                return_offsets_mapping=True,
                return_special_tokens_mask=True,
            )
        else:
            enc = tokenizer(
                sample,
                max_length=32,
                padding="max_length",
                truncation=True,
                return_special_tokens_mask=True,
            )
        print("Tokenizer:", tokenizer.__class__.__name__)
        print("is_fast:", tokenizer.is_fast)
        print("tokens:", tokenizer.convert_ids_to_tokens(enc["input_ids"][0])[:20])
        if "offset_mapping" in enc:
            print("offsets:", enc["offset_mapping"][0][:20])
    except Exception as e:
        raise RuntimeError(
            f"Tokenizer {model_name} cannot be initialized for this ABSA pipeline."
        ) from e

    return tokenizer


def label_names_for_sentiment():
    return ["NEG", "POS", "NEU"]


def build_offsets_from_tokens(text, tokens, special_tokens_mask):
    text_l = text.lower()
    cursor = 0
    offsets = []

    for tok, is_special in zip(tokens, special_tokens_mask):
        if is_special:
            offsets.append((0, 0))
            continue

        piece = tok or ""
        if piece.startswith("##"):
            piece = piece[2:]

        # SentencePiece/Roberta boundary markers.
        piece = piece.replace("▁", " ").replace("Ġ", " ")
        piece = piece.strip()

        if not piece:
            offsets.append((0, 0))
            continue

        piece_l = piece.lower()
        idx = text_l.find(piece_l, cursor)
        if idx == -1:
            idx = text_l.find(piece_l)

        if idx == -1:
            offsets.append((0, 0))
            continue

        start = idx
        end = idx + len(piece)
        offsets.append((start, end))
        cursor = end

    return offsets


def confusion_payload(gold, pred, labels, label_names):
    matrix = confusion_matrix(gold, pred, labels=labels).tolist() if gold and pred else []
    normalized = []
    if matrix:
        for row in matrix:
            row_sum = sum(row)
            normalized.append([round(v / row_sum, 6) if row_sum else 0.0 for v in row])
    return {"labels": label_names, "raw": matrix, "normalized": normalized, "support": len(gold)}


def save_confusion_matrices(path, epoch, phase_name, matrices, is_best):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(
            {"epoch": epoch, "phase": phase_name, "is_best": is_best, "matrices": matrices},
            ensure_ascii=False,
        ) + "\n")


def extract_contrast_feature(sequence, offsets_batch, text_batch, mask):
    """
    Tìm hidden state của contrast words dựa trên char offsets thay vì subword tokens.
    Tránh bug khi ViBERTa split "nhưng" thành nhiều piece.
    Tránh inplace ops trên tensors có grad_fn để không phá autograd graph.
    """
    B, L, H = sequence.shape
    per_batch = []

    for b in range(B):
        text    = text_batch[b]
        offsets = offsets_batch[b]
        contrast_spans = find_contrast_char_spans(text)
        found   = []
        for i in range(L):
            if mask[b, i]:
                continue
            cs  = int(offsets[i, 0])
            ce  = int(offsets[i, 1])
            if cs == ce:
                continue
            if any(overlaps(cs, ce, ss, se) for ss, se in contrast_spans):
                found.append(sequence[b, i])
        if found:
            summed = torch.stack(found, dim=0).sum(0)   # no inplace
            per_batch.append(F.normalize(summed, dim=0))
        else:
            per_batch.append(sequence.new_zeros(H))

    return torch.stack(per_batch, dim=0)  # (B, H)


# =============================================================================
# DATASET
# =============================================================================
class ABSADataset(Dataset):
    def __init__(self, file_path, tokenizer, max_len, max_ops, max_context_window):
        self.items = []
        with open(file_path, encoding="utf-8") as f:
            records = [json.loads(line) for line in f if line.strip()]
        print(f"Pre-tokenizing {len(records)} records from {file_path}...")

        for start_idx in range(0, len(records), TOKENIZE_BATCH_SIZE):
            batch_records = records[start_idx:start_idx + TOKENIZE_BATCH_SIZE]
            batch_texts = [nfc(record["text"]) for record in batch_records]
            if getattr(tokenizer, "is_fast", False):
                enc = tokenizer(
                    batch_texts,
                    max_length=max_len,
                    padding="max_length",
                    truncation=True,
                    return_offsets_mapping=True,
                    return_special_tokens_mask=True,
                )
                batch_offsets = enc["offset_mapping"]
            else:
                enc = tokenizer(
                    batch_texts,
                    max_length=max_len,
                    padding="max_length",
                    truncation=True,
                    return_special_tokens_mask=True,
                )
                batch_offsets = []
                for text, input_ids, spec_mask in zip(
                    batch_texts,
                    enc["input_ids"],
                    enc["special_tokens_mask"],
                ):
                    toks = tokenizer.convert_ids_to_tokens(input_ids)
                    batch_offsets.append(build_offsets_from_tokens(text, toks, spec_mask))

            for record, text, input_ids, attention_mask, offsets, spec_mask in zip(
                batch_records,
                batch_texts,
                enc["input_ids"],
                enc["attention_mask"],
                batch_offsets,
                enc["special_tokens_mask"],
            ):
                seq_len = len(input_ids)
                bio, span_mask, span_sent, span_aspect, span_clause_pos = build_gold_span_targets(
                    text,
                    record.get("opinions", []),
                    offsets,
                    spec_mask,
                    seq_len,
                    max_ops,
                    max_context_window,
                )

                self.items.append({
                    "ids":             torch.tensor(input_ids),
                    "mask":            torch.tensor(attention_mask),
                    "offsets":         torch.tensor(offsets),
                    "spec_mask":       torch.tensor(spec_mask, dtype=torch.bool),
                    "bio":             torch.tensor(bio),
                    "span_mask":       span_mask,
                    "span_sent":       span_sent,
                    "span_aspect":     span_aspect,
                    "span_clause_pos": span_clause_pos,
                    "text":            text,
                    "global":          torch.tensor(record.get("global_sentiment", -1)),
                })

            if (start_idx + len(batch_records)) % 1000 == 0 or (start_idx + len(batch_records)) == len(records):
                print(f"  tokenized {start_idx + len(batch_records)}/{len(records)}")

    def __len__(self):        return len(self.items)
    def __getitem__(self, i): return self.items[i]


# =============================================================================
# MODEL
# =============================================================================
class ABSAModel(nn.Module):
    def __init__(self, model_name, max_ops):
        super().__init__()
        self.max_ops  = max_ops
        self.backbone = AutoModel.from_pretrained(model_name)
        h             = self.backbone.config.hidden_size
        self.dropout      = nn.Dropout(0.3)
        self.bio_lstm     = nn.LSTM(h, h // 2, num_layers=1, batch_first=True, bidirectional=True)
        self.bio_head     = nn.Linear(h, N_BIO)
        self.crf          = CRF(N_BIO, batch_first=True)
        self.fc_pool      = nn.Linear(h, 1)
        self.span_proj    = nn.Linear(h * 4, h)
        self.cross_attn   = nn.MultiheadAttention(h, num_heads=8, dropout=0.1, batch_first=True)
        self.cross_attn_scale = nn.Parameter(torch.tensor(0.5))
        self.cross_attn_norm  = nn.LayerNorm(h)
        self.span_self_attn = nn.MultiheadAttention(h, num_heads=4, dropout=0.1, batch_first=True)
        self.aspect_embed = nn.Embedding(len(ASPECTS) + 1, h, padding_idx=len(ASPECTS))
        self.aspect_scale = nn.Parameter(torch.tensor(0.8))
        self.clause_pos_embed = nn.Embedding(3, h)
        self.clause_pos_scale = nn.Parameter(torch.tensor(0.5))
        self.sent_head    = nn.Sequential(
            nn.Linear(h, h),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(h, h // 2),
            nn.GELU(),
            nn.Dropout(0.15),
            nn.Linear(h // 2, N_SENT),
        )
        # Polarity-aware global head: [cls, neg_pool, pos_pool, contra_vec] → h → N_SENT
        self.global_polarity_fusion = nn.Linear(h * 4, h)
        self.global_head  = nn.Sequential(nn.Dropout(0.2), nn.Linear(h, N_SENT))

    def forward(self, ids, mask, span_mask=None, bio=None, cached_seq=None,
                span_aspect=None, span_clause_pos=None, offsets=None, texts=None):
        seq      = self.dropout(self.backbone(ids, attention_mask=mask).last_hidden_state) \
                   if cached_seq is None else cached_seq
        B        = seq.shape[0]
        bio_feat, _ = self.bio_lstm(seq)
        emiss    = self.bio_head(bio_feat)
        crf_loss = -self.crf(emiss.float(), bio, mask=mask.bool(), reduction="mean") \
                   if bio is not None else None

        sent_logits = None
        span_features = None
        if span_mask is not None:
            B2, L, H = seq.shape
            M        = span_mask.shape[1]
            exp_seq  = seq.unsqueeze(1).expand(B2, M, L, H)
            scores   = self.fc_pool(exp_seq).squeeze(-1).masked_fill(span_mask == 0, -1e4)
            attn     = torch.softmax(scores, dim=-1).unsqueeze(-1)
            pooled   = (exp_seq * attn).sum(dim=2)          # (B, M, H)

            # Contrast feature — Fix: dùng char offsets
            if offsets is not None and texts is not None:
                c_vec  = extract_contrast_feature(seq, offsets, texts, ~mask.bool())
                pooled = pooled + 0.3 * c_vec.unsqueeze(1)

            # CLS residual
            pooled = pooled + seq[:, 0].unsqueeze(1)

            if span_aspect is not None:
                pooled = pooled + self.aspect_scale * self.aspect_embed(span_aspect)

            if span_clause_pos is not None:
                pooled = pooled + self.clause_pos_scale * self.clause_pos_embed(span_clause_pos)
            elif offsets is not None and texts is not None:
                clause_pos_ids = torch.zeros((B2, M), dtype=torch.long, device=seq.device)
                for b_idx in range(B2):
                    for m_idx in range(M):
                        active = (span_mask[b_idx, m_idx] > 0).nonzero(as_tuple=False).flatten()
                        if active.numel() == 0:
                            continue
                        span_start = int(active.min().item())
                        span_end = int(active.max().item())
                        clause_pos_ids[b_idx, m_idx] = compute_clause_position(
                            span_start,
                            span_end,
                            offsets[b_idx],
                            texts[b_idx],
                            L,
                        )
                pooled = pooled + self.clause_pos_scale * self.clause_pos_embed(clause_pos_ids)

            span_active = span_mask > 0
            valid_span_slots = span_active.any(dim=-1, keepdim=True).float()
            span_padding_mask = ~span_active.any(dim=-1)

            pos_ids = torch.arange(L, device=seq.device).view(1, 1, L).expand(B2, M, L)
            start_pos = pos_ids.masked_fill(~span_active, L).min(dim=-1).values
            end_pos = pos_ids.masked_fill(~span_active, -1).max(dim=-1).values
            empty_spans = span_padding_mask
            start_pos = start_pos.masked_fill(empty_spans, 0).long()
            end_pos = end_pos.masked_fill(empty_spans, 0).long()

            batch_ids = torch.arange(B2, device=seq.device).view(B2, 1).expand(B2, M)
            start_repr = seq[batch_ids, start_pos] * valid_span_slots
            end_repr = seq[batch_ids, end_pos] * valid_span_slots
            boundary_feat = torch.cat([pooled, start_repr, end_repr, start_repr * end_repr], dim=-1)
            pooled = self.span_proj(boundary_feat)

            cross_out, _ = self.cross_attn(
                pooled,
                seq,
                seq,
                key_padding_mask=~mask.bool(),
                need_weights=False,
            )
            pooled = self.cross_attn_norm(pooled + self.cross_attn_scale * cross_out * valid_span_slots)

            span_interact, _ = self.span_self_attn(
                pooled,
                pooled,
                pooled,
                key_padding_mask=span_padding_mask,
                need_weights=False,
            )
            pooled = pooled + span_interact * valid_span_slots
            span_features = pooled

            sent_logits = self.sent_head(pooled)            # (B, M, N_SENT)

        # Global head — polarity-aware pooling over span_features
        # For mixed reviews: neg_pool and pos_pool carry distinct signal;
        # contra_vec = neg_pool − pos_pool is the contradiction-aware direction.
        cls_repr = seq[:, 0]
        h_dim = seq.shape[-1]
        if sent_logits is not None and span_features is not None:
            valid_spans = (span_mask.sum(dim=-1) > 0).float()      # (B, M)
            # Prevent global loss from directly pulling sentiment logits.
            span_probs  = sent_logits.detach().softmax(-1)          # (B, M, 3)
            neg_w = span_probs[:, :, 0] * valid_spans              # (B, M)
            pos_w = span_probs[:, :, 1] * valid_spans
            neg_pool = (span_features * neg_w.unsqueeze(-1)).sum(1) / neg_w.sum(1, keepdim=True).clamp(min=1e-4)
            pos_pool = (span_features * pos_w.unsqueeze(-1)).sum(1) / pos_w.sum(1, keepdim=True).clamp(min=1e-4)
            contra_vec = neg_pool - pos_pool                        # explicit contradiction signal
        else:
            neg_pool = pos_pool = contra_vec = seq.new_zeros(B, h_dim)

        fused = F.gelu(self.global_polarity_fusion(
            torch.cat([cls_repr, neg_pool, pos_pool, contra_vec], dim=-1)
        ))
        global_logits = self.global_head(fused)

        return crf_loss, emiss, sent_logits, global_logits, seq, span_features


# =============================================================================
# CONTRAST LOSS
# =============================================================================
def contrast_loss_fn(span_features, span_sent, global_sent, margin, device):
    loss, n = torch.tensor(0.0, device=device), 0
    for b in range(span_features.shape[0]):
        if not is_gold_contrast(span_sent[b]):
            continue
        v_idx = (span_sent[b] != -100).nonzero().flatten()
        if v_idx.numel() < 2:
            continue
        feats = F.normalize(span_features[b][v_idx], dim=-1)
        labels = span_sent[b][v_idx]
        neg_sims = []
        pos_sims = []
        for i in range(v_idx.numel()):
            for j in range(i + 1, v_idx.numel()):
                sim = F.cosine_similarity(feats[i].unsqueeze(0), feats[j].unsqueeze(0)).squeeze()
                if labels[i] != labels[j]:
                    neg_sims.append(sim)
                else:
                    pos_sims.append(sim)
        if neg_sims:
            hard_neg = torch.stack(neg_sims)
            top_k = min(3, hard_neg.numel())
            neg_loss = F.relu(hard_neg.topk(top_k).values - margin).mean()
        else:
            neg_loss = torch.tensor(0.0, device=device)
        if pos_sims:
            pos_loss = F.relu(0.55 - torch.stack(pos_sims)).mean()
        else:
            pos_loss = torch.tensor(0.0, device=device)
        pair_loss = neg_loss + 0.5 * pos_loss
        if pair_loss.detach().item() > 0:
            weight = 2.0 if global_sent[b].item() == 2 else 1.0
            loss  += weight * pair_loss
            n     += 1
    return loss / max(n, 1)


def smooth_values_for_targets(targets, label_smoothing, n_classes):
    if isinstance(label_smoothing, (list, tuple)):
        smooth = torch.tensor(label_smoothing, dtype=torch.float32, device=targets.device)
        if smooth.numel() != n_classes:
            raise ValueError(f"label_smoothing must have {n_classes} values, got {smooth.numel()}")
        return smooth[targets]
    return torch.full(
        (targets.shape[0],),
        float(label_smoothing),
        dtype=torch.float32,
        device=targets.device,
    )


def smoothed_ce_per_sample(logits, targets, weight=None, ignore_index=-100, label_smoothing=0.0):
    valid = (targets != ignore_index)
    if not valid.any():
        return logits.new_zeros((0,)), valid

    logits_valid = logits[valid]
    targets_valid = targets[valid]
    n_classes = logits_valid.shape[-1]
    smoothing = smooth_values_for_targets(targets_valid, label_smoothing, n_classes).to(logits_valid.dtype)
    log_probs = F.log_softmax(logits_valid, dim=-1)
    true_dist = torch.zeros_like(log_probs)
    true_dist.scatter_(1, targets_valid.unsqueeze(1), 1.0)
    if n_classes > 1:
        true_dist = true_dist * (1.0 - smoothing.unsqueeze(1)) + \
                    (1.0 - true_dist) * (smoothing.unsqueeze(1) / (n_classes - 1))
    losses = -(true_dist * log_probs).sum(dim=-1)
    if weight is not None:
        losses = losses * weight[targets_valid]
    return losses, valid


def smoothed_cross_entropy(logits, targets, weight=None, ignore_index=-100, label_smoothing=0.0):
    losses, valid = smoothed_ce_per_sample(
        logits,
        targets,
        weight=weight,
        ignore_index=ignore_index,
        label_smoothing=label_smoothing,
    )
    if valid.any():
        return losses.mean()
    return logits.sum() * 0.0


def focal_loss(logits, targets, weight=None, gamma=2.0, ignore_index=-100, label_smoothing=0.0):
    ce, valid = smoothed_ce_per_sample(
        logits,
        targets,
        weight=weight,
        ignore_index=ignore_index,
        label_smoothing=label_smoothing,
    )
    if not valid.any():
        return logits.sum() * 0.0
    logits_valid = logits[valid]
    targets_valid = targets[valid]
    pt = F.softmax(logits_valid, dim=-1).gather(1, targets_valid.unsqueeze(1)).squeeze(1).clamp_min(1e-6)
    focal = ((1.0 - pt) ** gamma) * ce
    return focal.mean()


def symmetric_kl_loss(logits_a, logits_b):
    if logits_a.numel() == 0 or logits_b.numel() == 0:
        return logits_a.sum() * 0.0
    log_pa = F.log_softmax(logits_a, dim=-1)
    log_pb = F.log_softmax(logits_b, dim=-1)
    pa = log_pa.exp()
    pb = log_pb.exp()
    return 0.5 * (
        F.kl_div(log_pa, pb, reduction="batchmean") +
        F.kl_div(log_pb, pa, reduction="batchmean")
    )


class LBTWWeighter:
    def __init__(self, base_weights, ema_decay=0.99, clamp_min=0.3, clamp_max=3.0, eps=1e-6):
        self.base_weights = {name: float(value) for name, value in base_weights.items()}
        self.ema_decay = ema_decay
        self.clamp_min = clamp_min
        self.clamp_max = clamp_max
        self.eps = eps
        self.ema = {name: None for name in self.base_weights}

    def base_snapshot(self, active_names=None):
        active_set = set(self.base_weights.keys()) if active_names is None else set(active_names)
        return {
            name: (weight if name in active_set else 0.0)
            for name, weight in self.base_weights.items()
        }

    def compute_weights(self, losses):
        ratios = {}
        active_names = []

        for name, loss in losses.items():
            value = float(loss.detach().item())
            if not math.isfinite(value):
                value = self.ema[name] if self.ema[name] is not None else 0.0
            ema_prev = self.ema.get(name)
            ema_value = value if ema_prev is None else self.ema_decay * ema_prev + (1.0 - self.ema_decay) * value
            self.ema[name] = ema_value
            ratios[name] = value / max(ema_value, self.eps)
            active_names.append(name)

        if not active_names:
            return self.base_snapshot(active_names=[])

        ratio_sum = sum(ratios.values())
        n_active = len(active_names)
        weights = self.base_snapshot(active_names=[])

        for name in active_names:
            factor = n_active * ratios[name] / max(ratio_sum, self.eps)
            factor = min(max(factor, self.clamp_min), self.clamp_max)
            weights[name] = self.base_weights[name] * factor

        return weights

    def combine(self, losses, weights):
        total = None
        for name, loss in losses.items():
            weighted = weights[name] * loss
            total = weighted if total is None else total + weighted
        if total is None:
            raise ValueError("No losses were provided to LBTWWeighter.combine")
        return total


class ModelEMA:
    def __init__(self, model, decay=0.999):
        self.decay = decay
        self.num_updates = 0
        self.shadow = {}
        self.backup = None
        for name, param in model.named_parameters():
            if param.requires_grad:
                self.shadow[name] = param.detach().clone()

    def update(self, model):
        self.num_updates += 1
        # Warmup decay to avoid EMA lagging too far behind at early epochs.
        decay = min(self.decay, (1.0 + self.num_updates) / (10.0 + self.num_updates))
        with torch.no_grad():
            for name, param in model.named_parameters():
                if not param.requires_grad:
                    continue
                self.shadow[name].mul_(decay).add_(param.detach(), alpha=1.0 - decay)

    def apply_to(self, model):
        self.backup = {}
        with torch.no_grad():
            for name, param in model.named_parameters():
                if not param.requires_grad:
                    continue
                self.backup[name] = param.detach().clone()
                param.copy_(self.shadow[name])

    def restore(self, model):
        if self.backup is None:
            return
        with torch.no_grad():
            for name, param in model.named_parameters():
                if not param.requires_grad:
                    continue
                param.copy_(self.backup[name])
        self.backup = None


def build_class_weights(train_items, device):
    sent_counts = [0] * N_SENT
    glob_counts = [0] * N_SENT

    for item in train_items:
        for sent in item["span_sent"].tolist():
            if sent != -100:
                sent_counts[sent] += 1
        global_sent = item["global"].item()
        if global_sent != -1:
            glob_counts[global_sent] += 1

    total_sent = sum(sent_counts)
    total_glob = sum(glob_counts)

    if total_sent > 0:
        sent_class_weights = torch.tensor(
            [total_sent / (N_SENT * max(count, 1)) for count in sent_counts],
            dtype=torch.float32,
            device=device,
        )
        sent_class_weights = torch.clamp(sent_class_weights, min=0.7, max=2.5)
        sent_class_weights[2] = min(float(sent_class_weights[2].item()), 2.0)
    else:
        sent_class_weights = torch.ones(N_SENT, dtype=torch.float32, device=device)

    if total_glob > 0:
        glob_class_weights = torch.tensor(
            [total_glob / (N_SENT * max(count, 1)) for count in glob_counts],
            dtype=torch.float32,
            device=device,
        )
        glob_class_weights = torch.clamp(glob_class_weights, min=0.7, max=2.0)
    else:
        glob_class_weights = torch.ones(N_SENT, dtype=torch.float32, device=device)

    return sent_counts, glob_counts, sent_class_weights, glob_class_weights


def build_sample_weights(train_items, contrast_sampler_weight):
    aspect_counts = Counter()
    for item in train_items:
        for aspect_idx, sent in zip(item["span_aspect"].tolist(), item["span_sent"].tolist()):
            if sent == -100 or aspect_idx >= len(ASPECTS):
                continue
            aspect_counts[aspect_idx] += 1

    if aspect_counts:
        max_aspect = max(aspect_counts.values())
    else:
        max_aspect = 1

    sample_weights = []
    for item in train_items:
        weight = 1.0
        valid_sentiments = [sent for sent in item["span_sent"].tolist() if sent != -100]
        valid_aspects = [aspect for aspect, sent in zip(item["span_aspect"].tolist(), item["span_sent"].tolist())
                         if sent != -100 and aspect < len(ASPECTS)]

        if is_gold_contrast(item["span_sent"]):
            weight *= contrast_sampler_weight

        if 1 in valid_sentiments:
            weight *= 1.20
        if 2 in valid_sentiments:
            weight *= 1.35

        unique_aspects = sorted(set(valid_aspects))
        if len(unique_aspects) >= 2:
            weight *= 1.08

        if unique_aspects:
            rarity_boost = max(max_aspect / max(aspect_counts[aspect], 1) for aspect in unique_aspects)
            rarity_boost = min(rarity_boost, 2.0)
            weight *= 1.0 + 0.12 * (rarity_boost - 1.0)

        sample_weights.append(min(weight, 3.0))

    return sample_weights


# =============================================================================
# EVALUATE — Fix: dùng sorted(predicted_set) thay vì predicted_spans từ loop trên
#            Fix: bỏ aspect_sent_single_f1 redundant
# =============================================================================
def evaluate(model, dataloader, device, max_ops, max_context_window, span_match_iou):
    model.eval()

    pred_spans_all, gold_spans_all = [], []
    sent_pred, sent_gold = [], []
    sent_goldspan_pred, sent_goldspan_gold = [], []
    glob_pred, glob_gold = [], []
    bio_pred_all, bio_gold_all = [], []

    asp_sent_pred = {a: [] for a in ASPECTS}
    asp_sent_gold = {a: [] for a in ASPECTS}
    asp_span_tp = {a: 0 for a in ASPECTS}
    asp_span_fp = {a: 0 for a in ASPECTS}
    asp_span_fn = {a: 0 for a in ASPECTS}

    tas_strict_tp = tas_strict_fp = tas_strict_fn = 0
    tas_relaxed_tp = tas_relaxed_fp = tas_relaxed_fn = 0

    def tas_relaxed_match_count(pred_tuples, gold_tuples, iou_thr):
        used = [False] * len(gold_tuples)
        matched = 0
        for ps, pe, pa, psv in pred_tuples:
            best_iou = -1.0
            best_j = -1
            for j, (gs, ge, ga, gsv) in enumerate(gold_tuples):
                if used[j] or pa != ga or psv != gsv:
                    continue
                inter = max(0, min(pe, ge) - max(ps, gs) + 1)
                union = (pe - ps + 1) + (ge - gs + 1) - inter
                iou = inter / union if union > 0 else 0.0
                if iou >= iou_thr and iou > best_iou:
                    best_iou = iou
                    best_j = j
            if best_j != -1:
                used[best_j] = True
                matched += 1
        return matched

    with torch.inference_mode():
        for batch in dataloader:
            ids = batch["ids"].to(device)
            mask = batch["mask"].to(device)
            spec_mask = batch["spec_mask"].to(device)
            bio = batch["bio"].to(device)

            gold_span_mask = batch["span_mask"].to(device)
            span_sent = batch["span_sent"].to(device)
            span_asp_g = batch["span_aspect"].to(device)
            gold_clause_pos = batch["span_clause_pos"].to(device)

            glob_sent = batch["global"].to(device)
            offsets = batch["offsets"].to(device)
            texts = batch["text"]

            # First forward: get BIO emissions + cached encoder states
            with autocast_context(device):
                _, emiss, _, _, cached, _ = model(ids, mask)

            bio_p = model.crf.decode(emiss, mask=mask.bool())

            pred_sm = torch.zeros(ids.shape[0], max_ops, ids.shape[1], device=device)
            pred_sp_asp = torch.full(
                (ids.shape[0], max_ops),
                len(ASPECTS),
                dtype=torch.long,
                device=device,
            )
            pred_clause_pos = torch.zeros(
                (ids.shape[0], max_ops),
                dtype=torch.long,
                device=device,
            )
            pred_sets = []

            # Build predicted spans from decoded BIO
            for ri, seq in enumerate(bio_p):
                seq_len = int(mask[ri].sum())
                pred_set, pred_mask_row, pred_aspect_row, pred_clause_row = build_predicted_span_inputs(
                    seq,
                    offsets[ri],
                    spec_mask[ri],
                    texts[ri],
                    seq_len,
                    max_ops,
                    max_context_window,
                    device,
                )
                pred_sets.append(pred_set)
                pred_sm[ri] = pred_mask_row
                pred_sp_asp[ri] = pred_aspect_row
                pred_clause_pos[ri] = pred_clause_row

            # Forward 1: predicted spans -> main evaluation metrics
            with autocast_context(device):
                _, _, pred_sent_logits, pred_glob_logits, _, _ = model(
                    ids,
                    mask,
                    span_mask=pred_sm,
                    cached_seq=cached,
                    span_aspect=pred_sp_asp,
                    span_clause_pos=pred_clause_pos,
                    offsets=offsets,
                    texts=texts,
                )

            # Forward 2: gold spans -> diagnostic only: Sent@GoldSpan
            with autocast_context(device):
                _, _, gold_sent_logits, _, _, _ = model(
                    ids,
                    mask,
                    span_mask=gold_span_mask,
                    cached_seq=cached,
                    span_aspect=span_asp_g,
                    span_clause_pos=gold_clause_pos,
                    offsets=offsets,
                    texts=texts,
                )

            for ri in range(ids.shape[0]):
                vl = int(mask[ri].sum())

                pred_set = pred_sets[ri]
                gold_set = extract_spans(bio[ri].tolist()[:vl])

                pred_spans_all.append(pred_set)
                gold_spans_all.append(gold_set)

                # Per-aspect span F1
                for asp in ASPECTS:
                    p_asp = {(s, e) for s, e, a in pred_set if a == asp}
                    g_asp = {(s, e) for s, e, a in gold_set if a == asp}
                    asp_span_tp[asp] += len(p_asp & g_asp)
                    asp_span_fp[asp] += len(p_asp - g_asp)
                    asp_span_fn[asp] += len(g_asp - p_asp)

                # BIO token-level confusion
                vtm = (~spec_mask[ri][:vl]).cpu().tolist()
                for keep, gl, pl in zip(vtm, bio[ri][:vl].cpu().tolist(), bio_p[ri][:vl]):
                    if keep:
                        bio_gold_all.append(gl)
                        bio_pred_all.append(pl)

                # Gold spans + sentiment
                gold_sents = [
                    span_sent[ri, slot].item()
                    for slot in range(max_ops)
                    if span_sent[ri, slot] != -100
                ]
                gold_asps = [
                    span_asp_g[ri, slot].item()
                    for slot in range(max_ops)
                    if span_sent[ri, slot] != -100
                ]

                sorted_gold = sorted(gold_set)
                gold_with_s = [
                    (s, e, a, gold_sents[i], gold_asps[i])
                    for i, (s, e, a) in enumerate(sorted_gold[:len(gold_sents)])
                ]
                pred_with_s = []

                # Diagnostic: Sent@GoldSpan
                for slot in range(max_ops):
                    if span_sent[ri, slot] != -100:
                        pv_goldspan = gold_sent_logits[ri, slot].argmax().item()
                        sent_goldspan_pred.append(pv_goldspan)
                        sent_goldspan_gold.append(span_sent[ri, slot].item())

                # Main sentiment eval: predicted span matched to gold by IoU + aspect
                for si, (ps, pe, pa) in enumerate(sorted(pred_set)[:max_ops]):
                    pv_span = pred_sent_logits[ri, si].argmax().item() if pred_sent_logits is not None else 2
                    pred_with_s.append((ps, pe, pa, pv_span))

                    best_iou, best_sv, best_ai = 0.0, None, None

                    for gs, ge, ga, gsv, gai in gold_with_s:
                        if ga != pa:
                            continue

                        inter = max(0, min(pe, ge) - max(ps, gs) + 1)
                        union = (pe - ps + 1) + (ge - gs + 1) - inter
                        iou = inter / union if union > 0 else 0.0

                        if iou > best_iou:
                            best_iou, best_sv, best_ai = iou, gsv, gai

                    if best_iou >= span_match_iou and pred_sent_logits is not None and best_sv is not None:
                        pv = pv_span
                        sent_pred.append(pv)
                        sent_gold.append(best_sv)

                        asp_name = ASPECTS[best_ai]
                        asp_sent_pred[asp_name].append(pv)
                        asp_sent_gold[asp_name].append(best_sv)

                # TAS strict: exact (span, aspect, sentiment)
                gold_strict = {(gs, ge, ga, gsv) for (gs, ge, ga, gsv, _) in gold_with_s}
                pred_strict = {(ps, pe, pa, psv) for (ps, pe, pa, psv) in pred_with_s}
                strict_tp = len(pred_strict & gold_strict)
                tas_strict_tp += strict_tp
                tas_strict_fp += max(0, len(pred_strict) - strict_tp)
                tas_strict_fn += max(0, len(gold_strict) - strict_tp)

                # TAS relaxed: IoU + aspect + sentiment
                relaxed_tp = tas_relaxed_match_count(pred_with_s, list(gold_strict), span_match_iou)
                tas_relaxed_tp += relaxed_tp
                tas_relaxed_fp += max(0, len(pred_with_s) - relaxed_tp)
                tas_relaxed_fn += max(0, len(gold_strict) - relaxed_tp)

            # Global eval uses predicted spans, not gold spans
            if (glob_sent != -1).any():
                glob_pred.extend(pred_glob_logits.argmax(-1)[glob_sent != -1].cpu().tolist())
                glob_gold.extend(glob_sent[glob_sent != -1].cpu().tolist())

    tp = sum(len(p & g) for p, g in zip(pred_spans_all, gold_spans_all))
    fp = sum(len(p - g) for p, g in zip(pred_spans_all, gold_spans_all))
    fn = sum(len(g - p) for p, g in zip(pred_spans_all, gold_spans_all))

    span_precision = tp / (tp + fp + 1e-9)
    span_recall = tp / (tp + fn + 1e-9)
    span_f1 = 2 * span_precision * span_recall / (span_precision + span_recall + 1e-9)

    if sent_gold:
        sent_p, sent_r, sent_f1, _ = precision_recall_fscore_support(
            sent_gold, sent_pred, labels=[0, 1, 2], average="macro", zero_division=0
        )
    else:
        sent_p = sent_r = sent_f1 = 0.0

    if sent_goldspan_gold:
        sg_p, sg_r, sg_f1, _ = precision_recall_fscore_support(
            sent_goldspan_gold, sent_goldspan_pred, labels=[0, 1, 2], average="macro", zero_division=0
        )
    else:
        sg_p = sg_r = sg_f1 = 0.0

    if glob_gold:
        g_p, g_r, g_f1, _ = precision_recall_fscore_support(
            glob_gold, glob_pred, labels=[0, 1, 2], average="macro", zero_division=0
        )
    else:
        g_p = g_r = g_f1 = 0.0

    tas_strict_p = tas_strict_tp / (tas_strict_tp + tas_strict_fp + 1e-9)
    tas_strict_r = tas_strict_tp / (tas_strict_tp + tas_strict_fn + 1e-9)
    tas_strict_f1 = 2 * tas_strict_p * tas_strict_r / (tas_strict_p + tas_strict_r + 1e-9)

    tas_relaxed_p = tas_relaxed_tp / (tas_relaxed_tp + tas_relaxed_fp + 1e-9)
    tas_relaxed_r = tas_relaxed_tp / (tas_relaxed_tp + tas_relaxed_fn + 1e-9)
    tas_relaxed_f1 = 2 * tas_relaxed_p * tas_relaxed_r / (tas_relaxed_p + tas_relaxed_r + 1e-9)

    asp_sent_f1 = {}
    asp_span_f1 = {}
    asp_support = {}
    asp_sent_pred_dist = {}
    asp_sent_gold_dist = {}

    for asp in ASPECTS:
        asp_sent_f1[asp] = (
            f1_score(asp_sent_gold[asp], asp_sent_pred[asp], average="macro", zero_division=0)
            if asp_sent_gold[asp] else 0.0
        )

        t = asp_span_tp[asp]
        fp_ = asp_span_fp[asp]
        fn_ = asp_span_fn[asp]
        asp_span_f1[asp] = 2 * t / (2 * t + fp_ + fn_ + 1e-9)

        pc = Counter(asp_sent_pred[asp])
        gc = Counter(asp_sent_gold[asp])

        asp_sent_pred_dist[asp] = {
            "NEG": int(pc.get(0, 0)),
            "POS": int(pc.get(1, 0)),
            "NEU": int(pc.get(2, 0)),
            "TOTAL": int(len(asp_sent_pred[asp])),
        }

        asp_sent_gold_dist[asp] = {
            "NEG": int(gc.get(0, 0)),
            "POS": int(gc.get(1, 0)),
            "NEU": int(gc.get(2, 0)),
            "TOTAL": int(len(asp_sent_gold[asp])),
        }
        asp_support[asp] = int(len(asp_sent_gold[asp]))

    sent_cls_p, sent_cls_r, sent_cls_f1, sent_cls_support = precision_recall_fscore_support(
        sent_gold,
        sent_pred,
        labels=[0, 1, 2],
        average=None,
        zero_division=0,
    ) if sent_gold else ([0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0, 0, 0])

    global_cls_p, global_cls_r, global_cls_f1, global_cls_support = precision_recall_fscore_support(
        glob_gold,
        glob_pred,
        labels=[0, 1, 2],
        average=None,
        zero_division=0,
    ) if glob_gold else ([0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0, 0, 0])

    return {
        "tas_strict": {"precision": tas_strict_p, "recall": tas_strict_r, "f1": tas_strict_f1},
        "tas_relaxed": {"precision": tas_relaxed_p, "recall": tas_relaxed_r, "f1": tas_relaxed_f1},
        "span": {"precision": span_precision, "recall": span_recall, "f1": span_f1},
        "sent_matched": {"precision": sent_p, "recall": sent_r, "f1": sent_f1},
        "sent_goldspan": {"precision": sg_p, "recall": sg_r, "f1": sg_f1},
        "global": {"precision": g_p, "recall": g_r, "f1": g_f1},
        "asp_sent_f1": asp_sent_f1,
        "asp_span_f1": asp_span_f1,
        "asp_support": asp_support,
        "asp_sent_pred_dist": asp_sent_pred_dist,
        "asp_sent_gold_dist": asp_sent_gold_dist,
        "class_metrics": {
            "sentiment": {
                "NEG": {"precision": float(sent_cls_p[0]), "recall": float(sent_cls_r[0]), "f1": float(sent_cls_f1[0]), "support": int(sent_cls_support[0])},
                "POS": {"precision": float(sent_cls_p[1]), "recall": float(sent_cls_r[1]), "f1": float(sent_cls_f1[1]), "support": int(sent_cls_support[1])},
                "NEU": {"precision": float(sent_cls_p[2]), "recall": float(sent_cls_r[2]), "f1": float(sent_cls_f1[2]), "support": int(sent_cls_support[2])},
            },
            "global": {
                "NEG": {"precision": float(global_cls_p[0]), "recall": float(global_cls_r[0]), "f1": float(global_cls_f1[0]), "support": int(global_cls_support[0])},
                "POS": {"precision": float(global_cls_p[1]), "recall": float(global_cls_r[1]), "f1": float(global_cls_f1[1]), "support": int(global_cls_support[1])},
                "NEU": {"precision": float(global_cls_p[2]), "recall": float(global_cls_r[2]), "f1": float(global_cls_f1[2]), "support": int(global_cls_support[2])},
            },
        },
        "confusion_matrices": {
            "bio": confusion_payload(bio_gold_all, bio_pred_all, list(range(N_BIO)), BIO_LABELS),
            "sentiment": confusion_payload(sent_gold, sent_pred, [0, 1, 2], label_names_for_sentiment()),
            "sentiment_goldspan": confusion_payload(
                sent_goldspan_gold,
                sent_goldspan_pred,
                [0, 1, 2],
                label_names_for_sentiment(),
            ),
            "global": confusion_payload(glob_gold, glob_pred, [0, 1, 2], label_names_for_sentiment()),
        },
    }

# =============================================================================
# SAVE METRICS
# =============================================================================
def save_metrics(csv_path, epoch, phase, train_m, eval_m, is_best):
    base_header = [
        "epoch", "phase", "train_loss", "bio_loss", "sent_loss",
        "glob_loss", "cons_loss", "ctr_loss",
        "w_bio", "w_sent", "w_global", "w_cons", "w_contrast",
        "tas_strict_p", "tas_strict_r", "tas_strict_f1",
        "tas_relaxed_p", "tas_relaxed_r", "tas_relaxed_f1",
        "span_p", "span_r", "span_f1",
        "sent_matched_p", "sent_matched_r", "sent_matched_f1",
        "sent_goldspan_p", "sent_goldspan_r", "sent_goldspan_f1",
        "global_p", "global_r", "global_f1",
        "is_best",
    ]
    # Per-aspect F1
    asp_headers = []
    for asp in ASPECTS:
        asp_headers.append(f"span_f1_{asp}")
    for asp in ASPECTS:
        asp_headers.append(f"sent_f1_{asp}")
    # Per-aspect sentiment distribution (pred + gold)
    for asp in ASPECTS:
        asp_headers.extend([f"pred_NEG_{asp}", f"pred_POS_{asp}", f"pred_NEU_{asp}", f"pred_TOTAL_{asp}"])
    for asp in ASPECTS:
        asp_headers.extend([f"gold_NEG_{asp}", f"gold_POS_{asp}", f"gold_NEU_{asp}", f"gold_TOTAL_{asp}"])

    header = base_header + asp_headers

    def ensure_header(path: Path, desired_header: list[str]) -> None:
        if not path.exists():
            return
        try:
            with open(path, newline="", encoding="utf-8") as rf:
                r = csv.reader(rf)
                cur_header = next(r, None)
                if cur_header == desired_header:
                    return
                rows = [row for row in r]
        except Exception:
            return
        # Rewrite with desired header; keep existing rows (pad/truncate) for continuity.
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", newline="", encoding="utf-8") as wf:
            w2 = csv.writer(wf)
            w2.writerow(desired_header)
            for row in rows:
                if len(row) < len(desired_header):
                    row = row + [""] * (len(desired_header) - len(row))
                elif len(row) > len(desired_header):
                    row = row[:len(desired_header)]
                w2.writerow(row)
        tmp.replace(path)

    ensure_header(csv_path, header)
    exists = csv_path.exists()
    with open(csv_path, "a" if exists else "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(header)

        row = [
            epoch, phase,
            f"{train_m['loss']:.4f}", f"{train_m['bio_loss']:.4f}",
            f"{train_m['sent_loss']:.4f}", f"{train_m['global_loss']:.4f}",
            f"{train_m['consistency_loss']:.4f}", f"{train_m['contrast_loss']:.4f}",
            f"{train_m['w_bio']:.4f}", f"{train_m['w_sent']:.4f}",
            f"{train_m['w_global']:.4f}", f"{train_m['w_cons']:.4f}",
            f"{train_m['w_contrast']:.4f}",
            f"{eval_m['tas_strict']['precision']:.4f}",
            f"{eval_m['tas_strict']['recall']:.4f}",
            f"{eval_m['tas_strict']['f1']:.4f}",
            f"{eval_m['tas_relaxed']['precision']:.4f}",
            f"{eval_m['tas_relaxed']['recall']:.4f}",
            f"{eval_m['tas_relaxed']['f1']:.4f}",
            f"{eval_m['span']['precision']:.4f}",
            f"{eval_m['span']['recall']:.4f}",
            f"{eval_m['span']['f1']:.4f}",
            f"{eval_m['sent_matched']['precision']:.4f}",
            f"{eval_m['sent_matched']['recall']:.4f}",
            f"{eval_m['sent_matched']['f1']:.4f}",
            f"{eval_m['sent_goldspan']['precision']:.4f}",
            f"{eval_m['sent_goldspan']['recall']:.4f}",
            f"{eval_m['sent_goldspan']['f1']:.4f}",
            f"{eval_m['global']['precision']:.4f}",
            f"{eval_m['global']['recall']:.4f}",
            f"{eval_m['global']['f1']:.4f}",
            "best" if is_best else "",
        ]

        asp_span_f1 = eval_m.get("asp_span_f1", {}) or {}
        asp_sent_f1 = eval_m.get("asp_sent_f1", {}) or {}
        pred_dist = eval_m.get("asp_sent_pred_dist", {}) or {}
        gold_dist = eval_m.get("asp_sent_gold_dist", {}) or {}

        for asp in ASPECTS:
            row.append(f"{float(asp_span_f1.get(asp, 0.0)):.4f}")
        for asp in ASPECTS:
            row.append(f"{float(asp_sent_f1.get(asp, 0.0)):.4f}")
        for asp in ASPECTS:
            d = pred_dist.get(asp, {})
            row.extend([d.get("NEG", 0), d.get("POS", 0), d.get("NEU", 0), d.get("TOTAL", 0)])
        for asp in ASPECTS:
            d = gold_dist.get(asp, {})
            row.extend([d.get("NEG", 0), d.get("POS", 0), d.get("NEU", 0), d.get("TOTAL", 0)])

        w.writerow(row)


# =============================================================================
# ARGS
# =============================================================================
def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--train-file",             type=Path,  default=DEFAULT_TRAIN_FILE)
    p.add_argument("--val-file",               type=Path,  default=DEFAULT_VAL_FILE)
    p.add_argument("--output-dir",             type=Path,  default=DEFAULT_OUTPUT_DIR)
    p.add_argument("--model-name",             default="vinai/phobert-base")
    p.add_argument("--seed",                   type=int,   default=42)
    p.add_argument("--max-len",                type=int,   default=192,
                   help="p50 text ~82 chars; 192 covers p95 without 224 cost")
    p.add_argument("--epochs",                 type=int,   default=50)
    p.add_argument("--patience",               type=int,   default=8)
    p.add_argument("--phase1-epochs",          type=int,   default=2)
    p.add_argument("--max-ops",                type=int,   default=6,
                   help="train max 6 opinions/sample; only 2 rows need >6")
    p.add_argument("--batch-size",             type=int,   default=24)
    p.add_argument("--eval-batch-size",        type=int,   default=64)
    p.add_argument("--grad-accum-steps",       type=int,   default=1)
    p.add_argument("--num-workers",            type=int,   default=2)
    p.add_argument("--eval-every",             type=int,   default=1,
                   help="validate every N epochs (phase2); phase1 always evals")
    p.add_argument("--save-all-confusion",     action="store_true",
                   help="write confusion_matrices.jsonl every epoch (slower I/O)")
    p.add_argument("--lr-backbone",            type=float, default=8e-6)
    p.add_argument("--lr-heads",               type=float, default=3e-5)
    p.add_argument("--max-context-window",     type=int,   default=25)
    p.add_argument("--span-match-iou",         type=float, default=0.5)
    p.add_argument("--contrast-margin",        type=float, default=0.25)
    p.add_argument("--lambda-bio",             type=float, default=1.1)
    p.add_argument("--lambda-sent",            type=float, default=1.4)
    p.add_argument("--lambda-global",          type=float, default=0.2)
    p.add_argument("--lambda-cons",            type=float, default=0)
    p.add_argument("--lambda-contrast",        type=float, default=0)
    p.add_argument("--contrast-sampler-weight",type=float, default=1.2)
    p.add_argument("--lbtw-ema-decay",         type=float, default=0.99)
    p.add_argument("--lbtw-min-factor",        type=float, default=0.3)
    p.add_argument("--lbtw-max-factor",        type=float, default=3.0)
    p.add_argument("--ema-decay",              type=float, default=0.999)
    p.add_argument("--ema-start-epoch",        type=int,   default=3)
    p.add_argument("--disable-ema",            action="store_true")
    p.add_argument("--disable-tf32",           action="store_true")
    p.add_argument("--rdrop-alpha",            type=float, default=0.0)
    p.add_argument("--pred-span-ratio",        type=float, default=0.1,
                   help="Phase2 ratio of samples using predicted spans (rest uses gold spans)")
    args, unknown = p.parse_known_args()
    if unknown:
        print(f"Ignoring unknown args: {unknown}")
    return args


# =============================================================================
# MAIN
# =============================================================================
def main():
    args   = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if device.type == "cuda" and args.disable_tf32:
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False

    for path in [args.train_file, args.val_file]:
        if not path.exists():
            raise FileNotFoundError(f"Missing: {path}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    best_model_path    = args.output_dir / "best_model.pt"
    checkpoint_path    = args.output_dir / "checkpoint.pt"
    metrics_csv_path   = args.output_dir / "train_log.csv"
    confusion_jsonl    = args.output_dir / "confusion_matrices.jsonl"
    best_confusion     = args.output_dir / "best_confusion_matrices.json"

    with open(args.output_dir / "run_config.json", "w", encoding="utf-8") as f:
        json.dump({k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
                  f, ensure_ascii=False, indent=2)

    set_seed(args.seed)
    print(f"Device: {device} | Train: {args.train_file} | Val: {args.val_file}")

    tokenizer = load_tokenizer(args.model_name)
    train_ds  = ABSADataset(args.train_file, tokenizer, args.max_len, args.max_ops, args.max_context_window)
    val_ds    = ABSADataset(args.val_file,   tokenizer, args.max_len, args.max_ops, args.max_context_window)

    sent_counts, glob_counts, sent_class_weights, glob_class_weights = build_class_weights(train_ds.items, device)
    total_sent = sum(sent_counts)
    total_glob = sum(glob_counts)
    print(f"Sent weights [NEG/POS/NEU]: {[round(w, 3) for w in sent_class_weights.tolist()]}")
    print(f"Glob weights [NEG/POS/NEU]: {[round(w, 3) for w in glob_class_weights.tolist()]}")
    print(f"Sent dist    [NEG/POS/NEU]: {[round(c/max(total_sent,1), 3) for c in sent_counts]}")
    print(f"Glob dist    [NEG/POS/NEU]: {[round(c/max(total_glob,1), 3) for c in glob_counts]}")

    # Sampler
    sample_w = build_sample_weights(train_ds.items, args.contrast_sampler_weight)
    loader_kwargs = {
        "num_workers": args.num_workers,
        "pin_memory": device.type == "cuda",
    }
    if args.num_workers > 0:
        loader_kwargs["persistent_workers"] = True
        loader_kwargs["prefetch_factor"] = 2

    train_dl = DataLoader(train_ds, batch_size=args.batch_size,
                          sampler=WeightedRandomSampler(sample_w, len(train_ds), replacement=True),
                          **loader_kwargs)
    val_dl   = DataLoader(val_ds, batch_size=args.eval_batch_size, shuffle=False,
                          **loader_kwargs)

    model = ABSAModel(args.model_name, args.max_ops).to(device).float()
    model_ema = None if args.disable_ema else ModelEMA(model, decay=args.ema_decay)
    optimizer = AdamW([
        {"params": model.backbone.parameters(),
         "lr": args.lr_backbone, "weight_decay": 0.01},
        {"params": [p for n, p in model.named_parameters() if "backbone" not in n],
         "lr": args.lr_heads},
    ])
    task_weighter = LBTWWeighter(
        {
            "bio": args.lambda_bio,
            "sent": args.lambda_sent,
            "global": args.lambda_global,
            "cons": args.lambda_cons,
            "contrast": args.lambda_contrast,
        },
        ema_decay=args.lbtw_ema_decay,
        clamp_min=args.lbtw_min_factor,
        clamp_max=args.lbtw_max_factor,
    )

    steps_per_ep       = max(1, (len(train_dl) + args.grad_accum_steps - 1) // args.grad_accum_steps)
    total_steps_all    = steps_per_ep * args.epochs
    est_min_per_ep     = steps_per_ep * 0.22  # ~0.22s/step T4 rough
    print(
        f"Steps/epoch≈{steps_per_ep} | est ~{est_min_per_ep:.1f} min/ep train "
        f"| cap {args.epochs} ep + patience {args.patience} → ~{est_min_per_ep * min(args.epochs, args.patience + args.phase1_epochs + 5):.0f} min train"
    )
    phase1_steps       = steps_per_ep * args.phase1_epochs
    phase2_steps       = max(1, total_steps_all - phase1_steps)
    warmup_heads_steps = max(1, int(0.05 * total_steps_all))
    warmup_bb_steps    = min(2 * steps_per_ep, max(1, int(0.10 * phase2_steps)))

    def lr_lambda_heads(step: int) -> float:
        # Warmup + cosine decay for heads over ALL steps.
        if step < warmup_heads_steps:
            return step / max(1, warmup_heads_steps)
        progress = (step - warmup_heads_steps) / max(1, (total_steps_all - warmup_heads_steps))
        return max(0.0, 0.5 * (1.0 + np.cos(np.pi * progress)))

    def lr_lambda_backbone(step: int) -> float:
        # Phase1: backbone frozen -> force LR=0 so scheduler state doesn't "consume" the curve.
        if step < phase1_steps:
            return 0.0
        step2 = step - phase1_steps
        if step2 < warmup_bb_steps:
            return step2 / max(1, warmup_bb_steps)
        progress = (step2 - warmup_bb_steps) / max(1, (phase2_steps - warmup_bb_steps))
        return max(0.0, 0.5 * (1.0 + np.cos(np.pi * progress)))

    # NOTE: optimizer has 2 param groups: [backbone, heads]
    scheduler = LambdaLR(optimizer, lr_lambda=[lr_lambda_backbone, lr_lambda_heads])
    scaler = torch.amp.GradScaler(enabled=device.type == "cuda")

    best_score, patience_cnt, start_ep = 0.0, 0, 1
    if checkpoint_path.exists():
        print(f"Checkpoint present but ignored for fresh training: {checkpoint_path}")
    if model_ema is not None:
        print(f"EMA enabled with decay={args.ema_decay} (starts at epoch {args.ema_start_epoch})")
    if device.type == "cuda":
        print(f"TF32 matmul={'on' if torch.backends.cuda.matmul.allow_tf32 else 'off'}")

    for epoch in range(start_ep, args.epochs + 1):
        in_phase1 = epoch <= args.phase1_epochs

        # Freeze/unfreeze backbone
        for p in model.backbone.parameters():
            p.requires_grad = not in_phase1

        model.train()
        contrast_scale = min(1.0, (epoch - args.phase1_epochs) / 2.0) if not in_phase1 else 0.0
        sums = {
            k: 0.0 for k in [
                "loss", "bio_loss", "sent_loss", "global_loss", "consistency_loss", "contrast_loss",
                "w_bio", "w_sent", "w_global", "w_cons", "w_contrast",
            ]
        }
        n_steps = 0

        pbar = tqdm(train_dl, desc=f"Epoch {epoch:02d} [{'BIO' if in_phase1 else 'FULL'}]")
        optimizer.zero_grad(set_to_none=True)

        for step, batch in enumerate(pbar, start=1):
            ids        = batch["ids"].to(device)
            mask       = batch["mask"].to(device)
            spec_mask  = batch["spec_mask"].to(device)
            bio        = batch["bio"].to(device)
            span_mask  = batch["span_mask"].to(device)
            span_sent  = batch["span_sent"].to(device)
            span_asp   = batch["span_aspect"].to(device)
            span_clause = batch["span_clause_pos"].to(device)
            glob_sent  = batch["global"].to(device)
            offsets    = batch["offsets"].to(device)
            texts      = batch["text"]

            with autocast_context(device):
                crf_loss, emiss, _, glob_logits, cached_seq, span_features = model(
                    ids, mask, span_mask=None, bio=bio,
                )

                sent_logits = None
                mixed_span_sent = span_sent
                if not in_phase1:
                    phase2_epoch = epoch - args.phase1_epochs
                    if phase2_epoch <= 3:
                        mix_ratio = 0.0
                    elif phase2_epoch <= 8:
                        mix_ratio = min(max(float(args.pred_span_ratio), 0.0), 0.15)
                    else:
                        mix_ratio = min(max(float(args.pred_span_ratio), 0.0), 1.0)

                    mixed_span_mask = span_mask
                    mixed_span_asp = span_asp
                    mixed_span_clause = span_clause
                    pred_span_sent = span_sent

                    if mix_ratio > 0.0:
                        bio_p = model.crf.decode(emiss, mask=mask.bool())
                        pred_sm = torch.zeros(ids.shape[0], args.max_ops, ids.shape[1], device=device)
                        pred_sp_asp = torch.full(
                            (ids.shape[0], args.max_ops), len(ASPECTS), dtype=torch.long, device=device
                        )
                        pred_clause_pos = torch.zeros((ids.shape[0], args.max_ops), dtype=torch.long, device=device)
                        pred_sets = []
                        pred_span_sent = torch.full_like(span_sent, -100)

                        for ri, seq in enumerate(bio_p):
                            seq_len = int(mask[ri].sum())
                            pred_set, pred_mask_row, pred_aspect_row, pred_clause_row = build_predicted_span_inputs(
                                seq,
                                offsets[ri],
                                spec_mask[ri],
                                texts[ri],
                                seq_len,
                                args.max_ops,
                                args.max_context_window,
                                device,
                            )
                            pred_sets.append(pred_set)
                            pred_sm[ri] = pred_mask_row
                            pred_sp_asp[ri] = pred_aspect_row
                            pred_clause_pos[ri] = pred_clause_row

                            gold_set = extract_spans(bio[ri].tolist()[:seq_len])
                            gold_sents = [
                                span_sent[ri, slot].item()
                                for slot in range(args.max_ops)
                                if span_sent[ri, slot] != -100
                            ]
                            pred_span_sent[ri] = build_predicted_span_labels(
                                pred_sets[ri],
                                gold_set,
                                gold_sents,
                                args.max_ops,
                                args.span_match_iou,
                                device,
                            )

                        use_pred = (torch.rand(ids.shape[0], device=device) < mix_ratio)
                        use_pred_3d = use_pred.view(-1, 1, 1)
                        use_pred_2d = use_pred.view(-1, 1)
                        mixed_span_mask = torch.where(use_pred_3d, pred_sm, span_mask)
                        mixed_span_asp = torch.where(use_pred_2d, pred_sp_asp, span_asp)
                        mixed_span_clause = torch.where(use_pred_2d, pred_clause_pos, span_clause)
                        mixed_span_sent = torch.where(use_pred_2d, pred_span_sent, span_sent)

                    _, _, sent_logits, glob_logits, _, span_features = model(
                        ids,
                        mask,
                        span_mask=mixed_span_mask,
                        cached_seq=cached_seq,
                        span_aspect=mixed_span_asp,
                        span_clause_pos=mixed_span_clause,
                        offsets=offsets,
                        texts=texts,
                    )

                sent_logits_r = None
                glob_logits_r = None
                if not in_phase1 and args.rdrop_alpha > 0:
                    _, _, sent_logits_r, glob_logits_r, _, _ = model(
                        ids, mask,
                        span_mask=mixed_span_mask,
                        bio=bio,
                        span_aspect=mixed_span_asp,
                        span_clause_pos=mixed_span_clause,
                        offsets=offsets,
                        texts=texts,
                    )

                sent_loss = (
                    focal_loss(sent_logits.view(-1, N_SENT), mixed_span_sent.view(-1),
                               weight=sent_class_weights, gamma=1.5, # Đẩy gamma lên 1.5
                               ignore_index=-100, label_smoothing=[0.005, 0.005, 0.015])
                    if not in_phase1 else torch.tensor(0.0, device=device)
                )

                v_g = (glob_sent != -1)
                glob_loss = (
                    smoothed_cross_entropy(glob_logits, glob_sent,
                                           weight=glob_class_weights,
                                           ignore_index=-1,
                                           label_smoothing=[0.01, 0.01, 0.05])
                    if (not in_phase1 and v_g.any()) else torch.tensor(0.0, device=device)
                )

                ctr_loss = (
                    contrast_loss_fn(span_features, mixed_span_sent, glob_sent, args.contrast_margin, device)
                    if not in_phase1 else torch.tensor(0.0, device=device)
                )

                cons_loss = torch.tensor(0.0, device=device)
                if not in_phase1:
                    vm = (mixed_span_sent != -100).float()
                    if vm.sum() > 0 and v_g.any():
                        span_avg = (sent_logits * vm.unsqueeze(-1)).sum(1) / \
                                   vm.sum(1, keepdim=True).clamp(min=1)
                        gold_dist = torch.full((glob_sent.shape[0], N_SENT), 0.1, device=device)
                        for ri in range(glob_sent.shape[0]):
                            if glob_sent[ri] != -1:
                                gold_dist[ri, glob_sent[ri]] = 0.8
                        cons_loss = F.kl_div(
                            F.log_softmax(span_avg[v_g], dim=-1),
                            gold_dist[v_g], reduction="batchmean",
                        )

                    if sent_logits_r is not None and glob_logits_r is not None:
                        valid_span_mask = (mixed_span_sent != -100)
                        sent_rdrop = symmetric_kl_loss(sent_logits[valid_span_mask], sent_logits_r[valid_span_mask])
                        glob_rdrop = symmetric_kl_loss(glob_logits[v_g], glob_logits_r[v_g]) if v_g.any() else torch.tensor(0.0, device=device)
                        cons_loss = cons_loss + args.rdrop_alpha * (sent_rdrop + 0.5 * glob_rdrop)

                if in_phase1:
                    task_weights = task_weighter.base_snapshot(active_names=["bio"])
                    total_loss = (
                        task_weights["bio"] * crf_loss
                    )
                else:
                    phase2_losses = {
                        "bio": crf_loss,
                        "sent": sent_loss,
                    }
                    if args.lambda_global > 0:
                        phase2_losses["global"] = glob_loss
                    if args.lambda_cons > 0:
                        phase2_losses["cons"] = cons_loss
                    if args.lambda_contrast > 0 and contrast_scale > 0:
                        phase2_losses["contrast"] = contrast_scale * ctr_loss
                        
                    task_weights = task_weighter.compute_weights(phase2_losses)
                    task_weights.setdefault("global", 0.0)
                    task_weights.setdefault("cons", 0.0)
                    task_weights.setdefault("contrast", 0.0)
                    
                    total_loss = task_weighter.combine(phase2_losses, task_weights)

                loss = total_loss.float() / args.grad_accum_steps

            if not torch.isfinite(loss):
                print(
                    f"Skip non-finite batch at epoch={epoch} step={step}: "
                    f"bio={float(crf_loss.detach()):.4f}, sent={float(sent_loss.detach()):.4f}, "
                    f"glob={float(glob_loss.detach()):.4f}, cons={float(cons_loss.detach()):.4f}, "
                    f"ctr={float(ctr_loss.detach()):.4f}, total={float(total_loss.detach()):.4f}"
                )
                optimizer.zero_grad(set_to_none=True)
                continue

            scaler.scale(loss).backward()

            if step % args.grad_accum_steps == 0 or step == len(train_dl):
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optimizer)
                scaler.update()
                if model_ema is not None:
                    model_ema.update(model)
                scheduler.step()
                optimizer.zero_grad(set_to_none=True)

            raw = loss.item() * args.grad_accum_steps
            sums["loss"]             += raw
            sums["bio_loss"]         += crf_loss.detach().item()
            sums["sent_loss"]        += sent_loss.detach().item()
            sums["global_loss"]      += glob_loss.detach().item()
            sums["consistency_loss"] += cons_loss.detach().item()
            sums["contrast_loss"]    += ctr_loss.detach().item()
            sums["w_bio"]            += task_weights["bio"]
            sums["w_sent"]           += task_weights["sent"]
            sums["w_global"]         += task_weights["global"]
            sums["w_cons"]           += task_weights["cons"]
            sums["w_contrast"]       += task_weights["contrast"]
            n_steps += 1
            pbar.set_postfix({"loss": f"{raw:.3f}"})

        train_m = {k: v / max(n_steps, 1) for k, v in sums.items()}

        run_eval = (
            in_phase1
            or epoch % max(1, args.eval_every) == 0
            or epoch == args.epochs
        )
        if not run_eval:
            print(
                f"Ep {epoch:02d} | loss={train_m['loss']:.4f} | "
                f"(skip dev eval, eval_every={args.eval_every})"
            )
            continue

        use_ema_eval = (
            model_ema is not None and
            epoch >= args.ema_start_epoch and
            model_ema.num_updates > 0
        )
        if use_ema_eval:
            model_ema.apply_to(model)
        try:
            eval_m = evaluate(model, val_dl, device, args.max_ops, args.max_context_window, args.span_match_iou)
        finally:
            if use_ema_eval:
                model_ema.restore(model)

        print(
            f"Ep {epoch:02d} | loss={train_m['loss']:.4f} | "
            f"TAS-Strict={eval_m['tas_strict']['f1']:.4f} | "
            f"TAS-Relaxed={eval_m['tas_relaxed']['f1']:.4f} | "
            f"Span={eval_m['span']['f1']:.4f} | "
            f"Sent@Matched={eval_m['sent_matched']['f1']:.4f} | "
            f"Sent@GoldSpan={eval_m['sent_goldspan']['f1']:.4f} | "
            f"Global={eval_m['global']['f1']:.4f}"
        )
        print("  Aspect sent F1:", {a: f"{v:.3f}" for a, v in eval_m["asp_sent_f1"].items()})
        print("  Aspect span F1:", {a: f"{v:.3f}" for a, v in eval_m["asp_span_f1"].items()})

        is_best = eval_m["tas_relaxed"]["f1"] > best_score
        if is_best:
            best_score, patience_cnt = eval_m["tas_relaxed"]["f1"], 0
            if use_ema_eval:
                model_ema.apply_to(model)
            try:
                torch.save(model.state_dict(), best_model_path)
            finally:
                if use_ema_eval:
                    model_ema.restore(model)
            print(f"  ⭐ New best: {best_score:.4f} → {best_model_path}")
            with open(best_confusion, "w", encoding="utf-8") as f:
                json.dump({"epoch": epoch, "best_metric": "tas_relaxed_f1", "tas_relaxed_f1": best_score,
                           "matrices": eval_m["confusion_matrices"]}, f,
                          ensure_ascii=False, indent=2)
        else:
            patience_cnt += 1

        if in_phase1 and epoch == args.phase1_epochs:
            best_score, patience_cnt = 0.0, 0
            print("--- Phase 2 start: reset early-stop ---")

        save_metrics(metrics_csv_path, epoch, "phase1" if in_phase1 else "phase2",
                     train_m, eval_m, is_best)
        if args.save_all_confusion or is_best:
            save_confusion_matrices(confusion_jsonl, epoch, "phase1" if in_phase1 else "phase2",
                                    eval_m["confusion_matrices"], is_best)

        if not in_phase1 and patience_cnt >= args.patience:
            print("Early stopping.")
            break


if __name__ == "__main__":
    main()