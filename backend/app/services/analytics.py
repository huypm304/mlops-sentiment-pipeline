"""Analytics and review queue derived from inference log + drift."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any

from backend.app.config.guardrails import (
    DEFAULT_GUARDRAIL_CONFIG,
    evaluate_guardrail_from_log_entry,
)
from backend.app.services import drift as drift_service

LOW_CONFIDENCE_THRESHOLD = DEFAULT_GUARDRAIL_CONFIG.low_confidence_analytics

ASPECT_ORDER = drift_service.ASPECT_ORDER


def _parse_ts(ts: str) -> datetime | None:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _guardrail(entry: dict[str, Any]) -> tuple[str, list[str]]:
    status, reasons = evaluate_guardrail_from_log_entry(entry)
    return status, reasons


def _filtered_entries(
    *,
    hours: int | None = None,
    model_version: str | None = None,
) -> list[dict[str, Any]]:
    entries = drift_service.get_inference_entries()
    if hours is not None:
        cutoff = datetime.now(timezone.utc).timestamp() - hours * 3600
        filtered: list[dict[str, Any]] = []
        for e in entries:
            ts = _parse_ts(str(e.get("ts", "")))
            if ts and ts.timestamp() >= cutoff:
                filtered.append(e)
        entries = filtered
    if model_version:
        entries = [e for e in entries if e.get("model_version", "absa-v1") == model_version]
    return entries


def get_analytics(*, hours: int = 24, model_version: str | None = None) -> dict[str, Any]:
    from backend.app.services import registry_db

    store = registry_db.get_store()
    if store is not None and store.config.predictions_table:
        predictions = store.list_predictions(limit=200, model_version=model_version)
        entries = []
        cutoff = None
        if hours is not None:
            cutoff = datetime.now(timezone.utc).timestamp() - hours * 3600
        for row in predictions:
            ts = _parse_ts(str(row.get("created_at", "")))
            if cutoff is not None and ts and ts.timestamp() < cutoff:
                continue
            entries.append(
                {
                    "ts": row.get("created_at", ""),
                    "text_preview": row.get("text_preview", ""),
                    "global_sentiment": row.get("global_sentiment", "neutral"),
                    "global_confidence": float(row.get("confidence", 0)),
                    "aspects": row.get("aspects") or [],
                    "model_version": row.get("model_version", "absa-v1"),
                }
            )
    else:
        entries = _filtered_entries(hours=hours, model_version=model_version)

    drift = drift_service.get_drift_report()

    total = len(entries)
    low_conf = sum(1 for e in entries if float(e.get("global_confidence", 0)) < LOW_CONFIDENCE_THRESHOLD)
    no_opinion = sum(1 for e in entries if not e.get("aspects"))
    review_items = [e for e in entries if _guardrail(e)[0] in ("REVIEW", "REJECT")]
    flagged_items = [e for e in entries if _guardrail(e)[0] != "PASS"]

    aspect_counts: Counter[str] = Counter()
    conf_bins = [0] * 10
    sentiment_buckets: dict[str, Counter[str]] = {}

    for e in entries:
        for asp in e.get("aspects") or []:
            aspect_counts[str(asp)] += 1
        conf = float(e.get("global_confidence", 0))
        bin_idx = min(9, int(conf * 10))
        conf_bins[bin_idx] += 1

        ts = _parse_ts(str(e.get("ts", "")))
        bucket = ts.strftime("%H:00") if ts else "—"
        if bucket not in sentiment_buckets:
            sentiment_buckets[bucket] = Counter()
        sentiment_buckets[bucket][str(e.get("global_sentiment", "neutral"))] += 1

    sentiment_trend = []
    for bucket in sorted(sentiment_buckets.keys()):
        c = sentiment_buckets[bucket]
        sentiment_trend.append({
            "time": bucket,
            "positive": c.get("positive", 0),
            "neutral": c.get("neutral", 0),
            "negative": c.get("negative", 0),
        })

    aspect_distribution = [
        {"aspect": asp, "count": aspect_counts.get(asp, 0)} for asp in ASPECT_ORDER if aspect_counts.get(asp, 0)
    ]
    aspect_distribution.sort(key=lambda x: x["count"], reverse=True)

    confidence_histogram = [
        {"bin": f"{i * 10}–{(i + 1) * 10}%", "count": conf_bins[i]} for i in range(10)
    ]

    drift_trend = [{"day": "current", "score": drift.get("drift_score", 0.0)}]
    if drift.get("status") != "insufficient_data":
        drift_trend = [{"day": "now", "score": drift.get("drift_score", 0.0)}]

    recent = []
    for e in reversed(entries[-20:]):
        guardrail, _ = _guardrail(e)
        ts = _parse_ts(str(e.get("ts", "")))
        recent.append({
            "time": ts.strftime("%H:%M:%S") if ts else "—",
            "text": e.get("text_preview") or "—",
            "aspects": e.get("aspects") or [],
            "sentiment": e.get("global_sentiment", "neutral"),
            "confidence": float(e.get("global_confidence", 0)),
            "guardrail": guardrail,
            "model_version": e.get("model_version", "absa-v1"),
        })

    models = sorted({str(e.get("model_version", "absa-v1")) for e in drift_service.get_inference_entries()})

    return {
        "summary": {
            "predictions": total,
            "low_confidence_rate": round(low_conf / total * 100, 1) if total else 0.0,
            "low_confidence_threshold_pct": round(LOW_CONFIDENCE_THRESHOLD * 100, 1),
            "no_opinion_rate": round(no_opinion / total * 100, 1) if total else 0.0,
            "review_queue": len(review_items),
            "review_queue_pending": len(flagged_items),
            "review_queue_urgent": len(review_items),
        },
        "sentiment_trend": sentiment_trend,
        "aspect_distribution": aspect_distribution,
        "confidence_histogram": confidence_histogram,
        "drift_trend": drift_trend,
        "drift": {
            "score": drift.get("drift_score", 0.0),
            "threshold": drift.get("threshold", 0.18),
            "status": drift.get("status", "insufficient_data"),
        },
        "recent_predictions": recent,
        "models": models or ["absa-v1"],
    }


def get_review_queue(*, limit: int = 50) -> dict[str, Any]:
    from backend.app.services import registry_db

    store = registry_db.get_store()
    if store is not None and store.config.review_queue_table:
        items = store.list_review_queue(limit=limit, status="PENDING")
        rows = [
            {
                "id": row.get("review_id", ""),
                "time": str(row.get("created_at", ""))[:16].replace("T", " "),
                "text": row.get("text_preview") or "—",
                "reason": row.get("guardrail_status", "WARN"),
                "model_version": row.get("model_id", "absa-v1"),
                "confidence": f"{float(row.get('confidence', 0)) * 100:.0f}%",
                "status": "Pending",
                "assigned_to": "—",
                "guardrail": row.get("guardrail_status", "WARN"),
            }
            for row in items
        ]
        return {"items": rows, "open_count": len(rows)}

    entries = drift_service.get_inference_entries()
    rows: list[dict[str, Any]] = []

    for i, e in enumerate(reversed(entries)):
        guardrail, reasons = _guardrail(e)
        if guardrail not in ("REVIEW", "REJECT"):
            continue
        ts = _parse_ts(str(e.get("ts", "")))
        rows.append({
            "id": f"rq-{len(entries) - i:04d}",
            "time": ts.strftime("%Y-%m-%d %H:%M") if ts else "—",
            "text": e.get("text_preview") or "—",
            "reason": reasons[0] if reasons else guardrail,
            "model_version": e.get("model_version", "absa-v1"),
            "confidence": f"{float(e.get('global_confidence', 0)) * 100:.0f}%",
            "status": "Pending",
            "assigned_to": "—",
            "guardrail": guardrail,
        })
        if len(rows) >= limit:
            break

    return {"items": rows, "open_count": len(rows)}
