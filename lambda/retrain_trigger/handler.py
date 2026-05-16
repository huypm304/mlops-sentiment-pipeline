"""Retrain Trigger Lambda — start Step Functions retraining workflow."""

from __future__ import annotations

import json
import os
import uuid
from typing import Any

import boto3

_STATE_MACHINE_ARN = os.getenv("RETRAIN_STATE_MACHINE_ARN", "")
_BUCKET = os.getenv("ARTIFACTS_BUCKET", "")
_sfn = boto3.client("stepfunctions")


def _response(status: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def _parse_body(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("body") or "{}"
    return json.loads(raw) if isinstance(raw, str) else raw


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    if not _STATE_MACHINE_ARN:
        return _response(503, {"detail": "RETRAIN_STATE_MACHINE_ARN is not configured"})

    try:
        payload = _parse_body(event)
    except json.JSONDecodeError:
        return _response(400, {"detail": "invalid JSON body"})

    dataset_key = payload.get("dataset_key") or "datasets/raw/latest.jsonl"
    execution_name = payload.get("execution_name") or f"retrain-{uuid.uuid4().hex[:12]}"

    input_doc = {
        "dataset_key": dataset_key,
        "bucket": _BUCKET,
        "requested_by": payload.get("requested_by", "api"),
    }

    try:
        result = _sfn.start_execution(
            stateMachineArn=_STATE_MACHINE_ARN,
            name=execution_name,
            input=json.dumps(input_doc),
        )
    except Exception as exc:  # noqa: BLE001
        return _response(500, {"detail": str(exc)})

    return _response(
        202,
        {
            "execution_arn": result["executionArn"],
            "start_date": result["startDate"].isoformat(),
            "dataset_key": dataset_key,
        },
    )
