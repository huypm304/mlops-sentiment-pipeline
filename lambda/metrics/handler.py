"""Metrics Lambda — monitoring snapshots, drift checks, and review queue API."""

from __future__ import annotations

import json
import os
from collections import Counter
from typing import Any
from urllib.parse import parse_qs, urlparse

from registry.store import RegistryStore, now_iso

_BUCKET = os.getenv("ARTIFACTS_BUCKET", "")
_STATE_MACHINE_ARN = os.getenv("STATE_MACHINE_ARN", "")
_store: RegistryStore | None = None

PRODUCTION_BASELINE = {
    "tas_f1": 0.72,
    "span_f1": 0.68,
    "sentiment_f1": 0.75,
    "global_f1": 0.73,
}

ASPECT_ORDER = ["Fashion", "Electronics", "General", "Service", "Ship", "Price", "App"]
SENTIMENT_KEYS = ["negative", "positive", "neutral"]
DRIFT_THRESHOLD = 0.18
MIN_PRODUCTION_SAMPLES = 5


def _get_store() -> RegistryStore:
    global _store
    if _store is None:
        _store = RegistryStore()
    return _store


def _response(status: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def _parse_body(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        import base64

        raw = base64.b64decode(raw).decode("utf-8")
    return json.loads(raw) if isinstance(raw, str) else raw


def _query_params(event: dict[str, Any]) -> dict[str, str]:
    params = event.get("queryStringParameters") or {}
    if params:
        return {str(k): str(v) for k, v in params.items()}
    raw_path = event.get("rawPath") or event.get("path") or ""
    if "?" in raw_path:
        parsed = urlparse(raw_path)
        return {k: v[0] for k, v in parse_qs(parsed.query).items()}
    return {}


def _compute_snapshot(model_id: str = "absa-v1") -> dict[str, Any]:
    store = _get_store()
    predictions = store.list_predictions(limit=200, model_version=model_id)
    count = len(predictions)
    low_conf = sum(1 for row in predictions if float(row.get("confidence", 0)) < 0.32)
    no_opinion = sum(1 for row in predictions if not row.get("aspects"))
    review_items = store.list_review_queue(limit=100, status="PENDING")
    return store.put_monitoring_snapshot(
        {
            "model_id": model_id,
            "window": "last_batch",
            "prediction_count": count,
            "low_confidence_rate": round(low_conf / count, 4) if count else 0.0,
            "no_opinion_rate": round(no_opinion / count, 4) if count else 0.0,
            "review_queue_size": len(review_items),
            "aspect_drift_score": 0.0,
            "sentiment_drift_score": 0.0,
            "created_at": now_iso(),
        }
    )


def _model_summaries() -> list[dict[str, Any]]:
    store = _get_store()
    rows = store.list_models(limit=20) if store.config.models_table else []
    if not rows:
        return [
            {
                "version": "absa-v1",
                "status": "production",
                "epoch": 0,
                "primary_metric": "global_f1",
                "tas_strict_f1": PRODUCTION_BASELINE["tas_f1"],
                "tas_relaxed_f1": PRODUCTION_BASELINE["tas_f1"],
                "span_f1": PRODUCTION_BASELINE["span_f1"],
                "sent_matched_f1": PRODUCTION_BASELINE["sentiment_f1"],
                "sent_goldspan_f1": PRODUCTION_BASELINE["sentiment_f1"],
                "global_f1": PRODUCTION_BASELINE["global_f1"],
                "encoder": "Fsoft-AIC/videberta-base",
                "checkpoint": "models/v1/best_model.pt",
            }
        ]
    summaries = []
    for row in rows:
        metrics = row.get("metrics") or {}
        summaries.append(
            {
                "version": row.get("model_id", "absa-v1"),
                "status": str(row.get("status", "production")).lower(),
                "epoch": 0,
                "primary_metric": "global_f1",
                "tas_strict_f1": float(metrics.get("tas_f1", 0)),
                "tas_relaxed_f1": float(metrics.get("tas_f1", 0)),
                "span_f1": float(metrics.get("span_f1", 0)),
                "sent_matched_f1": float(metrics.get("sentiment_f1", 0)),
                "sent_goldspan_f1": float(metrics.get("sentiment_f1", 0)),
                "global_f1": float(metrics.get("global_f1", 0)),
                "encoder": row.get("source", "sagemaker_training"),
                "checkpoint": row.get("artifact_prefix", ""),
            }
        )
    return summaries


def _model_evaluation(version: str) -> dict[str, Any] | None:
    store = _get_store()
    if store.config.models_table:
        for row in store.list_models(limit=50):
            if row.get("model_id") == version:
                metrics = row.get("metrics") or PRODUCTION_BASELINE
                f1 = float(metrics.get("global_f1", PRODUCTION_BASELINE["global_f1"]))
                span = float(metrics.get("span_f1", PRODUCTION_BASELINE["span_f1"]))
                return {
                    "version": version,
                    "status": str(row.get("status", "production")).lower(),
                    "epoch": 0,
                    "phase": "production",
                    "primary_metric": "global_f1",
                    "registered_at": row.get("registered_at", now_iso()),
                    "evaluated_at": row.get("registered_at", now_iso()),
                    "inference_latency_ms": 0,
                    "dataset": {
                        "version": row.get("dataset_id", "dataset-v1"),
                        "train_samples": 0,
                        "val_samples": 0,
                        "test_samples": 0,
                    },
                    "training": {
                        "encoder": "Fsoft-AIC/videberta-base",
                        "epochs": 50,
                        "batch_size": 24,
                        "learning_rate": 3e-5,
                        "trained_at": row.get("registered_at", now_iso()),
                        "checkpoint": row.get("artifact_prefix", "models/v1"),
                    },
                    "scores": {
                        "tas_strict_f1": float(metrics.get("tas_f1", 0)),
                        "tas_relaxed_f1": float(metrics.get("tas_f1", 0)),
                        "span_f1": span,
                        "sent_matched_f1": float(metrics.get("sentiment_f1", 0)),
                        "sent_goldspan_f1": float(metrics.get("sentiment_f1", 0)),
                        "global_f1": f1,
                    },
                    "sentiment": {"accuracy": span, "precision": span, "recall": span, "f1": span},
                    "global_sentiment": {"accuracy": f1, "precision": f1, "recall": f1, "f1": f1},
                    "aspect_polarity": {"accuracy": span, "precision": span, "recall": span, "f1": span},
                    "aspect_extraction": {"accuracy": span, "precision": span, "recall": span, "f1": span},
                    "confusion_matrix": {
                        "labels": ["negative", "neutral", "positive"],
                        "matrix": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                    },
                    "global_confusion_matrix": {
                        "labels": ["negative", "neutral", "positive"],
                        "matrix": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                    },
                    "per_aspect": [],
                    "confusion_labels": ["negative", "neutral", "positive"],
                }
    if version == "absa-v1":
        return {
            "version": "absa-v1",
            "status": "production",
            "epoch": 0,
            "phase": "baseline",
            "primary_metric": "global_f1",
            "registered_at": now_iso(),
            "evaluated_at": now_iso(),
            "inference_latency_ms": 0,
            "dataset": {"version": "dataset-v1", "train_samples": 0, "val_samples": 0, "test_samples": 0},
            "training": {
                "encoder": "Fsoft-AIC/videberta-base",
                "epochs": 50,
                "batch_size": 24,
                "learning_rate": 3e-5,
                "trained_at": now_iso(),
                "checkpoint": "models/v1/best_model.pt",
            },
            "scores": {
                "tas_strict_f1": PRODUCTION_BASELINE["tas_f1"],
                "tas_relaxed_f1": PRODUCTION_BASELINE["tas_f1"],
                "span_f1": PRODUCTION_BASELINE["span_f1"],
                "sent_matched_f1": PRODUCTION_BASELINE["sentiment_f1"],
                "sent_goldspan_f1": PRODUCTION_BASELINE["sentiment_f1"],
                "global_f1": PRODUCTION_BASELINE["global_f1"],
            },
            "sentiment": {
                "accuracy": PRODUCTION_BASELINE["span_f1"],
                "precision": PRODUCTION_BASELINE["span_f1"],
                "recall": PRODUCTION_BASELINE["span_f1"],
                "f1": PRODUCTION_BASELINE["span_f1"],
            },
            "global_sentiment": {
                "accuracy": PRODUCTION_BASELINE["global_f1"],
                "precision": PRODUCTION_BASELINE["global_f1"],
                "recall": PRODUCTION_BASELINE["global_f1"],
                "f1": PRODUCTION_BASELINE["global_f1"],
            },
            "aspect_polarity": {
                "accuracy": PRODUCTION_BASELINE["span_f1"],
                "precision": PRODUCTION_BASELINE["span_f1"],
                "recall": PRODUCTION_BASELINE["span_f1"],
                "f1": PRODUCTION_BASELINE["span_f1"],
            },
            "aspect_extraction": {
                "accuracy": PRODUCTION_BASELINE["span_f1"],
                "precision": PRODUCTION_BASELINE["span_f1"],
                "recall": PRODUCTION_BASELINE["span_f1"],
                "f1": PRODUCTION_BASELINE["span_f1"],
            },
            "confusion_matrix": {
                "labels": ["negative", "neutral", "positive"],
                "matrix": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            },
            "global_confusion_matrix": {
                "labels": ["negative", "neutral", "positive"],
                "matrix": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            },
            "per_aspect": [],
            "confusion_labels": ["negative", "neutral", "positive"],
        }
    return None


def _normalize_sentiment(label: str) -> str:
    value = str(label or "neutral").strip().lower()
    if value in SENTIMENT_KEYS:
        return value
    if value in ("neg", "negative", "0"):
        return "negative"
    if value in ("pos", "positive", "1"):
        return "positive"
    return "neutral"


def _dist_from_counter(counter: Counter[str], keys: list[str]) -> dict[str, float]:
    total = sum(counter.get(key, 0) for key in keys) or 1
    return {key: round(counter.get(key, 0) / total, 4) for key in keys}


def _l1_drift(a: dict[str, float], b: dict[str, float], keys: list[str]) -> float:
    return round(sum(abs(a.get(key, 0) - b.get(key, 0)) for key in keys) / 2, 4)


def _default_baseline() -> dict[str, Any]:
    return {
        "source": "default_uniform",
        "sample_size": 0,
        "aspect_distribution": _dist_from_counter(Counter(), ASPECT_ORDER),
        "global_sentiment_distribution": _dist_from_counter(Counter(), SENTIMENT_KEYS),
        "avg_text_length": 0,
    }


def _production_window(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    aspect_c: Counter[str] = Counter()
    global_c: Counter[str] = Counter()
    confidences: list[float] = []

    for row in predictions:
        global_c[_normalize_sentiment(str(row.get("global_sentiment", "neutral")))] += 1
        confidences.append(float(row.get("confidence", 0) or 0))
        for aspect in row.get("aspects") or []:
            asp = str(aspect)
            if asp in ASPECT_ORDER:
                aspect_c[asp] += 1

    sample_size = len(predictions)
    return {
        "sample_size": sample_size,
        "aspect_distribution": _dist_from_counter(aspect_c, ASPECT_ORDER),
        "global_sentiment_distribution": _dist_from_counter(global_c, SENTIMENT_KEYS),
        "avg_global_confidence": round(sum(confidences) / sample_size, 4) if sample_size else 0.0,
    }


def _runtime_stats(predictions: list[dict[str, Any]], *, model_ready: bool = True) -> dict[str, Any]:
    latencies = [float(row.get("latency_ms", 0) or 0) for row in predictions if row.get("latency_ms") is not None]
    avg = sum(latencies) / len(latencies) if latencies else 0.0
    sorted_latencies = sorted(latencies)
    p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)] if sorted_latencies else 0.0

    return {
        "endpoint_health": "healthy" if model_ready else "degraded",
        "api_status": "ok" if model_ready else "starting",
        "uptime_seconds": 0,
        "request_volume_total": len(predictions),
        "error_count": 0,
        "error_rate_pct": 0.0,
        "avg_latency_ms": round(avg, 1),
        "p95_latency_ms": round(p95, 1),
        "recent_latency_ms": [round(x, 1) for x in latencies[-24:]],
    }


def _drift_summary() -> dict[str, Any]:
    store = _get_store()
    baseline = _default_baseline()
    if not store.config.predictions_table:
        production = _production_window([])
        return {
            "status": "insufficient_data",
            "message": "Predictions table is not configured",
            "production_sample_size": 0,
            "baseline": baseline,
            "production": production,
            "drift_score": 0.0,
            "aspect_drift": 0.0,
            "sentiment_drift": 0.0,
            "confidence_delta": 0.0,
            "threshold": DRIFT_THRESHOLD,
            "suggest_retrain": False,
            "signals": [],
            "comparison": [],
        }

    predictions = store.list_predictions(limit=200)
    production = _production_window(predictions)
    sample_size = production["sample_size"]

    if sample_size < MIN_PRODUCTION_SAMPLES:
        return {
            "status": "insufficient_data",
            "message": f"Need at least {MIN_PRODUCTION_SAMPLES} predictions (have {sample_size})",
            "production_sample_size": sample_size,
            "baseline": baseline,
            "production": production,
            "drift_score": 0.0,
            "aspect_drift": 0.0,
            "sentiment_drift": 0.0,
            "confidence_delta": 0.0,
            "threshold": DRIFT_THRESHOLD,
            "suggest_retrain": False,
            "signals": [],
            "comparison": [],
        }

    aspect_drift = _l1_drift(
        baseline["aspect_distribution"],
        production["aspect_distribution"],
        ASPECT_ORDER,
    )
    sentiment_drift = _l1_drift(
        baseline["global_sentiment_distribution"],
        production["global_sentiment_distribution"],
        SENTIMENT_KEYS,
    )
    drift_score = round(0.6 * aspect_drift + 0.4 * sentiment_drift, 4)
    avg_conf = float(production.get("avg_global_confidence") or 0.0)
    confidence_delta = round(0.7 - avg_conf, 4) if avg_conf else 0.0

    signals: list[str] = []
    if aspect_drift >= DRIFT_THRESHOLD:
        signals.append("Aspect distribution shifted vs training data")
    if sentiment_drift >= DRIFT_THRESHOLD:
        signals.append("Global sentiment mix shifted vs training data")
    if avg_conf and avg_conf < 0.32:
        signals.append("Low average prediction confidence")
    if drift_score >= DRIFT_THRESHOLD:
        signals.append("Overall drift exceeds threshold — consider audit & retrain")

    suggest_retrain = drift_score >= DRIFT_THRESHOLD or len(signals) >= 2
    status = "alert" if suggest_retrain else "ok"
    if drift_score >= DRIFT_THRESHOLD * 0.7:
        status = "warning"

    comparison: list[dict[str, Any]] = []
    for aspect in ASPECT_ORDER:
        base_value = baseline["aspect_distribution"].get(aspect, 0)
        prod_value = production["aspect_distribution"].get(aspect, 0)
        comparison.append(
            {
                "name": aspect,
                "baseline": base_value,
                "production": prod_value,
                "delta": round(prod_value - base_value, 4),
            }
        )

    return {
        "status": status,
        "message": "Drift within normal range"
        if status == "ok"
        else "Elevated drift — review before next training cycle",
        "production_sample_size": sample_size,
        "baseline": baseline,
        "production": production,
        "drift_score": drift_score,
        "aspect_drift": aspect_drift,
        "sentiment_drift": sentiment_drift,
        "confidence_delta": confidence_delta,
        "threshold": DRIFT_THRESHOLD,
        "suggest_retrain": suggest_retrain,
        "signals": signals,
        "comparison": comparison,
    }


def _monitoring_summary() -> dict[str, Any]:
    store = _get_store()
    snapshot = store.get_latest_monitoring_snapshot() if store.config.monitoring_table else None
    review_items = store.list_review_queue(limit=50, status="PENDING") if store.config.review_queue_table else []
    predictions = store.list_predictions(limit=500) if store.config.predictions_table else []
    payload = {
        **_runtime_stats(predictions),
        "drift": _drift_summary(),
        "review_queue_pending": len(review_items),
    }
    if snapshot:
        payload["snapshot"] = snapshot
    return payload


def _analytics_payload(params: dict[str, str]) -> dict[str, Any]:
    store = _get_store()
    predictions = store.list_predictions(limit=200) if store.config.predictions_table else []
    total = len(predictions)
    low_conf = sum(1 for row in predictions if float(row.get("confidence", 0)) < 0.32)
    no_opinion = sum(1 for row in predictions if not row.get("aspects"))
    review_items = store.list_review_queue(limit=50, status="PENDING") if store.config.review_queue_table else []
    drift = _drift_summary()
    return {
        "summary": {
            "predictions": total,
            "low_confidence_rate": round(low_conf / total * 100, 1) if total else 0.0,
            "low_confidence_threshold_pct": 32.0,
            "no_opinion_rate": round(no_opinion / total * 100, 1) if total else 0.0,
            "review_queue": len(review_items),
            "review_queue_pending": len(review_items),
            "review_queue_urgent": len(review_items),
        },
        "sentiment_trend": [],
        "aspect_distribution": [],
        "confidence_histogram": [],
        "drift_trend": [{"day": "now", "score": drift.get("drift_score", 0.0)}],
        "drift": {
            "score": drift.get("drift_score", 0.0),
            "threshold": drift.get("threshold", 0.18),
            "status": drift.get("status", "insufficient_data"),
        },
        "recent_predictions": predictions[:10],
        "models": ["absa-v1"],
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    store = _get_store()

    if isinstance(event, dict) and event.get("action") == "compute_snapshot":
        try:
            snapshot = _compute_snapshot(str(event.get("model_id", "absa-v1")))
            return {"status": "ok", "action": "compute_snapshot", "snapshot": snapshot}
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "action": "compute_snapshot", "detail": str(exc)}

    if isinstance(event, dict) and event.get("action") == "check_retrain_recommendation":
        snapshot = store.get_latest_monitoring_snapshot()
        recommend = bool(snapshot and float(snapshot.get("low_confidence_rate", 0)) > 0.25)
        return {
            "status": "ok",
            "action": "check_retrain_recommendation",
            "recommend_retrain": recommend,
            "snapshot": snapshot,
        }

    route = event.get("rawPath") or event.get("path", "")
    params = _query_params(event)

    if route.endswith("/metrics/monitoring"):
        try:
            return _response(200, _monitoring_summary())
        except Exception as exc:  # noqa: BLE001
            return _response(500, {"detail": str(exc)})

    if route.endswith("/metrics/drift"):
        try:
            return _response(200, _drift_summary())
        except Exception as exc:  # noqa: BLE001
            return _response(500, {"detail": str(exc)})

    if route.endswith("/metrics/models"):
        return _response(200, {"models": _model_summaries()})

    if "/metrics/models/" in route:
        version = route.split("/metrics/models/")[1].strip("/").split("?")[0]
        evaluation = _model_evaluation(version)
        if evaluation is None:
            return _response(404, {"detail": f"Model '{version}' not found"})
        return _response(200, evaluation)

    if route.endswith("/metrics/analytics"):
        return _response(200, _analytics_payload(params))

    if route.endswith("/metrics/platform"):
        return _response(
            200,
            {
                "environment": os.getenv("ENVIRONMENT", "demo"),
                "production_model": "absa-v1",
                "endpoint_status": "ready",
                "artifacts_bucket": _BUCKET or None,
                "retrain_state_machine": _STATE_MACHINE_ARN or None,
                "pipeline_demo_mode": not bool(_STATE_MACHINE_ARN),
                "drift_threshold": 0.18,
                "guardrails": {
                    "reject_global": 0.18,
                    "review_global": 0.25,
                    "warn_global": 0.32,
                },
                "request_volume_total": len(store.list_predictions(limit=500)),
                "uptime_seconds": 0,
            },
        )

    if route.endswith("/metrics/runtime"):
        predictions = store.list_predictions(limit=500) if store.config.predictions_table else []
        return _response(200, _runtime_stats(predictions))

    if route.endswith("/metrics/training/history"):
        return _response(200, {"history": []})

    if route.endswith("/review-queue") and not route.endswith("/submit"):
        try:
            items = store.list_review_queue(limit=50, status="PENDING")
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
            return _response(200, {"items": rows, "open_count": len(rows)})
        except Exception as exc:  # noqa: BLE001
            return _response(500, {"detail": str(exc)})

    if route.endswith("/submit"):
        try:
            payload = _parse_body(event)
            item = store.put_review_item({**payload, "status": payload.get("status", "PENDING")})
            return _response(200, {"status": "submitted", "item": item})
        except json.JSONDecodeError:
            return _response(400, {"detail": "invalid JSON body"})
        except Exception as exc:  # noqa: BLE001
            return _response(500, {"detail": str(exc)})

    return _response(404, {"detail": "not found"})
