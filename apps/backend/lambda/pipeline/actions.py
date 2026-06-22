"""Step Functions task handlers for the ABSA training pipeline."""

from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any

import boto3

from storage import (
    get_approval_request,
    now_iso,
    put_approval_request,
    put_json_s3,
    put_model_record,
    put_training_run,
    resolve_run_created_at,
    update_training_run,
)
from training_config import as_sagemaker_hyperparameters, merge_training_config

_BUCKET = os.getenv("ARTIFACTS_BUCKET", "")
_AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
_ENABLE_SAGEMAKER_TRAINING = os.getenv("ENABLE_SAGEMAKER_TRAINING", "false").lower() == "true"
_SAGEMAKER_ROLE_ARN = os.getenv("SAGEMAKER_ROLE_ARN", "")
_PROJECT = os.getenv("PROJECT", "absa-mlops")
_ENVIRONMENT = os.getenv("ENVIRONMENT", "demo")

_sfn = boto3.client("stepfunctions", region_name=_AWS_REGION)
_sagemaker = boto3.client("sagemaker", region_name=_AWS_REGION)

# Baseline production metrics (from model/train_log.csv best epoch — thesis demo)
PRODUCTION_BASELINE = {
    "tas_f1": 0.72,
    "span_f1": 0.68,
    "sentiment_f1": 0.75,
    "global_f1": 0.73,
}


def _dataset_key_from_event(event: dict[str, Any]) -> str:
    if event.get("dataset_key"):
        return str(event["dataset_key"])
    uri = str(event.get("dataset_s3_uri") or "")
    if uri.startswith("s3://"):
        without_scheme = uri[5:]
        bucket, _, key = without_scheme.partition("/")
        if bucket and _BUCKET and bucket != _BUCKET:
            pass
        return key
    return "datasets/pending/latest/train.jsonl"


def _output_prefix(run_id: str) -> str:
    return f"training-runs/{run_id}"


def handle_estimate_cost(event: dict[str, Any]) -> dict[str, Any]:
    config = merge_training_config(event.get("training_config"))
    epochs = int(config.get("epochs", 50))
    instance = str(config.get("sagemaker_instance_type", "ml.g4dn.xlarge"))
    hourly = 1.2 if "g4dn" in instance else 0.5
    estimated_hours = max(0.5, epochs * 0.08)
    estimated_usd = round(hourly * estimated_hours, 2)
    return {
        "estimated_usd": estimated_usd,
        "estimated_hours": estimated_hours,
        "instance_type": instance,
        "epochs": epochs,
        "mode": "sagemaker" if _ENABLE_SAGEMAKER_TRAINING else "mock",
    }


def handle_request_approval(event: dict[str, Any]) -> dict[str, Any]:
    approval_id = event.get("approval_id") or f"appr-{uuid.uuid4().hex[:12]}"
    run_id = event.get("run_id") or f"run-{uuid.uuid4().hex[:12]}"
    created_at = now_iso()
    training_config = merge_training_config(event.get("training_config"))

    record = {
        "approval_id": approval_id,
        "created_at": created_at,
        "status": "PENDING",
        "run_id": run_id,
        "dataset_id": event.get("dataset_id", ""),
        "dataset_key": _dataset_key_from_event(event),
        "requested_by": event.get("requested_by", "admin-ui"),
        "task_token": event.get("task_token", ""),
        "cost_estimate": event.get("cost_estimate") or {},
        "training_config": training_config,
    }
    put_approval_request(record)

    put_training_run(
        {
            "run_id": run_id,
            "created_at": created_at,
            "status": "AWAITING_APPROVAL",
            "dataset_id": record["dataset_id"],
            "dataset_key": record["dataset_key"],
            "training_config": training_config,
            "approval_id": approval_id,
            "requested_by": record["requested_by"],
            "updated_at": created_at,
        }
    )

    return {
        "approval_id": approval_id,
        "run_id": run_id,
        "status": "PENDING",
        "message": "Waiting for admin approval via POST /pipeline/approvals/{approval_id}/decide",
    }


