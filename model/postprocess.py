"""Light inference post-processing driven by model probabilities only."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import torch

SENTIMENT_LABELS = ["Negative", "Positive", "Neutral"]
_LOG3 = math.log(3)


@dataclass(frozen=True)
class PostprocessConfig:
    enabled: bool = True
    min_aspect_confidence: float = 0.32
    span_iou_dedupe: float = 0.55
    global_blend_alpha: float = 0.45
    entropy_neutral_threshold: float = 0.94
    mixed_aspect_alpha: float = 0.30

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> PostprocessConfig:
        if not raw:
            return cls()
        return cls(
            enabled=bool(raw.get("enabled", True)),
            min_aspect_confidence=float(raw.get("min_aspect_confidence", 0.32)),
            span_iou_dedupe=float(raw.get("span_iou_dedupe", 0.55)),
            global_blend_alpha=float(raw.get("global_blend_alpha", 0.45)),
            entropy_neutral_threshold=float(raw.get("entropy_neutral_threshold", 0.94)),
            mixed_aspect_alpha=float(raw.get("mixed_aspect_alpha", 0.30)),
        )


def _normalized_entropy(probs: list[float]) -> float:
    ent = 0.0
    for p in probs:
        if p > 1e-12:
            ent -= p * math.log(p)
    return ent / _LOG3


def calibrate_aspect_sentiment(
    probs: torch.Tensor | list[float],
    cfg: PostprocessConfig,
) -> tuple[int, float, list[float]]:
    """Pick sentiment from softmax; fall back to Neutral when uncertain."""
    if isinstance(probs, torch.Tensor):
        vec = probs.detach().float().cpu().tolist()
    else:
        vec = [float(x) for x in probs]
    total = sum(vec)
    if total <= 0:
        return 2, 0.0, [1 / 3, 1 / 3, 1 / 3]
    vec = [v / total for v in vec]

    sent_id = max(range(3), key=lambda i: vec[i])
    confidence = vec[sent_id]
    entropy = _normalized_entropy(vec)

    if confidence < cfg.min_aspect_confidence or entropy >= cfg.entropy_neutral_threshold:
        sent_id = 2
        confidence = vec[2]

    return sent_id, confidence, vec


def span_iou(a_start: int, a_end: int, b_start: int, b_end: int) -> float:
    inter = max(0, min(a_end, b_end) - max(a_start, b_start))
    if inter <= 0:
        return 0.0
    union = (a_end - a_start) + (b_end - b_start) - inter
    return inter / union if union > 0 else 0.0


def dedupe_overlapping_spans(opinions: list[dict[str, Any]], iou_threshold: float) -> list[dict[str, Any]]:
    """Keep higher-confidence span when character spans overlap heavily."""
    if len(opinions) <= 1:
        return opinions

    ranked = sorted(opinions, key=lambda o: o.get("confidence", 0.0), reverse=True)
    kept: list[dict[str, Any]] = []
    for cand in ranked:
        cs, ce = int(cand["start"]), int(cand["end"])
        if any(
            span_iou(cs, ce, int(k["start"]), int(k["end"])) >= iou_threshold
            for k in kept
        ):
            continue
        kept.append(cand)

    kept.sort(key=lambda o: o["start"])
    return kept


def reconcile_global_sentiment(
    glob_probs: torch.Tensor | list[float],
    opinions: list[dict[str, Any]],
    cfg: PostprocessConfig,
) -> tuple[int, float]:
    """Blend global head with confidence-weighted aspect distribution."""
    if isinstance(glob_probs, torch.Tensor):
        g = glob_probs.detach().float().cpu().tolist()
    else:
        g = [float(x) for x in glob_probs]
    g_total = sum(g)
    g = [x / g_total for x in g] if g_total > 0 else [1 / 3, 1 / 3, 1 / 3]

    if not opinions:
        sent_id = max(range(3), key=lambda i: g[i])
        return sent_id, g[sent_id]

    agg = [0.0, 0.0, 0.0]
    weight_sum = 0.0
    for op in opinions:
        probs = op.get("_probs") or [0.0, 0.0, 1.0]
        w = max(float(op.get("confidence", 0.0)), 0.08)
        for i in range(3):
            agg[i] += w * probs[i]
        weight_sum += w
    if weight_sum > 0:
        agg = [x / weight_sum for x in agg]

    labels = {int(op.get("_sent_id", 2)) for op in opinions}
    alpha = cfg.global_blend_alpha
    if len(opinions) >= 2 and len(labels) >= 2:
        alpha = cfg.mixed_aspect_alpha

    blended = [alpha * g[i] + (1.0 - alpha) * agg[i] for i in range(3)]
    b_total = sum(blended)
    blended = [x / b_total for x in blended] if b_total > 0 else [1 / 3, 1 / 3, 1 / 3]

    sent_id = max(range(3), key=lambda i: blended[i])
    return sent_id, blended[sent_id]


def postprocess_predictions(
    opinions: list[dict[str, Any]],
    glob_probs: torch.Tensor,
    cfg: PostprocessConfig | None = None,
) -> tuple[list[dict[str, Any]], int, float]:
    """
    Refine raw opinions and global sentiment using model scores only.
    Strips internal `_probs` / `_sent_id` before returning.
    """
    cfg = cfg or PostprocessConfig()
    if not cfg.enabled:
        public = [_public_opinion(o) for o in opinions]
        g = glob_probs.detach().float().cpu().tolist()
        g_total = sum(g)
        g = [x / g_total for x in g] if g_total > 0 else [1 / 3, 1 / 3, 1 / 3]
        gid = max(range(3), key=lambda i: g[i])
        return public, gid, g[gid]

    refined: list[dict[str, Any]] = []
    for op in opinions:
        probs = op.get("_probs")
        if probs is None:
            continue
        sent_id, conf, vec = calibrate_aspect_sentiment(probs, cfg)
        if conf < cfg.min_aspect_confidence:
            continue
        refined.append({
            **op,
            "_sent_id": sent_id,
            "_probs": vec,
            "sentiment": SENTIMENT_LABELS[sent_id],
            "confidence": round(conf, 4),
        })

    refined = dedupe_overlapping_spans(refined, cfg.span_iou_dedupe)
    glob_id, glob_conf = reconcile_global_sentiment(glob_probs, refined, cfg)

    public = [_public_opinion(o) for o in refined]
    return public, glob_id, glob_conf


def _public_opinion(op: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in op.items() if not k.startswith("_")}
