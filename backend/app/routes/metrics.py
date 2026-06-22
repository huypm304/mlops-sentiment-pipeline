from fastapi import APIRouter, HTTPException

from backend.app.config.guardrails import DEFAULT_GUARDRAIL_CONFIG
from backend.app.config.settings import (
    ARTIFACTS_BUCKET,
    MODEL_DIR,
    PIPELINE_DEMO_MODE,
    RETRAIN_STATE_MACHINE_ARN,
)
from backend.app.services import analytics as analytics_service
from backend.app.services import drift as drift_service
from backend.app.services import inference as inference_service
from backend.app.services import metrics as metrics_service
from backend.app.services import platform_context as platform_context_service
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


@router.get("/metrics/analytics")
async def analytics_dashboard(hours: int = 24, model: str | None = None):
    return analytics_service.get_analytics(hours=hours, model_version=model)


@router.get("/metrics/review-queue")
async def review_queue(limit: int = 50):
    return analytics_service.get_review_queue(limit=limit)


@router.get("/metrics/platform/context")
async def platform_context():
    try:
        inference_service.get_model_bundle()
        model_ready = True
    except RuntimeError:
        model_ready = False
    return platform_context_service.get_platform_context(model_ready=model_ready)


@router.get("/metrics/platform")
async def platform_settings():
    try:
        inference_service.get_model_bundle()
        model_ready = True
    except RuntimeError:
        model_ready = False
    stats = runtime_service.get_runtime_stats(model_ready)
    models = metrics_service.list_models()
    return {
        "environment": "demo",
        "model_dir": str(MODEL_DIR),
        "production_model": models[0]["version"] if models else None,
        "endpoint_status": "ready" if model_ready else "disabled",
        "artifacts_bucket": ARTIFACTS_BUCKET or None,
        "retrain_state_machine": RETRAIN_STATE_MACHINE_ARN or None,
        "pipeline_demo_mode": PIPELINE_DEMO_MODE,
        "drift_threshold": drift_service.DRIFT_THRESHOLD,
        "guardrails": DEFAULT_GUARDRAIL_CONFIG.as_dict(),
        "request_volume_total": stats["request_volume_total"],
        "uptime_seconds": stats["uptime_seconds"],
    }


@router.get("/metrics/monitoring")
async def monitoring_dashboard():
    """Runtime ops + model/data drift vs training baseline."""
    from backend.app.services import registry_db

    try:
        inference_service.get_model_bundle()
        model_ready = True
    except RuntimeError:
        model_ready = False

    payload = {
        **runtime_service.get_runtime_stats(model_ready),
        "drift": drift_service.get_drift_report(),
    }
    store = registry_db.get_store()
    if store is not None and store.config.monitoring_table:
        snapshot = store.get_latest_monitoring_snapshot()
        if snapshot:
            payload["snapshot"] = snapshot
        pending = store.list_review_queue(limit=50, status="PENDING")
        payload["review_queue_pending"] = len(pending)
    return payload
