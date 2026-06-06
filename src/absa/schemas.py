"""Pydantic schemas for FastAPI inference API."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    text: str = Field(..., description="Input Vietnamese review text")


class BatchPredictRequest(BaseModel):
    texts: list[str] = Field(..., description="List of input texts")


class OpinionPrediction(BaseModel):
    target: str
    aspect: str
    sentiment: str
    sentiment_id: int
    confidence: float
    raw_confidence: float
    calibrated_confidence: float
    start: Optional[int] = None
    end: Optional[int] = None
    probs: dict[str, float]
    need_review: bool = False
    review_reasons: list[str] = Field(default_factory=list)


class PredictResponse(BaseModel):
    text: str
    opinions: list[OpinionPrediction]
    global_sentiment: str
    global_sentiment_id: int
    global_confidence: float
    global_raw_confidence: float
    global_probs: dict[str, float]
    model_version: str
    need_review: bool
    review_reasons: list[str]
    guardrail_status: str
    latency_ms: Optional[int] = None


class BatchPredictResponse(BaseModel):
    results: list[PredictResponse]
    total: int
    latency_ms: Optional[int] = None


class ModelInfoResponse(BaseModel):
    model_version: str
    backbone: str
    aspects: list[str]
    sentiment_labels: dict[str, int]
    max_ops: int
    max_len: int
    status: str


class HealthResponse(BaseModel):
    status: str
    model: str
    model_version: Optional[str] = None
    device: Optional[str] = None
