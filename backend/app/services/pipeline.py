"""Step Functions retrain pipeline — start runs and list executions."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from backend.app.config.settings import (
    ARTIFACTS_BUCKET,
    PIPELINE_DEMO_MODE,
    RETRAIN_STATE_MACHINE_ARN,
)

PIPELINE_STAGES = [
    "Upload",
    "Audit",
    "Clean",
    "Train",
    "Evaluate",
    "Register",
    "Deploy",
]

_demo_runs: list[dict[str, Any]] = []


def is_configured() -> bool:
    return bool(RETRAIN_STATE_MACHINE_ARN) and not PIPELINE_DEMO_MODE


def get_pipeline_config() -> dict[str, Any]:
    return {
        "configured": is_configured(),
        "demo_mode": not is_configured(),
        "state_machine_arn": RETRAIN_STATE_MACHINE_ARN or None,
        "artifacts_bucket": ARTIFACTS_BUCKET or None,
        "stages": PIPELINE_STAGES,
        "message": (
            "Step Functions connected — triggers start a real execution on AWS."
            if is_configured()
            else "Local demo mode — set RETRAIN_STATE_MACHINE_ARN (+ AWS credentials) "
            "to trigger the cloud workflow."
        ),
    }


def _sfn_client():
    import boto3

    return boto3.client(
        "stepfunctions",
        region_name=os.getenv("AWS_REGION", "ap-southeast-1"),
    )


def _stage_progress(status: str, current_stage: str | None) -> list[dict[str, Any]]:
    stages: list[dict[str, Any]] = []
    if status == "SUCCEEDED":
        for name in PIPELINE_STAGES:
            stages.append({"name": name, "status": "completed"})
        return stages
    if status == "FAILED":
        failed_idx = PIPELINE_STAGES.index(current_stage) if current_stage in PIPELINE_STAGES else 1
        for i, name in enumerate(PIPELINE_STAGES):
            if i < failed_idx:
                stages.append({"name": name, "status": "completed"})
            elif i == failed_idx:
                stages.append({"name": name, "status": "failed"})
            else:
                stages.append({"name": name, "status": "pending"})
        return stages
    # RUNNING / other
    active = current_stage if current_stage in PIPELINE_STAGES else "Audit"
    active_idx = PIPELINE_STAGES.index(active)
    for i, name in enumerate(PIPELINE_STAGES):
        if i < active_idx:
            stages.append({"name": name, "status": "completed"})
        elif i == active_idx:
            stages.append({"name": name, "status": "running"})
        else:
            stages.append({"name": name, "status": "pending"})
    return stages


def _infer_current_stage(execution_arn: str) -> str | None:
    try:
        hist = _sfn_client().get_execution_history(
            executionArn=execution_arn,
            reverseOrder=True,
            maxResults=30,
        )
    except Exception:
        return "Audit"
    for event in hist.get("events", []):
        if event["type"] in ("TaskStateEntered", "PassStateEntered"):
            details = event.get("stateEnteredEventDetails") or {}
            return details.get("name")
    return None


def _normalize_execution(item: dict[str, Any], *, include_stages: bool = False) -> dict[str, Any]:
    status = item.get("status", "UNKNOWN")
    current = item.get("current_stage")
    if include_stages and item.get("execution_arn") and is_configured():
        if status == "RUNNING" and not current:
            current = _infer_current_stage(item["execution_arn"])
        item = {**item, "current_stage": current}
    stages = _stage_progress(status, current) if include_stages else []
    return {**item, "stages": stages}


def _demo_trigger(dataset_key: str, requested_by: str) -> dict[str, Any]:
    run_id = f"demo-{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    run = {
        "execution_arn": f"arn:aws:states:local:demo:execution:{run_id}",
        "name": run_id,
        "status": "SUCCEEDED",
        "start_date": now,
        "stop_date": now,
        "dataset_key": dataset_key,
        "demo": True,
        "current_stage": "Deploy",
        "message": "Demo run recorded locally. Configure RETRAIN_STATE_MACHINE_ARN for AWS.",
    }
    _demo_runs.insert(0, run)
    _demo_runs[:] = _demo_runs[:20]
    return _normalize_execution(run, include_stages=True)


def start_execution(
    *,
    dataset_key: str = "datasets/raw/latest.jsonl",
    requested_by: str = "admin-ui",
) -> dict[str, Any]:
    if not is_configured():
        return _demo_trigger(dataset_key, requested_by)

    execution_name = f"retrain-{uuid.uuid4().hex[:12]}"
    input_doc = {
        "dataset_key": dataset_key,
        "bucket": ARTIFACTS_BUCKET,
        "requested_by": requested_by,
    }
    result = _sfn_client().start_execution(
        stateMachineArn=RETRAIN_STATE_MACHINE_ARN,
        name=execution_name,
        input=json.dumps(input_doc),
    )
    run = {
        "execution_arn": result["executionArn"],
        "name": execution_name,
        "status": "RUNNING",
        "start_date": result["startDate"].isoformat(),
        "stop_date": None,
        "dataset_key": dataset_key,
        "demo": False,
        "current_stage": "Upload",
    }
    return _normalize_execution(run, include_stages=True)


def list_runs(*, max_results: int = 15) -> list[dict[str, Any]]:
    if not is_configured():
        return [_normalize_execution(r, include_stages=True) for r in _demo_runs]

    arn = RETRAIN_STATE_MACHINE_ARN
    resp = _sfn_client().list_executions(
        stateMachineArn=arn,
        maxResults=min(max_results, 100),
    )
    runs: list[dict[str, Any]] = []
    for ex in resp.get("executions", []):
        runs.append(
            {
                "execution_arn": ex["executionArn"],
                "name": ex["name"],
                "status": ex["status"],
                "start_date": ex["startDate"].isoformat(),
                "stop_date": ex["stopDate"].isoformat() if ex.get("stopDate") else None,
                "dataset_key": None,
                "demo": False,
            }
        )
    return [_normalize_execution(r, include_stages=True) for r in runs]


def get_run(execution_arn: str) -> dict[str, Any] | None:
    if execution_arn.startswith("arn:aws:states:local:demo:"):
        for r in _demo_runs:
            if r["execution_arn"] == execution_arn:
                return _normalize_execution(r, include_stages=True)
        return None

    if not is_configured():
        return None

    try:
        detail = _sfn_client().describe_execution(executionArn=execution_arn)
    except Exception:
        return None

    status = detail["status"]
    current = _infer_current_stage(execution_arn) if status == "RUNNING" else None
    if status == "SUCCEEDED":
        current = "Deploy"
    inp = {}
    try:
        inp = json.loads(detail.get("input") or "{}")
    except json.JSONDecodeError:
        pass

    run = {
        "execution_arn": detail["executionArn"],
        "name": detail["name"],
        "status": status,
        "start_date": detail["startDate"].isoformat(),
        "stop_date": detail["stopDate"].isoformat() if detail.get("stopDate") else None,
        "dataset_key": inp.get("dataset_key"),
        "demo": False,
        "current_stage": current,
    }
    return _normalize_execution(run, include_stages=True)
