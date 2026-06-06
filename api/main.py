"""FastAPI inference API for ABSA — thesis/SageMaker deployment surface.

Model is loaded once at startup via lifespan event.
All endpoints share the same bundle; no per-request model loading.

Usage:
    export ABSA_MODEL_DIR=final_artifacts/model
    export ABSA_DEVICE=cpu          # or cuda
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

Environment variables:
    ABSA_MODEL_DIR  - path to model directory (default: final_artifacts/model)
    ABSA_DEVICE     - cpu or cuda (default: auto-detect)
"""

from __future__ import annotations

import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.absa.inference import load_model, predict_one, predict_batch
from src.absa.labels import ASPECTS, SENT_LABEL2ID
from src.absa.schemas import (
    BatchPredictRequest,
    BatchPredictResponse,
    HealthResponse,
    ModelInfoResponse,
    PredictRequest,
    PredictResponse,
    OpinionPrediction,
)

# ---------------------------------------------------------------------------
# Global state — loaded once at startup
# ---------------------------------------------------------------------------
_bundle: dict[str, Any] | None = None
_startup_time: float = time.time()
_request_count: int = 0
_latency_samples: list[int] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _bundle
    model_dir = Path(os.environ.get("ABSA_MODEL_DIR", "final_artifacts/model"))
    device = os.environ.get("ABSA_DEVICE", None)
    print(f"[ABSA API] Loading model from {model_dir} ...")
    try:
        _bundle = load_model(model_dir, device=device, strict=True)
        print(f"[ABSA API] Model loaded: {_bundle['model_version']} on {_bundle['device']}")
    except Exception as exc:
        print(f"[ABSA API] WARNING: model not loaded at startup: {exc}")
        _bundle = None
    yield
    # Shutdown
    _bundle = None
    print("[ABSA API] Shutdown complete")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="ABSA Inference API",
    description="Vietnamese Aspect-Based Sentiment Analysis — thesis deployment API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_bundle() -> dict[str, Any]:
    if _bundle is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Check ABSA_MODEL_DIR.")
    return _bundle


def _to_opinion_prediction(op: dict[str, Any]) -> OpinionPrediction:
    return OpinionPrediction(
        target=op.get("target", ""),
        aspect=op.get("aspect", ""),
        sentiment=op.get("sentiment", "NEU"),
        sentiment_id=op.get("sentiment_id", 2),
        confidence=float(op.get("confidence", 0.0)),
        raw_confidence=float(op.get("raw_confidence", 0.0)),
        calibrated_confidence=float(op.get("calibrated_confidence", 0.0)),
        start=op.get("start"),
        end=op.get("end"),
        probs=op.get("probs", {"NEG": 0.0, "POS": 0.0, "NEU": 1.0}),
        need_review=op.get("need_review", False),
        review_reasons=op.get("review_reasons", []),
    )


def _to_predict_response(raw: dict[str, Any]) -> PredictResponse:
    return PredictResponse(
        text=raw.get("text", ""),
        opinions=[_to_opinion_prediction(op) for op in raw.get("opinions", [])],
        global_sentiment=raw.get("global_sentiment", "NEU"),
        global_sentiment_id=raw.get("global_sentiment_id", 2),
        global_confidence=float(raw.get("global_confidence", 0.0)),
        global_raw_confidence=float(raw.get("global_raw_confidence", 0.0)),
        global_probs=raw.get("global_probs", {"NEG": 0.0, "POS": 0.0, "NEU": 1.0}),
        model_version=str(raw.get("model_version", "absa-v2b")),
        need_review=bool(raw.get("need_review", False)),
        review_reasons=list(raw.get("review_reasons", [])),
        guardrail_status=str(raw.get("guardrail_status", "PASS")),
        latency_ms=raw.get("latency_ms"),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health():
    global _bundle
    model_ready = _bundle is not None
    return HealthResponse(
        status="ok" if model_ready else "loading",
        model="loaded" if model_ready else "not_ready",
        model_version=_bundle.get("model_version") if model_ready else None,
        device=str(_bundle["device"]) if model_ready else None,
    )


@app.get("/model-info", response_model=ModelInfoResponse)
async def model_info():
    bundle = _get_bundle()
    return ModelInfoResponse(
        model_version=bundle.get("model_version", "absa-v2b"),
        backbone=bundle.get("model_name", "Fsoft-AIC/videberta-base"),
        aspects=ASPECTS,
        sentiment_labels=SENT_LABEL2ID,
        max_ops=bundle.get("max_ops", 6),
        max_len=bundle.get("max_len", 192),
        status="ready",
    )


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    global _request_count, _latency_samples
    bundle = _get_bundle()

    if not request.text.strip():
        raise HTTPException(status_code=422, detail="text must not be empty")

    try:
        raw = predict_one(request.text, bundle)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    _request_count += 1
    if raw.get("latency_ms") is not None:
        _latency_samples.append(raw["latency_ms"])
        if len(_latency_samples) > 1000:
            _latency_samples = _latency_samples[-1000:]

    return _to_predict_response(raw)


@app.post("/predict-batch", response_model=BatchPredictResponse)
async def predict_batch_endpoint(request: BatchPredictRequest):
    global _request_count, _latency_samples
    bundle = _get_bundle()

    if not request.texts:
        raise HTTPException(status_code=422, detail="texts must not be empty")
    if len(request.texts) > 32:
        raise HTTPException(status_code=422, detail="Maximum 32 texts per batch request")

    started = time.perf_counter()
    try:
        results_raw = predict_batch(request.texts, bundle)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    total_ms = int((time.perf_counter() - started) * 1000)
    _request_count += len(request.texts)

    return BatchPredictResponse(
        results=[_to_predict_response(r) for r in results_raw],
        total=len(results_raw),
        latency_ms=total_ms,
    )


@app.get("/metrics/demo")
async def metrics_demo():
    """Return simple runtime stats for monitoring dashboards."""
    uptime_s = int(time.time() - _startup_time)
    avg_latency = (
        sum(_latency_samples) / len(_latency_samples)
        if _latency_samples else 0.0
    )
    return {
        "uptime_seconds": uptime_s,
        "total_requests": _request_count,
        "avg_latency_ms": round(avg_latency, 1),
        "p95_latency_ms": sorted(_latency_samples)[int(0.95 * len(_latency_samples))] if len(_latency_samples) >= 20 else None,
        "model_ready": _bundle is not None,
    }
