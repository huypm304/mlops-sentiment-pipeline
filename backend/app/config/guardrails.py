"""Inference guardrail thresholds — tuned for early-stage / demo models.

Softmax confidence from ABSA heads is often modest even when predictions are
usable. Keep PASS as the default; reserve REVIEW/REJECT for clearly risky cases.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

GuardrailStatus = Literal["PASS", "WARN", "REVIEW", "REJECT"]


@dataclass(frozen=True)
class GuardrailConfig:
    reject_global: float = 0.18
    review_global: float = 0.25
    warn_global: float = 0.32
    aspect_low: float = 0.22
    aspect_warn_count: int = 2
    aspect_review_count: int = 3
    no_opinion_reject: float = 0.22
    no_opinion_review: float = 0.30
    low_confidence_analytics: float = 0.32

    def as_dict(self) -> dict[str, float | int]:
        return {
            "reject_global": self.reject_global,
            "review_global": self.review_global,
            "warn_global": self.warn_global,
            "aspect_low": self.aspect_low,
            "aspect_warn_count": self.aspect_warn_count,
            "aspect_review_count": self.aspect_review_count,
            "no_opinion_reject": self.no_opinion_reject,
            "no_opinion_review": self.no_opinion_review,
            "low_confidence_analytics": self.low_confidence_analytics,
        }


DEFAULT_GUARDRAIL_CONFIG = GuardrailConfig()


def _pct(value: float) -> str:
    return f"{value * 100:.0f}%"


def evaluate_guardrail(
    *,
    global_confidence: float,
    aspects: list[str] | None = None,
    aspect_confidences: dict[str, float] | None = None,
    cfg: GuardrailConfig | None = None,
) -> tuple[GuardrailStatus, list[str]]:
    cfg = cfg or DEFAULT_GUARDRAIL_CONFIG
    c = float(global_confidence)
    aspect_list = aspects or []
    conf_map = aspect_confidences or {}

    low_aspects = [
        a
        for a in aspect_list
        if float(conf_map.get(a, c)) < cfg.aspect_low
    ]

    status: GuardrailStatus = "PASS"
    reasons: list[str] = []

    if c < cfg.reject_global or (not aspect_list and c < cfg.no_opinion_reject):
        status = "REJECT"
        if c < cfg.reject_global:
            reasons.append(
                f"Global confidence below {_pct(cfg.reject_global)} — prediction unreliable"
            )
        if not aspect_list:
            reasons.append("No aspect opinions extracted (no-opinion output)")
            if c < cfg.no_opinion_reject:
                reasons.append(
                    f"No-opinion output with global confidence below {_pct(cfg.no_opinion_reject)}"
                )
    elif (
        c < cfg.review_global
        or (not aspect_list and c < cfg.no_opinion_review)
        or len(low_aspects) >= cfg.aspect_review_count
    ):
        status = "REVIEW"
        if c < cfg.review_global:
            reasons.append(
                f"Global confidence below {_pct(cfg.review_global)} — recommend human review"
            )
        if not aspect_list:
            reasons.append("No aspect opinions extracted (no-opinion output)")
        if len(low_aspects) >= cfg.aspect_review_count:
            reasons.append(
                f"{len(low_aspects)} aspect(s) below {_pct(cfg.aspect_low)} confidence: "
                f"{', '.join(low_aspects)}"
            )
    elif c < cfg.warn_global or len(low_aspects) >= cfg.aspect_warn_count:
        status = "WARN"
        if c < cfg.warn_global:
            reasons.append(
                f"Global confidence below {_pct(cfg.warn_global)} — soft low-confidence flag"
            )
        if len(low_aspects) >= cfg.aspect_warn_count:
            reasons.append(
                f"{len(low_aspects)} aspect(s) below {_pct(cfg.aspect_low)} confidence: "
                f"{', '.join(low_aspects)}"
            )
    elif not aspect_list:
        reasons.append("No aspect opinions extracted (informational only)")

    if status == "PASS" and not reasons:
        reasons.append("Prediction meets confidence thresholds")

    return status, reasons


def evaluate_guardrail_from_log_entry(
    entry: dict[str, Any],
    cfg: GuardrailConfig | None = None,
) -> tuple[GuardrailStatus, list[str]]:
    return evaluate_guardrail(
        global_confidence=float(entry.get("global_confidence", 0)),
        aspects=entry.get("aspects") or [],
        aspect_confidences=entry.get("aspect_confidences") or {},
        cfg=cfg,
    )
