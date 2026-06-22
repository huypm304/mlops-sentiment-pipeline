"""Environment-driven table names for the DynamoDB registry."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RegistryConfig:
    aws_region: str
    artifacts_bucket: str
    datasets_table: str
    training_runs_table: str
    models_table: str
    predictions_table: str
    monitoring_table: str
    approval_table: str
    review_queue_table: str

    @property
    def enabled(self) -> bool:
        return bool(
            self.datasets_table
            or self.training_runs_table
            or self.models_table
            or self.predictions_table
            or self.monitoring_table
            or self.approval_table
            or self.review_queue_table
        )


def load_config() -> RegistryConfig:
    return RegistryConfig(
        aws_region=os.getenv("AWS_REGION", "ap-southeast-1"),
        artifacts_bucket=os.getenv("ARTIFACTS_BUCKET", "").strip(),
        datasets_table=os.getenv("DATASETS_TABLE", "").strip(),
        training_runs_table=os.getenv("TRAINING_RUNS_TABLE", "").strip(),
        models_table=os.getenv("MODELS_TABLE", "").strip(),
        predictions_table=os.getenv("PREDICTIONS_TABLE", "").strip(),
        monitoring_table=os.getenv("MONITORING_TABLE", "").strip(),
        approval_table=os.getenv("APPROVAL_TABLE", "").strip(),
        review_queue_table=os.getenv("REVIEW_QUEUE_TABLE", "").strip(),
    )
