"""Inference post-processing for ABSA predictions.

Applies confidence filtering, span deduplication, boundary expansion,
need_review logic, and global sentiment reconciliation.
Does NOT affect evaluation metrics (eval runs on raw model outputs).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import Any

from .labels import SENT_ID2LABEL

_LOG3 = math.log(3)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(parsed) or math.isinf(parsed):
        return default
    return parsed


def _max_prob(probs: list[float]) -> float:
    clean = [_safe_float(p) for p in probs]
    return max(clean) if clean else 0.0


def _sanitize_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _sanitize_json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_json_value(item) for item in value]
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return 0.0
    return value

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_BAD_SINGLE_TARGETS = [
    "trả", "dịch", "chất", "giao", "đóng", "thanh", "đường", "khoản",
]

DEFAULT_PHRASE_EXPANSIONS = [
    "chất vải", "chất lượng", "dịch vụ", "trả lời", "giao hàng",
    "đóng gói", "thanh toán", "đường may", "tư vấn", "phản hồi",
]


@dataclass
class PostprocessConfig:
    enabled: bool = True
    sentiment_confidence_threshold: float = 0.55
    global_confidence_threshold: float = 0.55
    min_aspect_confidence: float = 0.45
    entropy_neutral_threshold: float = 0.94
    span_iou_dedupe: float = 0.55
    global_blend_alpha: float = 0.40
    mixed_aspect_alpha: float = 0.25
    bad_single_targets: list[str] = field(default_factory=lambda: list(DEFAULT_BAD_SINGLE_TARGETS))
    phrase_expansions: list[str] = field(default_factory=lambda: list(DEFAULT_PHRASE_EXPANSIONS))

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> "PostprocessConfig":
        if not raw:
            return cls()
        return cls(
            enabled=bool(raw.get("enabled", True)),
            sentiment_confidence_threshold=float(raw.get("sentiment_confidence_threshold", 0.55)),
            global_confidence_threshold=float(raw.get("global_confidence_threshold", 0.55)),
            min_aspect_confidence=float(raw.get("min_aspect_confidence", 0.45)),
            entropy_neutral_threshold=float(raw.get("entropy_neutral_threshold", 0.94)),
            span_iou_dedupe=float(raw.get("span_iou_dedupe", 0.55)),
            global_blend_alpha=float(raw.get("global_blend_alpha", 0.40)),
            mixed_aspect_alpha=float(raw.get("mixed_aspect_alpha", 0.25)),
            bad_single_targets=list(raw.get("bad_single_targets", DEFAULT_BAD_SINGLE_TARGETS)),
            phrase_expansions=list(raw.get("phrase_expansions", DEFAULT_PHRASE_EXPANSIONS)),
        )

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalized_entropy(probs: list[float]) -> float:
    ent = 0.0
    for p in probs:
        if p > 1e-12:
            ent -= p * math.log(p)
    return ent / _LOG3


def _span_iou(a_start: int, a_end: int, b_start: int, b_end: int) -> float:
    inter = max(0, min(a_end, b_end) - max(a_start, b_start))
    if inter <= 0:
        return 0.0
    union = (a_end - a_start) + (b_end - b_start) - inter
    return inter / union if union > 0 else 0.0


def _is_bad_target(target: str, bad_singles: list[str]) -> bool:
    stripped = target.strip().lower()
    return stripped in [t.lower() for t in bad_singles]


def _try_expand_target(target: str, text: str, expansions: list[str]) -> str:
    t_lower = target.strip().lower()
    text_lower = text.lower()
    for phrase in expansions:
        if phrase.lower().startswith(t_lower) and phrase.lower() in text_lower:
            return phrase
    return target


# ---------------------------------------------------------------------------
# Core postprocess steps
# ---------------------------------------------------------------------------

def dedupe_overlapping_spans(opinions: list[dict[str, Any]], iou_threshold: float) -> list[dict[str, Any]]:
    if len(opinions) <= 1:
        return opinions
    ranked = sorted(opinions, key=lambda o: o.get("confidence", 0.0), reverse=True)
    kept: list[dict[str, Any]] = []
    for cand in ranked:
        cs, ce = int(cand["start"]), int(cand["end"])
        if any(_span_iou(cs, ce, int(k["start"]), int(k["end"])) >= iou_threshold for k in kept):
            continue
        kept.append(cand)
    kept.sort(key=lambda o: o["start"])
    return kept


def reconcile_global_sentiment(
    glob_probs: list[float],
    opinions: list[dict[str, Any]],
    cfg: PostprocessConfig,
) -> tuple[int, float]:
    """Blend global head with confidence-weighted aspect distribution."""
    g = list(glob_probs)
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


def _review_reasons(op: dict[str, Any], cfg: PostprocessConfig, text: str = "") -> list[str]:
    reasons = []
    conf = float(op.get("confidence", 0.0))
    probs = op.get("_probs") or [0.0, 0.0, 1.0]
    entropy = _normalized_entropy(probs)

    if conf < cfg.sentiment_confidence_threshold:
        reasons.append(f"low_confidence ({conf:.2f} < {cfg.sentiment_confidence_threshold})")
    if entropy >= cfg.entropy_neutral_threshold:
        reasons.append(f"high_entropy ({entropy:.2f})")
    if _is_bad_target(op.get("target", ""), cfg.bad_single_targets):
        reasons.append("bad_single_target")
    return reasons


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def postprocess_predictions(
    opinions: list[dict[str, Any]],
    glob_probs: list[float],
    text: str = "",
    cfg: PostprocessConfig | None = None,
    model_version: str = "absa-v2b",
) -> dict[str, Any]:
    """
    Refine raw model outputs into API-ready response.

    Each opinion in `opinions` must have:
        target, aspect, start, end, confidence, _probs (list[float] NEG/POS/NEU), _sent_id (int)

    Returns full response dict including need_review, guardrail_status.
    """
    cfg = cfg or PostprocessConfig()

    if not cfg.enabled:
        refined_ops = [_public_opinion(op, cfg, text) for op in opinions]
        g_id = max(range(3), key=lambda i: glob_probs[i]) if glob_probs else 2
        g_conf = glob_probs[g_id] if glob_probs else 0.0
        return _build_response(refined_ops, g_id, g_conf, glob_probs, text, model_version)

    # Step 1: strip bad single-word targets and optionally expand
    refined: list[dict[str, Any]] = []
    for op in opinions:
        probs = op.get("_probs") or [0.0, 0.0, 1.0]
        sent_id = int(op.get("_sent_id", max(range(3), key=lambda i: probs[i])))
        conf = float(probs[sent_id])

        # Keep argmax — do not suppress below min_aspect_confidence here unless very low
        if conf < cfg.min_aspect_confidence:
            continue

        target = op.get("target", "").strip()
        # Attempt phrase expansion for bad single targets
        if _is_bad_target(target, cfg.bad_single_targets) and text:
            expanded = _try_expand_target(target, text, cfg.phrase_expansions)
            target = expanded

        entropy = _normalized_entropy(probs)
        # Use argmax; set need_review flag for uncertain predictions instead of forcing NEU
        final_sent_id = sent_id
        final_conf = conf

        refined.append({
            **op,
            "target": target,
            "_sent_id": final_sent_id,
            "_probs": probs,
            "confidence": round(final_conf, 4),
        })

    # Step 2: dedup overlapping spans
    refined = dedupe_overlapping_spans(refined, cfg.span_iou_dedupe)

    # Step 3: reconcile global
    glob_id, glob_conf = reconcile_global_sentiment(glob_probs, refined, cfg)

    return _build_response(
        [_public_opinion(op, cfg, text) for op in refined],
        glob_id,
        glob_conf,
        glob_probs,
        text,
        model_version,
    )


def _public_opinion(op: dict[str, Any], cfg: PostprocessConfig, text: str) -> dict[str, Any]:
    probs = op.get("_probs") or [0.0, 0.0, 1.0]
    sent_id = int(op.get("_sent_id", max(range(3), key=lambda i: probs[i])))
    conf = _safe_float(probs[sent_id])
    raw_conf = _safe_float(op.get("raw_confidence", op.get("confidence", conf)))
    reasons = _review_reasons(op, cfg, text)
    return {
        "target": op.get("target", ""),
        "aspect": op.get("aspect", ""),
        "sentiment": SENT_ID2LABEL[sent_id],
        "sentiment_id": sent_id,
        "confidence": round(conf, 4),
        "raw_confidence": round(raw_conf, 4),
        "calibrated_confidence": round(conf, 4),
        "start": op.get("start"),
        "end": op.get("end"),
        "probs": {
            "NEG": round(float(probs[0]), 4),
            "POS": round(float(probs[1]), 4),
            "NEU": round(float(probs[2]), 4),
        },
        "need_review": len(reasons) > 0,
        "review_reasons": reasons,
    }


def _build_response(
    public_ops: list[dict],
    glob_id: int,
    glob_conf: float,
    glob_probs: list[float],
    text: str,
    model_version: str,
) -> dict[str, Any]:
    any_need_review = any(op.get("need_review", False) for op in public_ops)
    return {
        "text": text,
        "opinions": public_ops,
        "global_sentiment": SENT_ID2LABEL[glob_id],
        "global_sentiment_id": glob_id,
        "global_confidence": round(_safe_float(glob_conf), 4),
        "global_raw_confidence": round(_max_prob(glob_probs), 4),
        "global_probs": {
            "NEG": round(_safe_float(glob_probs[0] if len(glob_probs) > 0 else 0.0), 4),
            "POS": round(_safe_float(glob_probs[1] if len(glob_probs) > 1 else 0.0), 4),
            "NEU": round(_safe_float(glob_probs[2] if len(glob_probs) > 2 else 0.0), 4),
        },
        "model_version": model_version,
        "need_review": any_need_review,
        "review_reasons": [r for op in public_ops for r in op.get("review_reasons", [])],
        "guardrail_status": "REVIEW" if any_need_review else "PASS",
    }
