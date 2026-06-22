"""Pipeline Lambda — Step Functions tasks + HTTP API for MLOps training workflow."""

from __future__ import annotations

import json
import os
import uuid
from typing import Any

import boto3

from actions import decide_approval, dispatch_action
from storage import get_approval_request, get_training_run, list_training_runs, now_iso, put_training_run
from training_config import DEFAULT_TRAINING_CONFIG, merge_training_config

_STATE_MACHINE_ARN = os.getenv("STATE_MACHINE_ARN", "")
_BUCKET = os.getenv("ARTIFACTS_BUCKET", "")
_AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")

_sfn = boto3.client("stepfunctions", region_name=_AWS_REGION)


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
    if isinstance(raw, str):
        return json.loads(raw) if raw.strip() else {}
    return raw if isinstance(raw, dict) else {}


def _route(event: dict[str, Any]) -> tuple[str, str]:
    path = event.get("rawPath") or event.get("path") or ""
    method = (
        event.get("requestContext", {}).get("http", {}).get("method")
        or event.get("httpMethod")
        or "GET"
    )
    return method.upper(), path


def _build_execution_input(payload: dict[str, Any]) -> dict[str, Any]:
    run_id = payload.get("run_id") or f"run-{uuid.uuid4().hex[:12]}"
    dataset_key = payload.get("dataset_key") or f"datasets/pending/{payload.get('dataset_id', 'dataset')}/train.jsonl"
    dataset_id = payload.get("dataset_id") or dataset_key.split("/")[2] if dataset_key.count("/") >= 2 else "dataset"
    created_at = now_iso()
    training_config = merge_training_config(payload.get("training_config"))

    return {
        "run_id": run_id,
        "created_at": created_at,
        "dataset_id": dataset_id,
        "dataset_key": dataset_key,
        "dataset_s3_uri": f"s3://{_BUCKET}/{dataset_key}",
        "artifacts_bucket": _BUCKET,
        "training_config": training_config,
        "base_model_id": payload.get("base_model_id", "absa-v1"),
        "candidate_model_id": payload.get("candidate_model_id") or f"candidate-{run_id}",
        "approval_id": payload.get("approval_id") or f"appr-{run_id}",
        "requested_by": payload.get("requested_by", "admin-ui"),
    }


