"""Step Functions retrain pipeline — start runs, approvals, and list executions."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.config.settings import (
    APPROVAL_TABLE,
    ARTIFACTS_BUCKET,
    AWS_REGION,
    PIPELINE_DEMO_MODE,
    REPO_ROOT,
    RETRAIN_STATE_MACHINE_ARN,
)
from backend.app.services import datasets as datasets_service
from backend.app.services import registry_db

PIPELINE_STAGES = ["Train", "Evaluate", "Register", "Done"]

SFN_DISPLAY_STEPS: list[tuple[str, str]] = [
    ("StartTraining", "Training"),
    ("EvaluateCandidate", "Evaluate"),
    ("RegisterCandidate", "Register"),
    ("NotifyResult", "Done"),
]

SFN_FAIL_STATES = {"PipelineFailed", "NotifyFailure"}

_demo_runs: list[dict[str, Any]] = []

PRODUCTION_BASELINE = {
    "tas_f1": 0.72,
    "span_f1": 0.68,
    "sentiment_f1": 0.75,
    "global_f1": 0.73,
}

EVAL_REPORTS_DIR = REPO_ROOT / "reports" / "evaluation"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _default_training_config() -> dict[str, Any]:
    path = REPO_ROOT / "model" / "run_config.json"
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        keys = [
            "model_name",
            "epochs",
            "patience",
            "batch_size",
            "lr_backbone",
            "lr_heads",
            "lambda_bio",
            "lambda_sent",
            "lambda_global",
            "lambda_cons",
            "lambda_contrast",
            "contrast_sampler_weight",
        ]
        return {key: data[key] for key in keys if key in data}
    return {
        "model_name": "Fsoft-AIC/videberta-base",
        "epochs": 50,
        "patience": 8,
        "batch_size": 24,
        "lr_backbone": 8e-6,
        "lr_heads": 3e-5,
        "lambda_bio": 1.1,
        "lambda_sent": 1.4,
        "lambda_global": 0.2,
        "lambda_cons": 0.0,
        "lambda_contrast": 0.0,
        "contrast_sampler_weight": 1.2,
    }


def merge_training_config(overrides: dict[str, Any] | None) -> dict[str, Any]:
    merged = _default_training_config()
    if overrides:
        merged.update({k: v for k, v in overrides.items() if v is not None})
    return merged


def is_configured() -> bool:
    return bool(RETRAIN_STATE_MACHINE_ARN) and not PIPELINE_DEMO_MODE


def get_pipeline_config() -> dict[str, Any]:
    return {
        "configured": is_configured(),
        "demo_mode": not is_configured(),
        "state_machine_arn": RETRAIN_STATE_MACHINE_ARN or None,
        "artifacts_bucket": ARTIFACTS_BUCKET or None,
        "stages": PIPELINE_STAGES,
        "default_training_config": _default_training_config(),
        "message": (
            "Step Functions connected — chọn dataset, config, trigger (train → evaluate → register)."
            if is_configured()
            else "Chưa kết nối AWS Step Functions — set RETRAIN_STATE_MACHINE_ARN + credentials để chạy."
        ),
    }


def _sfn_client():
    import boto3

    return boto3.client("stepfunctions", region_name=os.getenv("AWS_REGION", "ap-southeast-1"))


def _s3_client():
    import boto3

    return boto3.client("s3", region_name=os.getenv("AWS_REGION", "ap-southeast-1"))


def _sync_local_dataset_to_s3(dataset_id: str) -> str:
    if not ARTIFACTS_BUCKET:
        raise RuntimeError("ARTIFACTS_BUCKET is required to sync dataset to S3")

    manifest = datasets_service.get_dataset(dataset_id)
    s3 = _s3_client()
    prefix = f"datasets/pending/{dataset_id}"
    for split, info in manifest.get("splits", {}).items():
        local_path = datasets_service.resolve_split_path(dataset_id, split)
        key = f"{prefix}/{info['filename']}"
        s3.upload_file(str(local_path), ARTIFACTS_BUCKET, key)
    return f"{prefix}/train.jsonl"


def _build_execution_input(
    *,
    dataset_key: str | None,
    dataset_id: str | None,
    requested_by: str,
    base_model_id: str,
    training_config: dict[str, Any] | None,
) -> dict[str, Any]:
    if not ARTIFACTS_BUCKET:
        raise RuntimeError("ARTIFACTS_BUCKET is not configured")

    run_id = f"run-{uuid.uuid4().hex[:12]}"
    created_at = _now_iso()
    resolved_key = dataset_key

    if dataset_id:
        resolved_key = _sync_local_dataset_to_s3(dataset_id)
    elif not resolved_key:
        resolved_key = "datasets/pending/latest/train.jsonl"

    ds_id = dataset_id or resolved_key.split("/")[2] if "/datasets/" in resolved_key else "dataset"
    config = merge_training_config(training_config)

    return {
        "run_id": run_id,
        "created_at": created_at,
        "dataset_id": ds_id,
        "dataset_key": resolved_key,
        "dataset_s3_uri": f"s3://{ARTIFACTS_BUCKET}/{resolved_key}",
        "artifacts_bucket": ARTIFACTS_BUCKET,
        "training_config": config,
        "base_model_id": base_model_id,
        "candidate_model_id": f"candidate-{run_id}",
        "approval_id": f"appr-{run_id}",
        "requested_by": requested_by,
    }


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
    steps, current = _build_sfn_timeline(execution_arn, "RUNNING")
    if current:
        return current
    for step in steps:
        if step["status"] == "running":
            return step["id"]
    return None


def _build_sfn_timeline(execution_arn: str, execution_status: str) -> tuple[list[dict[str, Any]], str | None]:
    """Parse Step Functions history into a user-facing step timeline."""
    if execution_arn.startswith("arn:aws:states:local:demo:"):
        return _demo_sfn_timeline(execution_status)

    try:
        events: list[dict[str, Any]] = []
        next_token: str | None = None
        while True:
            kwargs: dict[str, Any] = {"executionArn": execution_arn, "maxResults": 200}
            if next_token:
                kwargs["nextToken"] = next_token
            page = _sfn_client().get_execution_history(**kwargs)
            events.extend(page.get("events") or [])
            next_token = page.get("nextToken")
            if not next_token:
                break
    except Exception:
        return _coarse_stage_fallback(execution_status, None)

    entered_order: list[str] = []
    completed: set[str] = set()
    failed_state: str | None = None
    current: str | None = None

    for event in events:
        event_type = event.get("type", "")
        if event_type == "TaskStateEntered":
            name = (event.get("stateEnteredEventDetails") or {}).get("name")
            if name:
                entered_order.append(name)
                current = name
        elif event_type in {"TaskStateExited", "ChoiceStateExited", "PassStateExited"}:
            name = (event.get("stateExitedEventDetails") or {}).get("name")
            if name:
                completed.add(name)
        elif event_type == "FailStateEntered":
            failed_state = (event.get("stateEnteredEventDetails") or {}).get("name")
            current = failed_state
        elif event_type == "ExecutionFailed":
            if not failed_state and entered_order:
                failed_state = entered_order[-1]

    display_ids = [step_id for step_id, _ in SFN_DISPLAY_STEPS]
    if execution_status == "RUNNING" and current in completed:
        current = None
        for step_id in reversed(display_ids):
            if step_id in entered_order and step_id not in completed:
                current = step_id
                break
        if current is None and entered_order:
            current = entered_order[-1]

    if execution_status == "SUCCEEDED":
        current = "NotifyResult"

    steps: list[dict[str, Any]] = []
    current_idx = display_ids.index(current) if current in display_ids else -1

    for idx, (step_id, label) in enumerate(SFN_DISPLAY_STEPS):
        if execution_status == "SUCCEEDED":
            status = "completed"
        elif failed_state in SFN_FAIL_STATES and step_id == "ValidateDataset" and failed_state == "DatasetRejected":
            status = "failed" if idx == 0 else ("pending" if idx > 0 else "failed")
        elif execution_status == "FAILED":
            if step_id in completed:
                status = "completed"
            elif step_id == current or (current_idx >= 0 and idx == current_idx):
                status = "failed"
            elif current_idx >= 0 and idx < current_idx:
                status = "completed"
            else:
                status = "pending"
        elif execution_status == "RUNNING":
            if step_id in completed:
                status = "completed"
            elif step_id == current or idx == current_idx:
                status = "running"
            elif current_idx >= 0 and idx < current_idx:
                status = "completed"
            else:
                status = "pending"
        else:
            status = "completed" if step_id in completed else "pending"

        steps.append({"id": step_id, "name": label, "status": status})

    return steps, current


def _demo_sfn_timeline(execution_status: str) -> tuple[list[dict[str, Any]], str | None]:
    if execution_status == "SUCCEEDED":
        steps = [{"id": s[0], "name": s[1], "status": "completed"} for s in SFN_DISPLAY_STEPS]
        return steps, "NotifyResult"
    if execution_status == "FAILED":
        steps = [
            {"id": s[0], "name": s[1], "status": "failed" if i == 0 else "pending"}
            for i, s in enumerate(SFN_DISPLAY_STEPS)
        ]
        return steps, SFN_DISPLAY_STEPS[0][0]
    steps = [
        {"id": s[0], "name": s[1], "status": "running" if i == 0 else "pending"}
        for i, s in enumerate(SFN_DISPLAY_STEPS)
    ]
    return steps, SFN_DISPLAY_STEPS[0][0]


def _coarse_stage_fallback(execution_status: str, current: str | None) -> tuple[list[dict[str, Any]], str | None]:
    stages = _stage_progress(execution_status, current)
    return [{"id": s["name"].lower(), "name": s["name"], "status": s["status"]} for s in stages], current


def _infer_current_stage_legacy(execution_arn: str) -> str | None:
    try:
        hist = _sfn_client().get_execution_history(
            executionArn=execution_arn,
            reverseOrder=True,
            maxResults=40,
        )
    except Exception:
        return "Audit"
    stage_map = {
        "ValidateDataset": "Audit",
        "CheckApproval": "Approval",
        "StartTraining": "Train",
        "EvaluateCandidate": "Evaluate",
        "RegisterCandidate": "Register",
        "PromoteModel": "Deploy",
    }
    for event in hist.get("events", []):
        if event["type"] in ("TaskStateEntered", "PassStateEntered"):
            details = event.get("stateEnteredEventDetails") or {}
            name = details.get("name") or ""
            return stage_map.get(name, name)
    return None


def _normalize_execution(
    item: dict[str, Any],
    *,
    include_stages: bool = False,
    include_sfn_timeline: bool = False,
) -> dict[str, Any]:
    status = item.get("status", "UNKNOWN")
    current = item.get("current_state")
    execution_arn = item.get("execution_arn")

    if include_sfn_timeline and execution_arn:
        sfn_steps, sfn_current = _build_sfn_timeline(execution_arn, status)
        item = {
            **item,
            "sfn_steps": sfn_steps,
            "current_state": sfn_current,
            "current_stage": _map_sfn_to_coarse_stage(sfn_current),
        }
    elif include_stages and execution_arn and is_configured():
        if status == "RUNNING" and not current:
            current = _infer_current_stage_legacy(execution_arn)
        item = {**item, "current_stage": current}

    stages = _stage_progress(status, item.get("current_stage")) if include_stages else []
    return {**item, "stages": stages}


def _build_comparison(metrics: dict[str, Any]) -> dict[str, Any]:
    delta = {
        key: round(float(metrics.get(key, 0)) - PRODUCTION_BASELINE.get(key, 0), 4)
        for key in PRODUCTION_BASELINE
    }
    metric_gate_passed = float(metrics.get("global_f1", 0)) >= PRODUCTION_BASELINE["global_f1"]
    return {
        "production_baseline": PRODUCTION_BASELINE,
        "candidate_metrics": metrics,
        "delta": delta,
        "metric_gate_passed": metric_gate_passed,
        "promote": metric_gate_passed,
    }


def _mock_evaluation_report(run_id: str, *, mode: str = "mock") -> dict[str, Any]:
    metrics = {
        key: round(PRODUCTION_BASELINE[key] + bump, 4)
        for key, bump in {
            "tas_f1": 0.015,
            "span_f1": 0.012,
            "sentiment_f1": 0.01,
            "global_f1": 0.014,
        }.items()
    }
    metrics["mode"] = mode
    return {
        "run_id": run_id,
        "candidate_model_id": f"candidate-{run_id}",
        "metrics": metrics,
        "evaluated_at": _now_iso(),
    }


def _save_eval_report(report: dict[str, Any]) -> Path:
    EVAL_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = EVAL_REPORTS_DIR / f"{report['run_id']}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _load_eval_report(run_id: str) -> dict[str, Any] | None:
    local_path = EVAL_REPORTS_DIR / f"{run_id}.json"
    if local_path.is_file():
        return json.loads(local_path.read_text(encoding="utf-8"))

    if not ARTIFACTS_BUCKET:
        return None

    try:
        obj = _s3_client().get_object(
            Bucket=ARTIFACTS_BUCKET,
            Key=f"reports/evaluation/{run_id}.json",
        )
        return json.loads(obj["Body"].read().decode("utf-8"))
    except Exception:
        return None


def _attach_run_artifacts(run: dict[str, Any]) -> dict[str, Any]:
    run_id = run.get("run_id")
    if not run_id:
        return run

    enriched = dict(run)
    metrics = (run.get("metrics") or {}) if isinstance(run.get("metrics"), dict) else {}
    training_config = run.get("training_config")

    if run.get("artifact_uri"):
        enriched["artifact_uri"] = run["artifact_uri"]
    elif ARTIFACTS_BUCKET:
        enriched["artifact_uri"] = f"s3://{ARTIFACTS_BUCKET}/training-runs/{run_id}/"

    if metrics:
        enriched["best_f1"] = metrics.get("tas_relaxed_f1") or metrics.get("global_f1")
        enriched["evaluation"] = {
            "run_id": run_id,
            "candidate_model_id": run.get("candidate_model_id"),
            "metrics": metrics,
            "evaluated_at": run.get("finished_at") or run.get("updated_at"),
            "mode": "training_run",
        }
        enriched["comparison"] = _build_comparison(metrics)
        if training_config:
            enriched["training_config"] = training_config
        return enriched

    evaluation = _load_eval_report(str(run_id))
    if not evaluation:
        summary = _load_run_summary(str(run_id))
        if summary:
            metrics = summary.get("metrics") or {}
            enriched["evaluation"] = {
                "run_id": run_id,
                "metrics": metrics,
                "evaluated_at": summary.get("generated_at"),
                "mode": "training_run",
            }
            enriched["best_f1"] = metrics.get("tas_relaxed_f1") or metrics.get("global_f1")
            if summary.get("config"):
                enriched["training_config"] = summary["config"]
            if metrics:
                enriched["comparison"] = _build_comparison(metrics)
        return enriched

    metrics = evaluation.get("metrics") or {}
    if not metrics:
        return enriched
    return {
        **enriched,
        "evaluation": evaluation,
        "comparison": _build_comparison(metrics),
        "best_f1": metrics.get("tas_relaxed_f1") or metrics.get("global_f1"),
    }


def _load_run_summary(run_id: str) -> dict[str, Any] | None:
    local_path = REPO_ROOT / "experiments" / "training-runs" / run_id / "summary.json"
    if local_path.is_file():
        return json.loads(local_path.read_text(encoding="utf-8"))

    if not ARTIFACTS_BUCKET:
        return None

    try:
        obj = _s3_client().get_object(
            Bucket=ARTIFACTS_BUCKET,
            Key=f"training-runs/{run_id}/summary.json",
        )
        return json.loads(obj["Body"].read().decode("utf-8"))
    except Exception:
        return None


def get_run_evaluation(run_id: str) -> dict[str, Any] | None:
    report = _load_eval_report(run_id)
    if not report:
        return None
    metrics = report.get("metrics") or {}
    return {
        "evaluation": report,
        "comparison": _build_comparison(metrics),
    }


def _map_sfn_to_coarse_stage(state: str | None) -> str | None:
    if not state:
        return None
    mapping = {
        "StartTraining": "Train",
        "EvaluateCandidate": "Evaluate",
        "RegisterCandidate": "Register",
        "NotifyResult": "Done",
        "NotifyFailure": "Done",
    }
    return mapping.get(state, state)


def start_execution(
    *,
    dataset_id: str,
    requested_by: str = "admin-ui",
    base_model_id: str = "absa-v1",
    training_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not dataset_id.strip():
        raise ValueError("dataset_id is required")

    if not is_configured():
        raise RuntimeError(
            "Pipeline chưa kết nối AWS. Set RETRAIN_STATE_MACHINE_ARN, ARTIFACTS_BUCKET và AWS credentials."
        )

    config = merge_training_config(training_config)
    execution_input = _build_execution_input(
        dataset_key=None,
        dataset_id=dataset_id,
        requested_by=requested_by,
        base_model_id=base_model_id,
        training_config=config,
    )
    execution_name = f"retrain-{execution_input['run_id']}"[:80]
    result = _sfn_client().start_execution(
        stateMachineArn=RETRAIN_STATE_MACHINE_ARN,
        name=execution_name,
        input=json.dumps(execution_input),
    )
    store = registry_db.get_store()
    if store is not None and store.config.training_runs_table:
        store.put_training_run(
            {
                "run_id": execution_input["run_id"],
                "created_at": execution_input["created_at"],
                "status": "RUNNING",
                "dataset_id": execution_input["dataset_id"],
                "dataset_key": execution_input["dataset_key"],
                "base_model_id": execution_input["base_model_id"],
                "candidate_model_id": execution_input["candidate_model_id"],
                "approval_id": execution_input["approval_id"],
                "requested_by": requested_by,
                "training_config": execution_input["training_config"],
                "step_function_execution_arn": result["executionArn"],
                "started_at": result["startDate"].isoformat(),
            }
        )
    run = {
        "execution_arn": result["executionArn"],
        "name": execution_name,
        "status": "RUNNING",
        "start_date": result["startDate"].isoformat(),
        "stop_date": None,
        "dataset_key": execution_input["dataset_key"],
        "run_id": execution_input["run_id"],
        "approval_id": execution_input["approval_id"],
        "training_config": execution_input["training_config"],
        "demo": False,
        "current_stage": "Train",
    }
    return _normalize_execution(run, include_stages=True, include_sfn_timeline=True)


def _local_run_item(row: dict[str, Any]) -> dict[str, Any]:
    run_id = str(row.get("run_id", ""))
    status = str(row.get("status", "COMPLETED")).upper()
    if status == "COMPLETED":
        status = "SUCCEEDED"
    return {
        "execution_arn": f"local://training-runs/{run_id}",
        "name": run_id,
        "status": status if status in {"RUNNING", "FAILED", "SUCCEEDED"} else "SUCCEEDED",
        "start_date": row.get("created_at") or row.get("started_at") or _now_iso(),
        "stop_date": row.get("finished_at") or row.get("created_at"),
        "dataset_key": row.get("dataset_id"),
        "dataset_id": row.get("dataset_id"),
        "run_id": run_id,
        "artifact_uri": row.get("artifact_uri"),
        "training_config": row.get("training_config"),
        "metrics": row.get("metrics"),
        "best_f1": row.get("best_f1"),
        "demo": False,
    }


def _list_local_experiment_runs(*, max_results: int = 15) -> list[dict[str, Any]]:
    from registry.experiment import load_local_runs

    rows = load_local_runs(limit=max_results)
    return [
        _attach_run_artifacts(
            _normalize_execution(_local_run_item(row), include_stages=True, include_sfn_timeline=False)
        )
        for row in rows
    ]


def _get_local_experiment_run(run_id: str) -> dict[str, Any] | None:
    from registry.experiment import load_local_runs

    for row in load_local_runs(limit=100):
        if row.get("run_id") == run_id:
            return _attach_run_artifacts(
                _normalize_execution(_local_run_item(row), include_stages=True, include_sfn_timeline=False)
            )
    summary = _load_run_summary(run_id)
    if not summary:
        return None
    row = {
        "run_id": run_id,
        "created_at": summary.get("generated_at"),
        "finished_at": summary.get("generated_at"),
        "status": summary.get("status", "COMPLETED"),
        "dataset_id": summary.get("dataset_id"),
        "training_config": summary.get("config"),
        "metrics": summary.get("metrics"),
        "artifact_uri": str(REPO_ROOT / "experiments" / "training-runs" / run_id),
    }
    return _attach_run_artifacts(
        _normalize_execution(_local_run_item(row), include_stages=True, include_sfn_timeline=False)
    )


def list_runs(*, max_results: int = 15) -> list[dict[str, Any]]:
    if not is_configured():
        return _list_local_experiment_runs(max_results=max_results)

    store = registry_db.get_store()
    if store is not None and store.config.training_runs_table:
        db_runs = store.list_training_runs(limit=max_results)
        runs: list[dict[str, Any]] = []
        for row in db_runs:
            execution_arn = row.get("step_function_execution_arn") or row.get("execution_arn")
            status = str(row.get("status", "RUNNING")).upper()
            if status in {"COMPLETED", "REGISTERED", "APPROVED", "REJECTED"}:
                status = "SUCCEEDED"
            item = {
                "execution_arn": execution_arn or f"local://training-runs/{row.get('run_id')}",
                "name": row.get("run_id", ""),
                "status": status if status in {"RUNNING", "FAILED", "SUCCEEDED"} else "RUNNING",
                "start_date": row.get("started_at") or row.get("created_at"),
                "stop_date": row.get("finished_at"),
                "dataset_key": row.get("dataset_key"),
                "run_id": row.get("run_id"),
                "dataset_id": row.get("dataset_id"),
                "artifact_uri": row.get("artifact_uri"),
                "training_config": row.get("training_config"),
                "metrics": row.get("metrics"),
                "candidate_model_id": row.get("candidate_model_id"),
                "best_f1": row.get("best_f1"),
                "demo": False,
            }
            if execution_arn:
                try:
                    desc = _sfn_client().describe_execution(executionArn=execution_arn)
                    item["status"] = desc["status"]
                    item["start_date"] = desc["startDate"].isoformat()
                    item["stop_date"] = (
                        desc["stopDate"].isoformat() if desc.get("stopDate") else None
                    )
                except Exception:
                    pass
            runs.append(item)
        return [
            _attach_run_artifacts(
                _normalize_execution(
                    r,
                    include_stages=True,
                    include_sfn_timeline=r.get("status") in {"RUNNING", "FAILED", "SUCCEEDED"},
                )
            )
            for r in runs
        ]

    resp = _sfn_client().list_executions(
        stateMachineArn=RETRAIN_STATE_MACHINE_ARN,
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
    return [
        _attach_run_artifacts(
            _normalize_execution(
                r,
                include_stages=True,
                include_sfn_timeline=r.get("status") in {"RUNNING", "FAILED", "SUCCEEDED"},
            )
        )
        for r in runs
    ]


def get_run(execution_arn: str) -> dict[str, Any] | None:
    if execution_arn.startswith("arn:aws:states:local:demo:"):
        for r in _demo_runs:
            if r["execution_arn"] == execution_arn:
                return _attach_run_artifacts(_normalize_execution(r, include_stages=True, include_sfn_timeline=True))
        return None

    if execution_arn.startswith("local://training-runs/"):
        run_id = execution_arn.rsplit("/", 1)[-1]
        return _get_local_experiment_run(run_id)

    if not is_configured():
        return _get_local_experiment_run(execution_arn)

    try:
        detail = _sfn_client().describe_execution(executionArn=execution_arn)
    except Exception:
        return None

    status = detail["status"]
    current = _infer_current_stage(execution_arn) if status == "RUNNING" else None
    if status == "SUCCEEDED":
        current = "NotifyResult"
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
        "run_id": inp.get("run_id"),
        "approval_id": inp.get("approval_id"),
        "training_config": inp.get("training_config"),
        "demo": False,
        "current_stage": current,
    }
    return _attach_run_artifacts(_normalize_execution(run, include_stages=True, include_sfn_timeline=True))


def get_approval(approval_id: str) -> dict[str, Any] | None:
    store = registry_db.get_store()
    if store is None or not store.config.approval_table:
        return None
    record = store.get_approval_request(approval_id)
    if record is None:
        return None
    record.pop("task_token", None)
    return record


def decide_approval(approval_id: str, *, decision: str, decided_by: str = "admin-ui") -> dict[str, Any]:
    store = registry_db.get_store()
    if store is None or not store.config.approval_table:
        raise RuntimeError("APPROVAL_TABLE is not configured")

    import boto3

    sfn = boto3.client("stepfunctions", region_name=AWS_REGION)
    record = store.get_approval_request(approval_id)
    if record is None:
        raise KeyError(f"Approval '{approval_id}' not found")
    if record.get("status") != "PENDING":
        raise ValueError(f"Approval already {record.get('status')}")

    token = record.get("task_token")
    if not token:
        raise ValueError("Missing task token")

    if decision == "approve":
        sfn.send_task_success(
            taskToken=token,
            output=json.dumps({"decision": "approved", "approval_id": approval_id}),
        )
        status = "APPROVED"
    elif decision == "reject":
        sfn.send_task_failure(
            taskToken=token,
            error="ApprovalRejected",
            cause=f"Rejected by {decided_by}",
        )
        status = "REJECTED"
    else:
        raise ValueError("decision must be approve or reject")

    store.put_approval_request(
        {**record, "status": status, "decided_by": decided_by, "decided_at": _now_iso()}
    )
    return {"approval_id": approval_id, "status": status}
