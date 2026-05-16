"""Analytics Lambda — dashboard summary metrics (scaffold)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

_BUCKET = os.getenv("ARTIFACTS_BUCKET", "")


def _response(status: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    # Production: query RDS / CloudWatch / inference logs.
    return _response(
        200,
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "bucket": _BUCKET or None,
            "inference_count_24h": 0,
            "error_rate": 0.0,
            "avg_latency_ms": 0,
            "sentiment_distribution": {
                "positive": 0,
                "negative": 0,
                "neutral": 0,
            },
            "note": "Analytics scaffold — connect PostgreSQL RDS and inference history.",
        },
    )
