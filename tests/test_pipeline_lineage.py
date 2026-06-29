"""Tests for pipeline run lineage helpers."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "backend" / "lambda" / "pipeline"))

os.environ.setdefault("ARTIFACTS_BUCKET", "absa-mlops-demo-artifacts")
os.environ.setdefault("TRAINING_CODE_VERSION", "absa-train-v1")

from lineage import build_run_lineage, training_source_uri  # noqa: E402


def test_training_source_uri_from_config():
    uri = training_source_uri({"training_source_s3_uri": "s3://bucket/custom/source.tar.gz"})
    assert uri == "s3://bucket/custom/source.tar.gz"


def test_build_run_lineage_includes_three_layers():
    lineage = build_run_lineage(
        dataset_id="dataset-v2",
        dataset_key="datasets/pending/dataset-v2/train.jsonl",
        base_model_id="absa-v2b",
        candidate_model_id="candidate-run-1",
        training_config={"epochs": 50, "batch_size": 24},
    )
    assert lineage["code_version"] == "absa-train-v1"
    assert "training/source" in lineage["training_source_uri"]
    assert lineage["dataset_id"] == "dataset-v2"
    assert lineage["dataset_s3_uri"].startswith("s3://")
    assert lineage["training_config"]["epochs"] == 50
