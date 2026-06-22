"""Canonical S3 key prefixes for ABSA MLOps artifacts."""

from __future__ import annotations

DATASETS_PREFIX = "datasets"
MODELS_PREFIX = "models"
REPORTS_PREFIX = "reports"
TRAINING_RUNS_PREFIX = "training-runs"

# Standard filenames inside training-runs/{run_id}/
RUN_ARTIFACT_FILES = (
    "run_config.json",
    "train_log.csv",
    "summary.json",
    "classification_report.json",
    "learning_curve.png",
    "confusion_matrix.png",
)


def training_run_prefix(run_id: str) -> str:
    return f"{TRAINING_RUNS_PREFIX}/{run_id}"


def training_run_uri(bucket: str, run_id: str) -> str:
    return f"s3://{bucket}/{training_run_prefix(run_id)}/"


def training_run_key(run_id: str, filename: str) -> str:
    return f"{training_run_prefix(run_id)}/{filename}"


def model_candidate_prefix(run_id: str) -> str:
    """Weights/checkpoints promoted from a training run."""
    return f"{MODELS_PREFIX}/candidates/{run_id}"


def evaluation_report_key(run_id: str) -> str:
    return f"{REPORTS_PREFIX}/evaluation/{run_id}.json"
