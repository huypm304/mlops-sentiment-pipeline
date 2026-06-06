"""Predict Lambda — API Gateway proxy for ABSA inference."""

from __future__ import annotations

import json
import os
import time
from typing import Any

from registry.store import RegistryStore

_ENDPOINT = os.getenv("SAGEMAKER_ENDPOINT_NAME", "")
_ENABLE_SAGEMAKER = os.getenv("ENABLE_SAGEMAKER_ENDPOINT", "false").lower() == "true"
_BUCKET = os.getenv("ARTIFACTS_BUCKET", "")
_store: RegistryStore | None = None


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


def _record_prediction(
    *,
    text: str,
    global_sentiment: str,
    global_confidence: float,
    latency_ms: int,
    model_version: str,
    opinions: list[dict[str, Any]],
) -> None:
    store = _get_store()
    if not store.config.predictions_table:
        return

    preview = text.strip()
    if len(preview) > 200:
        preview = preview[:197] + "..."

    guardrail_status = "OK"
    need_review = False
    if global_confidence < 0.32 or not opinions:
        guardrail_status = "WARN"
        need_review = True

    prediction = store.put_prediction(
        {
            "model_id": model_version,
            "model_version": model_version,
            "text_preview": preview,
            "global_sentiment": global_sentiment,
            "confidence": round(global_confidence, 4),
            "guardrail_status": guardrail_status,
            "need_review": need_review,
            "latency_ms": latency_ms,
            "aspects": [str(o.get("aspect", "")) for o in opinions if o.get("aspect")],
        }
    )

    if need_review and store.config.review_queue_table:
        store.put_review_item(
            {
                "prediction_id": prediction["prediction_id"],
                "model_id": model_version,
                "text_preview": preview,
                "global_sentiment": global_sentiment,
                "confidence": round(global_confidence, 4),
                "guardrail_status": guardrail_status,
                "priority": "urgent" if global_confidence < 0.18 else "normal",
            }
        )


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    route = event.get("rawPath") or event.get("path", "")

    if route.endswith("/health") or event.get("requestContext", {}).get("http", {}).get("path", "").endswith("/health"):
        return _response(
            200,
            {
                "status": "ok",
                "model": "sagemaker" if _ENDPOINT and _ENABLE_SAGEMAKER else "local_stub",
                "endpoint": _ENDPOINT or None,
                "bucket": _BUCKET or None,
            },
        )

    try:
        payload = _parse_body(event)
        text = (payload.get("text") or "").strip()
        if not text:
            return _response(400, {"detail": "text is required"})

        started = time.time()
        model_version = "absa-v1"
        # Thesis scaffold: wire SageMaker Runtime invoke or shared inference package here.
        latency_ms = int((time.time() - started) * 1000)
        result = {
            "opinions": [],
            "global_sentiment": "neutral",
            "global_confidence": 0.0,
            "latency_ms": latency_ms,
            "model_version": model_version,
            "note": "Lambda scaffold — connect SageMaker endpoint or layer with model package.",
        }
        _record_prediction(
            text=text,
            global_sentiment=result["global_sentiment"],
            global_confidence=float(result["global_confidence"]),
            latency_ms=latency_ms,
            model_version=model_version,
            opinions=result["opinions"],
        )
        return _response(200, result)
    except json.JSONDecodeError:
        return _response(400, {"detail": "invalid JSON body"})
    except Exception as exc:  # noqa: BLE001
        return _response(500, {"detail": str(exc)})
