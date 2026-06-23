"""Run lineage — code version, data URI, training config snapshot."""

from __future__ import annotations

import os
from typing import Any

_BUCKET = os.getenv("ARTIFACTS_BUCKET", "")
_TRAINING_CODE_VERSION = os.getenv("TRAINING_CODE_VERSION", "absa-train-v1")
_DEFAULT_SOURCE_KEY = "training/source/source.tar.gz"


def training_source_uri(training_config: dict[str, Any] | None = None) -> str:
    if training_config and training_config.get("training_source_s3_uri"):
        return str(training_config["training_source_s3_uri"])
    if _BUCKET:
        return f"s3://{_BUCKET}/{_DEFAULT_SOURCE_KEY}"
    return ""


def build_run_lineage(
    *,
    dataset_id: str,
    dataset_key: str,
    base_model_id: str,
    candidate_model_id: str,
    training_config: dict[str, Any],
) -> dict[str, Any]:
    return {
        "code_version": _TRAINING_CODE_VERSION,
        "training_source_uri": training_source_uri(training_config),
        "dataset_id": dataset_id,
        "dataset_key": dataset_key,
        "dataset_s3_uri": f"s3://{_BUCKET}/{dataset_key}" if _BUCKET else "",
        "base_model_id": base_model_id,
        "candidate_model_id": candidate_model_id,
        "training_config": training_config,
    }
