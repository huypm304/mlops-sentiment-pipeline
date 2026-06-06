"""Pipeline trigger / approval schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TrainingConfig(BaseModel):
    model_name: str = "Fsoft-AIC/videberta-base"
    epochs: int = 50
    patience: int = 8
    batch_size: int = 24
    lr_backbone: float = 8e-6
    lr_heads: float = 3e-5
    lambda_bio: float = 1.1
    lambda_sent: float = 1.4
    lambda_global: float = 0.2
    lambda_cons: float = 0.0
    lambda_contrast: float = 0.0
    contrast_sampler_weight: float = 1.2
    sagemaker_instance_type: str = "ml.g4dn.xlarge"


class TriggerRequest(BaseModel):
    dataset_id: str = Field(description="Dataset uploaded in step 1 (train + dev bundle)")
    requested_by: str = "admin-ui"
    base_model_id: str = "absa-v1"
    training_config: dict[str, Any] | None = None


class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(description="approve or reject")
    decided_by: str = "admin-ui"
