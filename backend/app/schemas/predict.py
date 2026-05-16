from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Vietnamese review text")


class OpinionOut(BaseModel):
    target: str
    aspect: str
    sentiment: str
    confidence: float
    start: int | None = None
    end: int | None = None


class PredictResponse(BaseModel):
    opinions: list[OpinionOut]
    global_sentiment: str
    global_confidence: float = 0.0
    latency_ms: int
