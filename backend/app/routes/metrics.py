from fastapi import APIRouter, HTTPException

from backend.app.services import inference as inference_service
from backend.app.services import metrics as metrics_service
from backend.app.services import runtime as runtime_service

router = APIRouter(tags=["metrics"])


@router.get("/metrics/runtime")
async def runtime_metrics():
    try:
        inference_service.get_model_bundle()
        model_ready = True
    except RuntimeError:
        model_ready = False
    return runtime_service.get_runtime_stats(model_ready)


@router.get("/metrics/models")
async def list_models():
    return {"models": metrics_service.list_models()}


@router.get("/metrics/models/{version}")
async def get_model_metrics(version: str):
    evaluation = metrics_service.get_model_evaluation(version)
    if not evaluation:
        raise HTTPException(status_code=404, detail=f"Model '{version}' not found")
    return evaluation


@router.get("/metrics/training/history")
async def training_history():
    return {"history": metrics_service.get_training_history()}
