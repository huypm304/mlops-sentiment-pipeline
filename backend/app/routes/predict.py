from fastapi import APIRouter, HTTPException

from backend.app.schemas.predict import OpinionOut, PredictRequest, PredictResponse
from backend.app.services import drift as drift_service
from backend.app.services import inference as inference_service
from backend.app.services import runtime as runtime_service

router = APIRouter(tags=["predict"])


@router.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest) -> PredictResponse:
    try:
        raw = inference_service.run_predict(request.text)
    except RuntimeError as exc:
        runtime_service.record_predict(0, error=True)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        runtime_service.record_predict(0, error=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    runtime_service.record_predict(raw["latency_ms"], error=False)
    drift_service.record_inference(
        global_sentiment=raw["global_sentiment"],
        global_confidence=float(raw.get("global_confidence", 0)),
        opinions=raw["opinions"],
        latency_ms=raw["latency_ms"],
    )

    opinions = [
        OpinionOut(
            target=o["target"],
            aspect=o["aspect"],
            sentiment=o["sentiment"],
            confidence=o["confidence"],
            start=o.get("start"),
            end=o.get("end"),
        )
        for o in raw["opinions"]
    ]

    return PredictResponse(
        opinions=opinions,
        global_sentiment=raw["global_sentiment"],
        global_confidence=raw.get("global_confidence", 0.0),
        latency_ms=raw["latency_ms"],
    )


@router.get("/health")
async def health():
    try:
        inference_service.get_model_bundle()
        model_ready = True
        status = "ok"
        model = "loaded"
    except RuntimeError:
        model_ready = False
        status = "loading"
        model = "not_ready"
    return {
        "status": status,
        "model": model,
        **runtime_service.get_runtime_stats(model_ready),
    }