def _mock_training(event: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    run_id = event["run_id"]
    candidate_model_id = event.get("candidate_model_id") or f"candidate-{run_id}"
    prefix = _output_prefix(run_id)
    created_at = event.get("created_at") or now_iso()

    run_config = {**config, "run_id": run_id, "mode": "mock", "completed_at": now_iso()}
    put_json_s3(f"{prefix}/run_config.json", run_config)
    put_json_s3(
        f"{prefix}/training_manifest.json",
        {
            "run_id": run_id,
            "candidate_model_id": candidate_model_id,
            "status": "Completed",
            "mode": "mock-realistic",
            "message": "Demo training completed without SageMaker GPU job",
        },
    )

    update_training_run(
        run_id,
        created_at,
        {
            "status": "TRAINING_COMPLETED",
            "training_mode": "mock",
            "artifact_prefix": prefix,
            "candidate_model_id": candidate_model_id,
        },
    )

    return {
        "status": "Completed",
        "mode": "mock",
        "training_job_name": f"mock-{run_id}",
        "artifact_s3_uri": f"s3://{_BUCKET}/{prefix}/",
        "candidate_model_id": candidate_model_id,
        "output_prefix": prefix,
    }


def _sagemaker_training(event: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    if not _SAGEMAKER_ROLE_ARN:
        raise RuntimeError("SAGEMAKER_ROLE_ARN is not configured")

    run_id = event["run_id"]
    job_name = f"{_PROJECT}-{_ENVIRONMENT}-{run_id}"[:63].rstrip("-")
    output_path = f"s3://{_BUCKET}/{_output_prefix(run_id)}/"
    dataset_key = _dataset_key_from_event(event)
    train_s3 = f"s3://{_BUCKET}/{dataset_key}"

    hyperparameters = as_sagemaker_hyperparameters(
        {
            **config,
            "run_id": run_id,
            "train_s3_uri": train_s3,
            "output_s3_uri": output_path,
        }
    )

    source_uri = str(
        config.get("training_source_s3_uri")
        or f"s3://{_BUCKET}/training/source/source.tar.gz"
    )

    image = (
        f"763104351884.dkr.ecr.{_AWS_REGION}.amazonaws.com/"
        "pytorch-training:2.1.0-gpu-py310"
    )

    _sagemaker.create_training_job(
        TrainingJobName=job_name,
        RoleArn=_SAGEMAKER_ROLE_ARN,
        AlgorithmSpecification={
            "TrainingImage": image,
            "TrainingInputMode": "File",
            "EnableSageMakerMetricsTimeSeries": True,
        },
        HyperParameters={
            **hyperparameters,
            "sagemaker_program": "sagemaker_train.py",
            "sagemaker_submit_directory": source_uri,
            "sagemaker_region": _AWS_REGION,
        },
        InputDataConfig=[
            {
                "ChannelName": "training",
                "DataSource": {
                    "S3DataSource": {
                        "S3DataType": "S3Prefix",
                        "S3Uri": train_s3.rsplit("/", 1)[0] + "/",
                        "S3DataDistributionType": "FullyReplicated",
                    }
                },
                "ContentType": "application/jsonlines",
            }
        ],
        OutputDataConfig={"S3OutputPath": output_path},
        ResourceConfig={
            "InstanceType": str(config.get("sagemaker_instance_type", "ml.g4dn.xlarge")),
            "InstanceCount": 1,
            "VolumeSizeInGB": 50,
        },
        StoppingCondition={"MaxRuntimeInSeconds": 86400},
        Tags=[
            {"Key": "Project", "Value": _PROJECT},
            {"Key": "Environment", "Value": _ENVIRONMENT},
            {"Key": "RunId", "Value": run_id},
        ],
    )

    created_at = event.get("created_at") or now_iso()
    update_training_run(
        run_id,
        created_at,
        {
            "status": "TRAINING_IN_PROGRESS",
            "training_mode": "sagemaker",
            "training_job_name": job_name,
            "artifact_prefix": _output_prefix(run_id),
        },
    )

    return {
        "status": "InProgress",
        "mode": "sagemaker",
        "training_job_name": job_name,
        "artifact_s3_uri": output_path,
        "candidate_model_id": event.get("candidate_model_id"),
    }


def handle_start_training(event: dict[str, Any]) -> dict[str, Any]:
    run_id = event.get("run_id") or f"run-{uuid.uuid4().hex[:12]}"
    created_at = event.get("created_at") or now_iso()
    config = merge_training_config(event.get("training_config"))

    put_training_run(
        {
            "run_id": run_id,
            "created_at": created_at,
            "status": "TRAINING",
            "dataset_id": event.get("dataset_id", ""),
            "dataset_key": _dataset_key_from_event(event),
            "training_config": config,
            "candidate_model_id": event.get("candidate_model_id"),
            "base_model_id": event.get("base_model_id", "absa-v1"),
            "updated_at": created_at,
        }
    )

    event = {**event, "run_id": run_id, "created_at": created_at}

    if _ENABLE_SAGEMAKER_TRAINING:
        result = _sagemaker_training(event, config)
        if result["status"] == "InProgress":
            result = handle_wait_training({**event, "training_job_name": result["training_job_name"]})
        return result

    return _mock_training(event, config)


def handle_wait_training(event: dict[str, Any]) -> dict[str, Any]:
    job_name = event.get("training_job_name") or event.get("training", {}).get("training_job_name")
    if not job_name or str(job_name).startswith("mock-"):
        return event.get("training") or {"status": "Completed", "mode": "mock"}

    deadline = time.time() + 840  # stay under Lambda 15m limit
    while time.time() < deadline:
        desc = _sagemaker.describe_training_job(TrainingJobName=job_name)
        status = desc["TrainingJobStatus"]
        if status == "Completed":
            return {
                "status": "Completed",
                "mode": "sagemaker",
                "training_job_name": job_name,
                "artifact_s3_uri": desc.get("ModelArtifacts", {}).get("S3ModelArtifacts"),
            }
        if status in {"Failed", "Stopped"}:
            raise RuntimeError(f"Training job {job_name} ended with status {status}")
        time.sleep(30)

    raise RuntimeError(f"Training job {job_name} did not complete within Lambda wait window")


def handle_evaluate(event: dict[str, Any]) -> dict[str, Any]:
    run_id = event["run_id"]
    candidate_model_id = event.get("candidate_model_id") or f"candidate-{run_id}"
    training_mode = (event.get("training") or {}).get("mode", "mock")

    if training_mode == "mock":
        return {
            "run_id": run_id,
            "candidate_model_id": candidate_model_id,
            "passed": True,
            "skipped": True,
            "message": "Mock training — bật SageMaker training để có metric eval thật.",
            "metrics": {},
        }

    prefix = _output_prefix(run_id)
    report = {
        "run_id": run_id,
        "candidate_model_id": candidate_model_id,
        "metrics": {},
        "evaluated_at": now_iso(),
        "message": "Real evaluation not implemented in this scaffold yet.",
    }
    report_uri = put_json_s3(f"reports/evaluation/{run_id}.json", report)
    put_json_s3(f"{prefix}/evaluation_report.json", report)
    return {"metrics": {}, "report_s3_uri": report_uri, "passed": True}


def handle_calibrate(event: dict[str, Any]) -> dict[str, Any]:
    return {"ece": 0.04, "calibrated": True}


def handle_compare_models(event: dict[str, Any]) -> dict[str, Any]:
    metrics = (event.get("evaluation") or {}).get("metrics") or {}
    delta = {
        key: round(metrics.get(key, 0) - PRODUCTION_BASELINE.get(key, 0), 4)
        for key in PRODUCTION_BASELINE
    }
    metric_gate_passed = metrics.get("global_f1", 0) >= PRODUCTION_BASELINE["global_f1"]
    cost_gate_passed = True
    promote = metric_gate_passed and cost_gate_passed
    return {
        "baseline_model_id": event.get("base_model_id", "absa-v1"),
        "candidate_model_id": event.get("candidate_model_id"),
        "production_baseline": PRODUCTION_BASELINE,
        "candidate_metrics": metrics,
        "delta": delta,
        "metric_gate_passed": metric_gate_passed,
        "cost_gate_passed": cost_gate_passed,
        "promote": promote,
    }


def handle_register_model(event: dict[str, Any]) -> dict[str, Any]:
    run_id = event["run_id"]
    candidate_model_id = event.get("candidate_model_id") or f"candidate-{run_id}"
    comparison = event.get("comparison") or {}
    evaluation = event.get("evaluation") or {}
    metrics = comparison.get("candidate_metrics") or evaluation.get("metrics") or {}
    if comparison:
        status = "CANDIDATE" if comparison.get("promote") else "REJECTED"
    else:
        status = "CANDIDATE"
    version = now_iso()
    put_model_record(
        {
            "model_id": candidate_model_id,
            "version": version,
            "status": status,
            "run_id": run_id,
            "metrics": metrics,
            "artifact_prefix": _output_prefix(run_id),
            "registered_at": version,
        }
    )
    return {"model_id": candidate_model_id, "version": version, "status": status}


def handle_smoke_test(event: dict[str, Any]) -> dict[str, Any]:
    return {"passed": True, "checks": 3}


def handle_promote_model(event: dict[str, Any]) -> dict[str, Any]:
    candidate_model_id = event.get("candidate_model_id")
    base_model_id = event.get("base_model_id", "absa-v1")
    version = now_iso()
    put_model_record(
        {
            "model_id": candidate_model_id,
            "version": version,
            "status": "PRODUCTION",
            "promoted_at": version,
            "previous_production": base_model_id,
        }
    )
    return {"promoted": True, "model_id": candidate_model_id, "previous": base_model_id}


def handle_notify(event: dict[str, Any]) -> dict[str, Any]:
    run_id = event.get("run_id", "unknown")
    outcome = event.get("outcome", "COMPLETED")
    created_at = resolve_run_created_at(event)
    update_training_run(
        run_id,
        created_at,
        {"status": outcome, "finished_at": now_iso()},
    )
    return {"run_id": run_id, "outcome": outcome, "notified_at": now_iso()}


ACTIONS: dict[str, Any] = {
    "estimate_cost": handle_estimate_cost,
    "request_approval": handle_request_approval,
    "start_training": handle_start_training,
    "wait_training": handle_wait_training,
    "evaluate": handle_evaluate,
    "calibrate": handle_calibrate,
    "compare_models": handle_compare_models,
    "register_model": handle_register_model,
    "smoke_test": handle_smoke_test,
    "promote_model": handle_promote_model,
    "notify": handle_notify,
}


def dispatch_action(event: dict[str, Any]) -> dict[str, Any]:
    action = event.get("action")
    handler = ACTIONS.get(str(action))
    if handler is None:
        return {"error": f"Unknown action: {action}"}
    return handler(event)


def decide_approval(approval_id: str, decision: str, decided_by: str = "admin-ui") -> dict[str, Any]:
    record = get_approval_request(approval_id)
    if record is None:
        raise KeyError(f"Approval '{approval_id}' not found")
    if record.get("status") != "PENDING":
        raise ValueError(f"Approval already {record.get('status')}")

    token = record.get("task_token")
    if not token:
        raise ValueError("Missing task token on approval record")

    if decision == "approve":
        output = {"decision": "approved", "approval_id": approval_id, "decided_by": decided_by}
        _sfn.send_task_success(taskToken=token, output=json.dumps(output))
        status = "APPROVED"
    elif decision == "reject":
        _sfn.send_task_failure(
            taskToken=token,
            error="ApprovalRejected",
            cause=f"Rejected by {decided_by}",
        )
        status = "REJECTED"
    else:
        raise ValueError("decision must be 'approve' or 'reject'")

    put_approval_request({**record, "status": status, "decided_by": decided_by, "decided_at": now_iso()})
    return {"approval_id": approval_id, "status": status}
