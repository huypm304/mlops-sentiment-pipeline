"""Metric helpers — extracted from train/train.py (evaluate function internals).

All formulas are verbatim. Do not alter P/R/F1 calculations.
"""

from __future__ import annotations

from collections import Counter

from sklearn.metrics import confusion_matrix, f1_score, precision_recall_fscore_support

from .labels import ASPECTS, BIO_LABELS, N_BIO


def label_names_for_sentiment() -> list[str]:
    return ["NEG", "POS", "NEU"]


def confusion_payload(gold, pred, labels, label_names):
    matrix = confusion_matrix(gold, pred, labels=labels).tolist() if gold and pred else []
    normalized = []
    if matrix:
        for row in matrix:
            row_sum = sum(row)
            normalized.append([round(v / row_sum, 6) if row_sum else 0.0 for v in row])
    return {"labels": label_names, "raw": matrix, "normalized": normalized, "support": len(gold)}


def prf_macro(gold, pred, labels=None):
    """Return (precision, recall, f1) macro average; safe for empty lists."""
    if not gold:
        return 0.0, 0.0, 0.0
    lbl = labels if labels is not None else [0, 1, 2]
    p, r, f, _ = precision_recall_fscore_support(gold, pred, labels=lbl, average="macro", zero_division=0)
    return float(p), float(r), float(f)


def prf_per_class(gold, pred, labels=None):
    """Return (p_arr, r_arr, f_arr, support_arr) per class; safe for empty."""
    lbl = labels if labels is not None else [0, 1, 2]
    if not gold:
        z = [0.0] * len(lbl)
        return z, z, z, [0] * len(lbl)
    p, r, f, s = precision_recall_fscore_support(gold, pred, labels=lbl, average=None, zero_division=0)
    return list(p), list(r), list(f), list(s)


def span_prf(pred_spans_all, gold_spans_all):
    """Span extraction P/R/F1 (set-match, token-level)."""
    tp = sum(len(p & g) for p, g in zip(pred_spans_all, gold_spans_all))
    fp = sum(len(p - g) for p, g in zip(pred_spans_all, gold_spans_all))
    fn = sum(len(g - p) for p, g in zip(pred_spans_all, gold_spans_all))
    precision = tp / (tp + fp + 1e-9)
    recall    = tp / (tp + fn + 1e-9)
    f1        = 2 * precision * recall / (precision + recall + 1e-9)
    return float(precision), float(recall), float(f1)


def tas_prf(tp, fp, fn):
    """Compute P/R/F1 from TP/FP/FN accumulators."""
    p  = tp / (tp + fp + 1e-9)
    r  = tp / (tp + fn + 1e-9)
    f1 = 2 * p * r / (p + r + 1e-9)
    return float(p), float(r), float(f1)


def per_aspect_sent_f1(asp_sent_gold, asp_sent_pred):
    """Return dict {aspect: macro_f1}."""
    return {
        asp: (
            f1_score(asp_sent_gold[asp], asp_sent_pred[asp], average="macro", zero_division=0)
            if asp_sent_gold[asp] else 0.0
        )
        for asp in ASPECTS
    }


def per_aspect_span_f1(asp_span_tp, asp_span_fp, asp_span_fn):
    """Return dict {aspect: f1}."""
    result = {}
    for asp in ASPECTS:
        t  = asp_span_tp[asp]
        fp = asp_span_fp[asp]
        fn = asp_span_fn[asp]
        result[asp] = 2 * t / (2 * t + fp + fn + 1e-9)
    return result
