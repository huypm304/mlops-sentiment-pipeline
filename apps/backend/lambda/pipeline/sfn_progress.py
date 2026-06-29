"""Step Functions execution progress — stage stepper + cancel."""

from __future__ import annotations

from typing import Any

import boto3

from storage import now_iso, update_training_run

_AWS_REGION = __import__("os").environ.get("AWS_REGION", "ap-southeast-1")
_STATE_MACHINE_ARN = __import__("os").environ.get("STATE_MACHINE_ARN", "")
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

_ACTIVE_RUN_STATUSES = frozenset(
    {
        "RUNNING",
        "TRAINING",
        "TRAINING_IN_PROGRESS",
        "TRAINING_COMPLETED",
        "EVALUATED",
        "COMPARED",
    }
)

_CANCELLABLE_SFN = frozenset({"RUNNING", "PENDING_REDRIVE"})

_SFN_LIST_STATUSES = (
    "RUNNING",
    "PENDING_REDRIVE",
    "FAILED",
    "ABORTED",
    "TIMED_OUT",
    "SUCCEEDED",
)


def _execution_arn_from_run(row: dict[str, Any]) -> str:
    return str(row.get("step_function_execution_arn") or row.get("execution_arn") or "")


def _find_execution_arn_by_run_id(run_id: str) -> str:
    if not _STATE_MACHINE_ARN or not run_id:
        return ""
    name = f"retrain-{run_id}"[:80]
    try:
        paginator = _sfn.get_paginator("list_executions")
        for status in _SFN_LIST_STATUSES:
            for page in paginator.paginate(
                stateMachineArn=_STATE_MACHINE_ARN,
                statusFilter=status,
            ):
                for execution in page.get("executions", []):
                    if execution.get("name") == name:
                        return str(execution.get("executionArn") or "")
    except Exception:  # noqa: BLE001
        return ""
    return ""


def _resolve_execution_arn(row: dict[str, Any]) -> str:
    arn = _execution_arn_from_run(row)
    if arn:
        return arn
    return _find_execution_arn_by_run_id(str(row.get("run_id") or ""))


def _persist_run_updates(row: dict[str, Any], updates: dict[str, Any]) -> None:
    run_id = str(row.get("run_id") or "")
    created_at = str(row.get("created_at") or "")
    if run_id and created_at:
        update_training_run(run_id, created_at, updates)


def _status_from_sfn(sfn_status: str) -> str | None:
    if sfn_status in {"FAILED", "TIMED_OUT"}:
        return "FAILED"
    if sfn_status == "ABORTED":
        return "CANCELLED"
    return None


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
        train_phase_done = "EvaluateCandidate" in completed_states or (
            current_idx >= 0 and current_idx > 0
        )
        if sfn_status == "SUCCEEDED":
            status = "completed"
        elif sfn_status == "ABORTED":
            if idx == 0 and train_phase_done:
                status = "completed"
            elif idx < current_idx or sfn_id in completed_states:
                status = "completed"
            elif idx == current_idx:
                status = "failed"
            else:
                status = "pending"
        elif sfn_id == "StartTraining":
            if train_phase_done:
                status = "completed"
            elif current_state in _TRAIN_POLL_STATES or current_idx == 0:
                status = "failed" if failed else "running"
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


_TRAIN_POLL_STATES = frozenset(
    {"StartTraining", "CheckTrainingStatus", "WaitForTraining", "TrainingCompleteGate"}
)


def _state_index(sfn_id: str) -> int:
    if sfn_id in _TRAIN_POLL_STATES:
        sfn_id = "StartTraining"
    for idx, (sid, _) in enumerate(PIPELINE_SFN_STAGES):
        if sid == sfn_id:
            return idx
    return -1


def initial_sfn_steps() -> list[dict[str, str]]:
    return build_sfn_steps(
        completed_states=set(),
        current_state="StartTraining",
        sfn_status="RUNNING",
    )


def enrich_run_with_sfn_progress(row: dict[str, Any]) -> dict[str, Any]:
    execution_arn = _resolve_execution_arn(row)
    if not execution_arn:
        return row

    completed, current, sfn_status = _parse_history(execution_arn)
    failed = sfn_status in {"FAILED", "TIMED_OUT"} or str(row.get("status", "")).upper() in (
        "FAILED",
        "REJECTED",
    )
    steps = build_sfn_steps(
        completed_states=completed,
        current_state=current,
        sfn_status=sfn_status,
        failed=failed,
    )

    merged = dict(row)
    merged["step_function_execution_arn"] = execution_arn
    merged["execution_arn"] = execution_arn
    merged["sfn_steps"] = steps
    merged["stages"] = [{"name": s["name"], "status": s["status"]} for s in steps]
    merged["current_state"] = current
    merged["sfn_status"] = sfn_status

    row_status = str(row.get("status", "")).upper()
    if sfn_status == "ABORTED":
        merged["status"] = "CANCELLED"
    elif sfn_status in {"FAILED", "TIMED_OUT"}:
        merged["status"] = "FAILED"
    elif sfn_status == "SUCCEEDED" and row_status in _ACTIVE_RUN_STATUSES:
        merged["status"] = row.get("status")

    persist: dict[str, Any] = {"step_function_execution_arn": execution_arn}
    if str(merged.get("status", "")).upper() != row_status and merged.get("status"):
        persist["status"] = merged["status"]
        if str(merged["status"]).upper() in {"FAILED", "CANCELLED", "COMPLETED", "REJECTED"}:
            persist["finished_at"] = now_iso()
    if len(persist) > 1 or not _execution_arn_from_run(row):
        _persist_run_updates(row, persist)

    return merged


def cancel_training_run(row: dict[str, Any], *, cancelled_by: str = "ui") -> dict[str, Any]:
    run_id = str(row.get("run_id") or "")
    execution_arn = _resolve_execution_arn(row)

    if not execution_arn:
        _persist_run_updates(
            row,
            {
                "status": "CANCELLED",
                "finished_at": now_iso(),
                "cancelled_by": cancelled_by,
                "message": "Marked cancelled locally (no Step Functions execution ARN found).",
            },
        )
        return {
            "run_id": run_id,
            "status": "CANCELLED",
            "execution_arn": "",
            "message": "Run cleared in registry; no active Step Functions execution was found.",
        }

    desc = _sfn.describe_execution(executionArn=execution_arn)
    sfn_status = str(desc.get("status", ""))

    if sfn_status not in _CANCELLABLE_SFN:
        synced = _status_from_sfn(sfn_status)
        if synced:
            _persist_run_updates(
                row,
                {
                    "status": synced,
                    "finished_at": now_iso(),
                    "step_function_execution_arn": execution_arn,
                    "message": f"Step Functions already {sfn_status}; synced registry status.",
                },
            )
            enriched = enrich_run_with_sfn_progress({**row, "status": synced, "step_function_execution_arn": execution_arn})
            return {
                "run_id": run_id,
                "status": synced,
                "execution_arn": execution_arn,
                "sfn_steps": enriched.get("sfn_steps", []),
                "current_state": enriched.get("current_state"),
                "message": f"Execution already {sfn_status}; registry updated.",
            }
        raise ValueError(f"Cannot cancel run with Step Functions status: {sfn_status}")

    _sfn.stop_execution(
        executionArn=execution_arn,
        error="UserCancel",
        cause=f"Cancelled by {cancelled_by}",
    )

    _persist_run_updates(
        row,
        {
            "status": "CANCELLED",
            "finished_at": now_iso(),
            "cancelled_by": cancelled_by,
            "step_function_execution_arn": execution_arn,
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
