"""Pipeline Lambda — Step Functions tasks + HTTP API for MLOps training workflow."""

from __future__ import annotations

import json
import os
import uuid
from typing import Any

import boto3

from actions import decide_approval, dispatch_action
from lineage import build_run_lineage
from storage import (
    get_approval_request,
    get_training_run,
    list_training_runs,
    now_iso,
    put_training_run,
)
from sfn_progress import cancel_training_run, enrich_run_with_sfn_progress, initial_sfn_steps
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
        "base_model_id": payload.get("base_model_id", "absa-v2b"),
        "candidate_model_id": payload.get("candidate_model_id") or f"candidate-{run_id}",
        "approval_id": payload.get("approval_id") or f"appr-{run_id}",
        "requested_by": payload.get("requested_by", "admin-ui"),
    }


def _format_run_row(row: dict[str, Any]) -> dict[str, Any]:
    execution_arn = (
        row.get("step_function_execution_arn")
        or row.get("execution_arn")
        or f"run://{row.get('run_id', '')}"
    )
    return {
        "execution_arn": execution_arn,
        "name": row.get("run_id") or row.get("name", ""),
        "status": row.get("status", "UNKNOWN"),
        "start_date": row.get("started_at") or row.get("start_date") or row.get("created_at", ""),
        "stop_date": row.get("finished_at") or row.get("stop_date"),
        "dataset_key": row.get("dataset_key"),
        "dataset_id": row.get("dataset_id"),
        "run_id": row.get("run_id"),
        "base_model_id": row.get("base_model_id"),
        "candidate_model_id": row.get("candidate_model_id"),
        "best_f1": row.get("best_f1"),
        "artifact_uri": row.get("artifact_uri"),
        "approval_id": row.get("approval_id"),
        "training_config": row.get("training_config"),
        "stages": row.get("stages") or [],
        "sfn_steps": row.get("sfn_steps") or [],
        "current_state": row.get("current_state"),
        "sfn_status": row.get("sfn_status"),
        "evaluation": row.get("evaluation"),
        "comparison": row.get("comparison"),
        "metrics": row.get("metrics"),
        "production_uri": row.get("production_uri"),
        "code_version": row.get("code_version"),
        "training_source_uri": row.get("training_source_uri"),
        "dataset_s3_uri": row.get("dataset_s3_uri"),
    }


def _resolve_run(run_id: str) -> dict[str, Any] | None:
    run = get_training_run(run_id)
    if run is not None:
        return run
    for row in list_training_runs(limit=50):
        if row.get("run_id") == run_id:
            return row
        arn = row.get("step_function_execution_arn") or ""
        if arn and (arn == run_id or run_id in arn):
            return row
    return None


def _format_run_detail(run: dict[str, Any]) -> dict[str, Any]:
    enriched = enrich_run_with_sfn_progress(run)
    payload = _format_run_row(enriched) | {
        k: enriched[k]
        for k in (
            "evaluation",
            "comparison",
            "metrics",
            "deploy",
            "production_uri",
            "registry_status",
            "code_version",
            "training_source_uri",
            "dataset_s3_uri",
            "sfn_steps",
            "current_state",
            "sfn_status",
        )
        if k in enriched
    }
    return payload


def _is_active_run(status: str) -> bool:
    return status.upper() in {
        "RUNNING",
        "TRAINING",
        "TRAINING_IN_PROGRESS",
        "TRAINING_COMPLETED",
        "EVALUATED",
        "COMPARED",
    }


def _list_sfn_runs(limit: int = 15) -> list[dict[str, Any]]:
    if not _STATE_MACHINE_ARN:
        return []
    try:
        resp = _sfn.list_executions(stateMachineArn=_STATE_MACHINE_ARN, maxResults=limit)
    except Exception:  # noqa: BLE001 — missing IAM or SFN unavailable
        return []
    runs: list[dict[str, Any]] = []
    for item in resp.get("executions", []):
        runs.append(
            {
                "execution_arn": item["executionArn"],
                "name": item["name"],
                "status": item["status"],
                "start_date": item["startDate"].isoformat(),
                "stop_date": item.get("stopDate").isoformat() if item.get("stopDate") else None,
                "dataset_key": None,
                "stages": [],
            }
        )
    return runs


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
                "stages": ["Train", "Evaluate", "Compare", "Register", "Smoke", "Promote", "Deploy", "Done"],
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
            lineage = build_run_lineage(
                dataset_id=execution_input["dataset_id"],
                dataset_key=execution_input["dataset_key"],
                base_model_id=execution_input["base_model_id"],
                candidate_model_id=execution_input["candidate_model_id"],
                training_config=execution_input["training_config"],
            )
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
                    "dataset_s3_uri": lineage["dataset_s3_uri"],
                    "base_model_id": execution_input["base_model_id"],
                    "candidate_model_id": execution_input["candidate_model_id"],
                    "approval_id": execution_input["approval_id"],
                    "requested_by": execution_input["requested_by"],
                    "training_config": execution_input["training_config"],
                    "code_version": lineage["code_version"],
                    "training_source_uri": lineage["training_source_uri"],
                    "step_function_execution_arn": result["executionArn"],
                    "started_at": result["startDate"].isoformat(),
                }
            )
            steps = initial_sfn_steps()
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
                    "dataset_id": execution_input["dataset_id"],
                    "base_model_id": execution_input["base_model_id"],
                    "candidate_model_id": execution_input["candidate_model_id"],
                    "code_version": lineage["code_version"],
                    "training_source_uri": lineage["training_source_uri"],
                    "dataset_s3_uri": lineage["dataset_s3_uri"],
                    "sfn_steps": steps,
                    "stages": [{"name": s["name"], "status": s["status"]} for s in steps],
                    "current_state": "StartTraining",
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

    if "/pipeline/runs/" in path and path.endswith("/cancel") and method == "POST":
        run_id = path.split("/pipeline/runs/")[1].replace("/cancel", "").strip("/")
        run = _resolve_run(run_id)
        if run is None:
            return _response(404, {"detail": "Run not found"})
        try:
            payload = _parse_body(event)
            result = cancel_training_run(
                run,
                cancelled_by=str(payload.get("cancelled_by") or "console-ui"),
            )
            return _response(200, result)
        except ValueError as exc:
            return _response(400, {"detail": str(exc)})
        except Exception as exc:  # noqa: BLE001
            return _response(500, {"detail": str(exc)})

    if "/pipeline/runs/" in path and method == "GET":
        run_id = path.split("/pipeline/runs/")[1].strip("/").split("?")[0]
        run = _resolve_run(run_id)
        if run is None:
            return _response(404, {"detail": "Run not found"})
        return _response(200, _format_run_detail(run))

    if path.endswith("/pipeline/runs") and method == "GET":
        try:
            runs = list_training_runs(limit=15)
            if runs:
                formatted = []
                for row in runs:
                    if _is_active_run(str(row.get("status", ""))):
                        formatted.append(_format_run_row(enrich_run_with_sfn_progress(row)))
                    else:
                        formatted.append(_format_run_row(row))
                return _response(200, {"runs": formatted})
            return _response(200, {"runs": _list_sfn_runs(limit=15)})
        except Exception as exc:  # noqa: BLE001
            return _response(500, {"detail": str(exc)})

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
