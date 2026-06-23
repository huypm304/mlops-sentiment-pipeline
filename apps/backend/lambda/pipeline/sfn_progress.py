"""Step Functions execution progress — stage stepper + cancel."""

from __future__ import annotations

from typing import Any

import boto3

from storage import now_iso, update_training_run

_AWS_REGION = __import__("os").environ.get("AWS_REGION", "ap-southeast-1")
_sfn = boto3.client("stepfunctions", region_name=_AWS_REGION)

# Display order aligned with training_pipeline.asl.json
PIPELINE_SFN_STAGES: list[tuple[str, str]] = [
    ("StartTraining", "Train"),
    ("EvaluateCandidate", "Evaluate"),
    ("CompareToProduction", "Compare"),
    ("RegisterCandidate", "Register"),
    ("SmokeTestCandidate", "Smoke"),
    ("PromoteModel", "Promote"),
    ("DeployModel", "Deploy"),
    ("NotifyResult", "Done"),
]

_TERMINAL_SFN_STATES = frozenset(
    {
        "PipelineSucceeded",
        "PipelineRejected",
        "PipelineFailed",
        "NotifyResult",
        "NotifyRejected",
        "NotifyFailure",
    }
)

_CANCELLABLE_SFN = frozenset({"RUNNING", "PENDING_REDRIVE"})


def _execution_arn_from_run(row: dict[str, Any]) -> str:
    return str(row.get("step_function_execution_arn") or row.get("execution_arn") or "")


def _parse_history(execution_arn: str) -> tuple[set[str], str | None, str]:
    completed: set[str] = set()
    current: str | None = None
    sfn_status = "UNKNOWN"

    try:
        desc = _sfn.describe_execution(executionArn=execution_arn)
        sfn_status = str(desc.get("status", "UNKNOWN"))
    except Exception:  # noqa: BLE001
        return completed, current, sfn_status

    try:
        resp = _sfn.get_execution_history(executionArn=execution_arn, reverseOrder=True, maxResults=50)
        for event in resp.get("events", []):
            if current is None and "stateEnteredEventDetails" in event:
                current = event["stateEnteredEventDetails"]["name"]
            if "stateExitedEventDetails" in event:
                completed.add(event["stateExitedEventDetails"]["name"])
    except Exception:  # noqa: BLE001
        pass

    if sfn_status == "SUCCEEDED":
        for sfn_id, _ in PIPELINE_SFN_STAGES:
            completed.add(sfn_id)
        current = None
    elif sfn_status in ("ABORTED", "TIMED_OUT"):
        current = current or None

    return completed, current, sfn_status


def build_sfn_steps(
    *,
    completed_states: set[str],
    current_state: str | None,
    sfn_status: str,
    failed: bool = False,
) -> list[dict[str, str]]:
    current_idx = _state_index(current_state) if current_state else -1
    steps: list[dict[str, str]] = []

    for idx, (sfn_id, label) in enumerate(PIPELINE_SFN_STAGES):
        if sfn_status == "SUCCEEDED":
            status = "completed"
        elif sfn_status == "ABORTED":
            if idx < current_idx or sfn_id in completed_states:
                status = "completed"
            elif idx == current_idx:
                status = "failed"
            else:
                status = "pending"
        elif sfn_id in completed_states or (current_idx >= 0 and idx < current_idx):
            status = "completed"
        elif current_state == sfn_id or idx == current_idx:
            status = "failed" if failed else "running"
        else:
            status = "pending"
        steps.append({"id": sfn_id, "name": label, "status": status})

    return steps


def _state_index(sfn_id: str) -> int:
    for idx, (sid, _) in enumerate(PIPELINE_SFN_STAGES):
        if sid == sfn_id:
            return idx
    return -1


def initial_sfn_steps() -> list[dict[str, str]]:
    steps = build_sfn_steps(
        completed_states=set(),
        current_state="StartTraining",
        sfn_status="RUNNING",
    )
    return steps


def enrich_run_with_sfn_progress(row: dict[str, Any]) -> dict[str, Any]:
    execution_arn = _execution_arn_from_run(row)
    if not execution_arn:
        return row

    completed, current, sfn_status = _parse_history(execution_arn)
    failed = sfn_status == "FAILED" or str(row.get("status", "")).upper() in ("FAILED", "REJECTED")
    steps = build_sfn_steps(
        completed_states=completed,
        current_state=current,
        sfn_status=sfn_status,
        failed=failed,
    )

    merged = dict(row)
    merged["sfn_steps"] = steps
    merged["stages"] = [{"name": s["name"], "status": s["status"]} for s in steps]
    merged["current_state"] = current
    merged["sfn_status"] = sfn_status

    if sfn_status == "SUCCEEDED" and str(row.get("status", "")).upper() == "RUNNING":
        merged["status"] = row.get("status")
    elif sfn_status == "ABORTED":
        merged["status"] = "CANCELLED"
    elif sfn_status == "FAILED":
        merged["status"] = "FAILED"

    return merged


def cancel_training_run(row: dict[str, Any], *, cancelled_by: str = "ui") -> dict[str, Any]:
    execution_arn = _execution_arn_from_run(row)
    if not execution_arn:
        raise ValueError("Run has no Step Functions execution ARN")

    desc = _sfn.describe_execution(executionArn=execution_arn)
    sfn_status = str(desc.get("status", ""))
    if sfn_status not in _CANCELLABLE_SFN:
        raise ValueError(f"Cannot cancel run with Step Functions status: {sfn_status}")

    _sfn.stop_execution(
        executionArn=execution_arn,
        error="UserCancel",
        cause=f"Cancelled by {cancelled_by}",
    )

    created_at = str(row.get("created_at") or "")
    run_id = str(row.get("run_id") or "")
    if run_id and created_at:
        update_training_run(
            run_id,
            created_at,
            {
                "status": "CANCELLED",
                "finished_at": now_iso(),
                "cancelled_by": cancelled_by,
            },
        )

    enriched = enrich_run_with_sfn_progress(
        {
            **row,
            "status": "CANCELLED",
            "step_function_execution_arn": execution_arn,
        }
    )
    return {
        "run_id": run_id,
        "status": "CANCELLED",
        "execution_arn": execution_arn,
        "sfn_steps": enriched.get("sfn_steps", []),
        "current_state": enriched.get("current_state"),
    }
