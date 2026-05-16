"""Predict Lambda — API Gateway proxy for ABSA inference."""

from __future__ import annotations

import json
import os
from typing import Any

_ENDPOINT = os.getenv("SAGEMAKER_ENDPOINT_NAME", "")
_BUCKET = os.getenv("ARTIFACTS_BUCKET", "")


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


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    route = event.get("rawPath") or event.get("path", "")

    if route.endswith("/health") or event.get("requestContext", {}).get("http", {}).get("path", "").endswith("/health"):
        return _response(
            200,
            {
                "status": "ok",
                "model": "sagemaker" if _ENDPOINT else "local_stub",
                "endpoint": _ENDPOINT or None,
                "bucket": _BUCKET or None,
            },
        )

    try:
        payload = _parse_body(event)
        text = (payload.get("text") or "").strip()
        if not text:
            return _response(400, {"detail": "text is required"})

        # Thesis scaffold: wire SageMaker Runtime invoke or shared inference package here.
        return _response(
            200,
            {
                "opinions": [],
                "global_sentiment": "neutral",
                "global_confidence": 0.0,
                "latency_ms": 0,
                "note": "Lambda scaffold — connect SageMaker endpoint or layer with model package.",
            },
        )
    except json.JSONDecodeError:
        return _response(400, {"detail": "invalid JSON body"})
    except Exception as exc:  # noqa: BLE001
        return _response(500, {"detail": str(exc)})