def _handle_http(event: dict[str, Any]) -> dict[str, Any]:
    method, path = _route(event)

    if path.endswith("/health") and method == "GET":
        return _response(
            200,
            {
                "status": "ok",
                "state_machine": _STATE_MACHINE_ARN or None,
                "default_training_config": DEFAULT_TRAINING_CONFIG,
            },
        )

    if path.endswith("/pipeline/config") and method == "GET":
        configured = bool(_STATE_MACHINE_ARN)
        return _response(
            200,
            {
                "configured": configured,
                "demo_mode": not configured,
                "state_machine_arn": _STATE_MACHINE_ARN or None,
                "artifacts_bucket": _BUCKET or None,
                "stages": ["Train", "Evaluate", "Register", "Done"],
                "default_training_config": DEFAULT_TRAINING_CONFIG,
                "message": (
                    "Step Functions connected — chọn dataset, config, trigger."
                    if configured
                    else "STATE_MACHINE_ARN chưa cấu hình."
                ),
            },
        )

    if path.endswith("/pipeline/training-config") and method == "GET":
        return _response(200, {"training_config": DEFAULT_TRAINING_CONFIG})

    if path.endswith("/pipeline/trigger") and method == "POST":
        if not _STATE_MACHINE_ARN:
            return _response(503, {"detail": "STATE_MACHINE_ARN is not configured"})
        try:
            payload = _parse_body(event)
            execution_input = _build_execution_input(payload)
            name = f"retrain-{execution_input['run_id']}"[:80]
            result = _sfn.start_execution(
                stateMachineArn=_STATE_MACHINE_ARN,
                name=name,
                input=json.dumps(execution_input),
            )
            put_training_run(
                {
                    "run_id": execution_input["run_id"],
                    "created_at": execution_input["created_at"],
                    "status": "RUNNING",
                    "dataset_id": execution_input["dataset_id"],
                    "dataset_key": execution_input["dataset_key"],
                    "base_model_id": execution_input["base_model_id"],
                    "candidate_model_id": execution_input["candidate_model_id"],
                    "approval_id": execution_input["approval_id"],
                    "requested_by": execution_input["requested_by"],
                    "training_config": execution_input["training_config"],
                    "step_function_execution_arn": result["executionArn"],
                    "started_at": result["startDate"].isoformat(),
                }
            )
            return _response(
                200,
                {
                    "execution_arn": result["executionArn"],
                    "name": name,
                    "status": "RUNNING",
                    "start_date": result["startDate"].isoformat(),
                    "run_id": execution_input["run_id"],
                    "approval_id": execution_input["approval_id"],
                    "training_config": execution_input["training_config"],
                    "dataset_key": execution_input["dataset_key"],
                },
            )
        except json.JSONDecodeError:
            return _response(400, {"detail": "invalid JSON body"})
        except Exception as exc:  # noqa: BLE001
            return _response(500, {"detail": str(exc)})

    if "/pipeline/approvals/" in path and path.endswith("/decide") and method == "POST":
        try:
            approval_id = path.split("/pipeline/approvals/")[1].split("/")[0]
            payload = _parse_body(event)
            decision = payload.get("decision", "approve")
            result = decide_approval(
                approval_id,
                decision=decision,
                decided_by=payload.get("decided_by", "admin-ui"),
            )
            return _response(200, result)
        except KeyError as exc:
            return _response(404, {"detail": str(exc)})
        except ValueError as exc:
            return _response(400, {"detail": str(exc)})
        except Exception as exc:  # noqa: BLE001
            return _response(500, {"detail": str(exc)})

    if "/pipeline/approvals/" in path and method == "GET":
        approval_id = path.split("/pipeline/approvals/")[1].split("/")[0]
        record = get_approval_request(approval_id)
        if record is None:
            return _response(404, {"detail": "Approval not found"})
        record.pop("task_token", None)
        return _response(200, record)

    if "/pipeline/runs/" in path and method == "GET":
        run_id = path.split("/pipeline/runs/")[1].strip("/")
        run = get_training_run(run_id)
        if run is None:
            return _response(404, {"detail": "Run not found"})
        return _response(200, run)

    if path.endswith("/pipeline/runs") and method == "GET":
        runs = list_training_runs(limit=15)
        if runs:
            return _response(200, {"runs": runs})
        if not _STATE_MACHINE_ARN:
            return _response(200, {"runs": []})
        resp = _sfn.list_executions(stateMachineArn=_STATE_MACHINE_ARN, maxResults=15)
        sfn_runs = []
        for item in resp.get("executions", []):
            sfn_runs.append(
                {
                    "execution_arn": item["executionArn"],
                    "name": item["name"],
                    "status": item["status"],
                    "start_date": item["startDate"].isoformat(),
                    "stop_date": item.get("stopDate").isoformat() if item.get("stopDate") else None,
                }
            )
        return _response(200, {"runs": sfn_runs})

    if path.endswith("/models") and method == "GET":
        from storage import list_model_records

        return _response(200, {"models": list_model_records(limit=20)})

    if path.endswith("/models/compare") and method == "GET":
        from storage import list_model_records

        production = list_model_records(status="PRODUCTION", limit=1)
        candidates = list_model_records(status="CANDIDATE", limit=5)
        return _response(
            200,
            {
                "production": production[0] if production else None,
                "candidates": candidates,
            },
        )

    return _response(404, {"detail": f"No route for {method} {path}"})


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    # Step Functions direct task invocation
    if isinstance(event, dict) and event.get("action") and not event.get("requestContext"):
        try:
            return dispatch_action(event)
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc), "action": event.get("action")}

    if event.get("requestContext") or event.get("rawPath") or event.get("path"):
        return _handle_http(event)

    return _response(400, {"detail": "Unsupported event shape"})
