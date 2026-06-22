"""evaluate() and reporting helpers — extracted verbatim from train/train.py.

The evaluate() function body is identical to the original.
Additional wrappers (format_eval_metrics, print_eval_metrics_line,
save_eval_report) are new but do not touch model/metric logic.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import torch
from sklearn.metrics import f1_score, precision_recall_fscore_support

from .dataset import build_predicted_span_inputs, extract_spans
from .labels import ASPECTS, BIO_LABELS, N_BIO
from .metrics import confusion_payload, label_names_for_sentiment
from .utils import autocast_context, ensure_dir


# ---------------------------------------------------------------------------
# evaluate() — verbatim from train/train.py lines 820–1157
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# New wrappers for scripts
# ---------------------------------------------------------------------------

def format_eval_metrics(m: dict) -> dict:
    """Flatten eval dict for CSV/JSON reports."""
    flat = {
        "tas_strict_p":       round(m["tas_strict"]["precision"], 4),
        "tas_strict_r":       round(m["tas_strict"]["recall"], 4),
        "tas_strict_f1":      round(m["tas_strict"]["f1"], 4),
        "tas_relaxed_p":      round(m["tas_relaxed"]["precision"], 4),
        "tas_relaxed_r":      round(m["tas_relaxed"]["recall"], 4),
        "tas_relaxed_f1":     round(m["tas_relaxed"]["f1"], 4),
        "span_p":             round(m["span"]["precision"], 4),
        "span_r":             round(m["span"]["recall"], 4),
        "span_f1":            round(m["span"]["f1"], 4),
        "sent_matched_p":     round(m["sent_matched"]["precision"], 4),
        "sent_matched_r":     round(m["sent_matched"]["recall"], 4),
        "sent_matched_f1":    round(m["sent_matched"]["f1"], 4),
        "sent_goldspan_p":    round(m["sent_goldspan"]["precision"], 4),
        "sent_goldspan_r":    round(m["sent_goldspan"]["recall"], 4),
        "sent_goldspan_f1":   round(m["sent_goldspan"]["f1"], 4),
        "global_p":           round(m["global"]["precision"], 4),
        "global_r":           round(m["global"]["recall"], 4),
        "global_f1":          round(m["global"]["f1"], 4),
    }
    for asp in ASPECTS:
        flat[f"span_f1_{asp}"] = round(float(m["asp_span_f1"].get(asp, 0.0)), 4)
    for asp in ASPECTS:
        flat[f"sent_f1_{asp}"] = round(float(m["asp_sent_f1"].get(asp, 0.0)), 4)
    return flat


def print_eval_metrics_line(m: dict, prefix: str = "") -> None:
    """Print a single-line summary matching the train loop format."""
    print(
        f"{prefix}"
        f"TAS-Strict={m['tas_strict']['f1']:.4f} | "
        f"TAS-Relaxed={m['tas_relaxed']['f1']:.4f} | "
        f"Span={m['span']['f1']:.4f} | "
        f"Sent@Matched={m['sent_matched']['f1']:.4f} | "
        f"Sent@GoldSpan={m['sent_goldspan']['f1']:.4f} | "
        f"Global={m['global']['f1']:.4f}"
    )
    print("  Aspect sent F1:", {a: f"{v:.3f}" for a, v in m["asp_sent_f1"].items()})
    print("  Aspect span F1:", {a: f"{v:.3f}" for a, v in m["asp_span_f1"].items()})


def save_eval_report(m: dict, output_dir: str | Path) -> None:
    """Save eval_report.json, per_aspect_report.csv, per_class_report.csv."""
    out = ensure_dir(output_dir)

    # Full JSON report
    with open(out / "eval_report.json", "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)

    # Per-aspect CSV
    with open(out / "per_aspect_report.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["aspect", "span_f1", "sent_f1", "support"])
        for asp in ASPECTS:
            w.writerow([
                asp,
                round(float(m["asp_span_f1"].get(asp, 0.0)), 4),
                round(float(m["asp_sent_f1"].get(asp, 0.0)), 4),
                m["asp_support"].get(asp, 0),
            ])

    # Per-class CSV
    cm = m.get("class_metrics", {})
    sent_cm = cm.get("sentiment", {})
    glob_cm = cm.get("global", {})
    with open(out / "per_class_report.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["task", "class", "precision", "recall", "f1", "support"])
        for cls in ["NEG", "POS", "NEU"]:
            row = sent_cm.get(cls, {})
            w.writerow(["sentiment", cls, row.get("precision", 0.0), row.get("recall", 0.0), row.get("f1", 0.0), row.get("support", 0)])
        for cls in ["NEG", "POS", "NEU"]:
            row = glob_cm.get(cls, {})
            w.writerow(["global", cls, row.get("precision", 0.0), row.get("recall", 0.0), row.get("f1", 0.0), row.get("support", 0)])

    # Confusion matrices JSON
    with open(out / "confusion_matrix.json", "w", encoding="utf-8") as f:
        json.dump(m.get("confusion_matrices", {}), f, ensure_ascii=False, indent=2)
