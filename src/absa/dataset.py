"""ABSADataset and span-building helpers — extracted verbatim from train/train.py."""

from __future__ import annotations

import json

import torch
from torch.utils.data import Dataset
from transformers import PreTrainedTokenizerBase

from .labels import ASPECTS, BIO_L2I, BIO_I2L
from .utils import nfc

TOKENIZE_BATCH_SIZE = 512


# ---------------------------------------------------------------------------
# Helper functions — verbatim from train/train.py
# ---------------------------------------------------------------------------

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
    contrast_words = {"nhưng", "tuy", "dù", "mà", "song", "còn", "tuy_nhiên", "thế_nhưng"}
    contrast_pos = None
    for idx in range(seq_len):
        cs = int(offsets_row[idx][0])
        ce = int(offsets_row[idx][1])
        token = text[cs:ce].lower().strip()
        if token in contrast_words:
            contrast_pos = idx
            break
    if contrast_pos is None:
        return 0
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


# ---------------------------------------------------------------------------
# Dataset class — verbatim from train/train.py
# ---------------------------------------------------------------------------

class ABSADataset(Dataset):
    def __init__(
        self,
        file_path,
        tokenizer: PreTrainedTokenizerBase,
        max_len: int,
        max_ops: int,
        max_context_window: int,
    ):
        self.items = []
        with open(file_path, encoding="utf-8") as f:
            records = [json.loads(line) for line in f if line.strip()]
        print(f"Pre-tokenizing {len(records)} records from {file_path}...")

        for start_idx in range(0, len(records), TOKENIZE_BATCH_SIZE):
            batch_records = records[start_idx:start_idx + TOKENIZE_BATCH_SIZE]
            batch_texts = [nfc(record["text"]) for record in batch_records]
            enc = tokenizer(
                batch_texts,
                max_length=max_len,
                padding="max_length",
                truncation=True,
                return_offsets_mapping=True,
                return_special_tokens_mask=True,
            )

            for record, text, input_ids, attention_mask, offsets, spec_mask in zip(
                batch_records,
                batch_texts,
                enc["input_ids"],
                enc["attention_mask"],
                enc["offset_mapping"],
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
