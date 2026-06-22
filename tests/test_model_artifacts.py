"""Tests for S3-backed model artifact parsing."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "backend"))

from registry.model_artifacts import (
    build_evaluation_payload,
    build_training_history,
    metrics_summary_from_train_log,
)

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "model"
CONFIG_DIR = ROOT / "ml" / "configs"


def test_metrics_summary_from_local_train_log():
    text = (MODEL_DIR / "train_log.csv").read_text(encoding="utf-8")
    metrics = metrics_summary_from_train_log(text)
    assert metrics["global_f1"] > 0.8
    assert metrics["span_f1"] > 0.8


def test_build_evaluation_from_local_artifacts():
    train_log = (MODEL_DIR / "train_log.csv").read_text(encoding="utf-8")
    run_config = (CONFIG_DIR / "run_config.json").read_text(encoding="utf-8")
    confusion = (MODEL_DIR / "confusion_matrices.jsonl").read_text(encoding="utf-8")

    payload = build_evaluation_payload(
        model_id="absa-v2b",
        train_log_text=train_log,
        run_config_text=run_config,
        confusion_text=confusion,
        artifact_prefix="models/v1",
        registry_row={
            "encoder": "vinai/phobert-base",
            "status": "PRODUCTION",
            "registered_at": "2026-06-14T08:00:00Z",
            "dataset_id": "dataset-v1",
            "_bucket": "absa-mlops-demo-artifacts",
        },
    )

    assert payload is not None
    assert payload["training"]["encoder"] == "vinai/phobert-base"
    assert payload["scores"]["global_f1"] > 0.8
    assert payload["confusion_matrix"]["matrix"][0][0] >= 0
    assert payload["artifacts"]["train_log"].endswith("models/v1/train_log.csv")
    assert len(build_training_history(train_log)) > 10
