"""Audit Lambda — dataset quality checks for the retraining pipeline."""

from __future__ import annotations

import json
import os
from typing import Any

_BUCKET = os.getenv("ARTIFACTS_BUCKET", "")


def _response(status: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def _run_audit(dataset_key: str) -> dict[str, Any]:
    """Placeholder audit — replace with BIO/span/polarity validators."""
    return {
        "passed": True,
        "dataset_key": dataset_key,
        "bucket": _BUCKET,
        "checks": {
            "bio_validation": "skipped",
            "span_offsets": "skipped",
            "polarity_consistency": "skipped",
            "duplicate_opinions": "skipped",
        },
        "report_key": f"reports/audit-{dataset_key.replace('/', '-')}.json",
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    # Step Functions invoke passes Payload directly; API Gateway wraps body.
    if "body" in event:
        try:
            raw = event.get("body") or "{}"
            payload = json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError:
            return _response(400, {"detail": "invalid JSON body"})
    else:
        payload = event.get("Payload") or event

    dataset_key = payload.get("dataset_key") or payload.get("s3_key") or "datasets/raw/latest.jsonl"
    result = _run_audit(dataset_key)

    # Step Functions Task expects serializable output in Payload when using lambda:invoke.
    if "action" in payload and payload.get("action") == "audit":
        return result

    return _response(200, result)
