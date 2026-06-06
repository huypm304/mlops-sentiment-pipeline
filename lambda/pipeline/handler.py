"""Pipeline Lambda — trigger and orchestrate the ABSA MLOps training workflow."""

from __future__ import annotations

import json
import os
from typing import Any

_STATE_MACHINE_ARN = os.getenv("STATE_MACHINE_ARN", "")
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
    # Step Functions task invocation
    if isinstance(event, dict) and event.get("action"):
        action = event["action"]
        return _response(200, {"action": action, "status": "stub", "note": "Wire business logic here."})

    route = event.get("rawPath") or event.get("path", "")

    if route.endswith("/health"):
        return _response(200, {"status": "ok", "state_machine": _STATE_MACHINE_ARN or None})

    try:
        payload = _parse_body(event)
        return _response(
            200,
            {
                "status": "accepted",
                "run_id": payload.get("run_id", "stub-run"),
                "state_machine_arn": _STATE_MACHINE_ARN or None,
                "note": "Pipeline scaffold — connect Step Functions StartExecution.",
            },
        )
    except json.JSONDecodeError:
        return _response(400, {"detail": "invalid JSON body"})
    except Exception as exc:  # noqa: BLE001
        return _response(500, {"detail": str(exc)})
