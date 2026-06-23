"""Default and merged training hyperparameters for pipeline runs."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

_DEFAULT_PATH = Path(__file__).with_name("default_training_config.json")

with _DEFAULT_PATH.open(encoding="utf-8") as handle:
    DEFAULT_TRAINING_CONFIG: dict[str, Any] = json.load(handle)

NUMERIC_KEYS = {
    "seed",
    "max_len",
    "epochs",
    "patience",
    "phase1_epochs",
    "max_ops",
    "batch_size",
    "eval_batch_size",
    "grad_accum_steps",
    "lr_backbone",
    "lr_heads",
    "lambda_bio",
    "lambda_sent",
    "lambda_global",
    "lambda_cons",
    "lambda_contrast",
    "contrast_sampler_weight",
    "lbtw_ema_decay",
    "lbtw_min_factor",
    "lbtw_max_factor",
    "pred_span_ratio",
}


def merge_training_config(overrides: dict[str, Any] | None) -> dict[str, Any]:
    merged = deepcopy(DEFAULT_TRAINING_CONFIG)
    if not overrides:
        return merged
    for key, value in overrides.items():
        if value is None:
            continue
        if key in NUMERIC_KEYS:
            merged[key] = float(value) if isinstance(value, (int, float, str)) else value
        else:
            merged[key] = value
    return merged


def as_sagemaker_hyperparameters(config: dict[str, Any]) -> dict[str, str]:
    """SageMaker HyperParameters must be string values."""
    return {str(key): str(value) for key, value in config.items()}
