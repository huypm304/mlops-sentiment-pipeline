"""Tests for pipeline training config helpers."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "backend" / "lambda" / "pipeline"))

from training_config import as_sagemaker_hyperparameters, merge_training_config  # noqa: E402


def test_merge_training_config_includes_lambda_cons_and_contrast():
    merged = merge_training_config({"lambda_cons": 0.05, "lambda_contrast": 0.2})
    assert merged["lambda_cons"] == 0.05
    assert merged["lambda_contrast"] == 0.2
    assert merged["epochs"] == 50


def test_sagemaker_hyperparameters_exclude_infra_keys():
    config = merge_training_config(None)
    hp = as_sagemaker_hyperparameters({**config, "run_id": "run-1"})
    assert "run_id" not in hp
    assert "training_source_s3_uri" not in hp
    assert hp["lambda_cons"] == "0.03"
    assert hp["lambda_contrast"] == "0.1"
    assert hp["epochs"] == "50"
