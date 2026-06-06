"""Metrics Lambda — monitoring snapshots, drift checks, and review queue API."""

from __future__ import annotations

import json
import os
from typing import Any

_BUCKET = os.getenv("ARTIFACTS_BUCKET", "")
_MONITORING_TABLE = os.getenv("MONITORING_TABLE", "")
_REVIEW_QUEUE_TABLE = os.getenv("REVIEW_QUEUE_TABLE", "")


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
    # EventBridge scheduled invocation
    if isinstance(event, dict) and event.get("action") in {"compute_snapshot", "check_retrain_recommendation"}:
        return {"status": "ok", "action": event["action"], "note": "Metrics scaffold."}

    route = event.get("rawPath") or event.get("path", "")

    if "/metrics/" in route or route.endswith("/review-queue"):
        return _response(
            200,
            {
                "status": "ok",
                "monitoring_table": _MONITORING_TABLE or None,
                "review_queue_table": _REVIEW_QUEUE_TABLE or None,
                "items": [],
                "note": "Metrics scaffold — connect DynamoDB queries.",
            },
        )

    if route.endswith("/submit"):
        try:
            _parse_body(event)
            return _response(200, {"status": "submitted", "note": "Review queue scaffold."})
        except json.JSONDecodeError:
            return _response(400, {"detail": "invalid JSON body"})

    return _response(404, {"detail": "not found"})
