from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Vietnamese review text")


class OpinionOut(BaseModel):
    target: str
    aspect: str
    sentiment: str
    confidence: float
    raw_confidence: float | None = None
    calibrated_confidence: float | None = None
    start: int | None = None
    end: int | None = None


class PredictResponse(BaseModel):
    opinions: list[OpinionOut]
    global_sentiment: str
    global_confidence: float = 0.0
    global_raw_confidence: float | None = None
    model_version: str | None = None
    latency_ms: int
