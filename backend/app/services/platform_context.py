"""Aggregate workspace metadata for the control-plane header."""

from __future__ import annotations

from typing import Any

from backend.app.services import datasets as datasets_service
from backend.app.services import metrics as metrics_service
from backend.app.services import pipeline as pipeline_service
from backend.app.services import runtime as runtime_service


def get_platform_context(*, model_ready: bool = True) -> dict[str, Any]:
    models = metrics_service.list_models()
    champion = next((m for m in models if m.get("status") == "production"), models[0] if models else None)

    dataset_rows = datasets_service.list_datasets()
    active = next(
        (d for d in dataset_rows if d.get("status") in {"approved", "audited"} or d.get("audit_passed")),
        dataset_rows[0] if dataset_rows else None,
    )

    runs = pipeline_service.list_runs(max_results=5)
    last_run = runs[0] if runs else None
    last_training_at = (
        last_run.get("stop_date") or last_run.get("start_date") if last_run else None
    )
    if not last_training_at and champion:
        last_training_at = champion.get("promoted_at")

    if not last_training_at:
        artifact_ts = metrics_service.get_last_training_at()
        last_training_at = artifact_ts or None

    stats = runtime_service.get_runtime_stats(model_ready)
    endpoint = stats.get("endpoint_health", "unknown")

    return {
        "environment": "demo",
        "champion_model": champion.get("version") if champion else None,
        "active_dataset": active.get("dataset_id") if active else None,
        "active_dataset_name": active.get("name") if active else None,
        "api_status": "healthy" if endpoint == "healthy" else endpoint,
        "last_training_at": last_training_at,
        "pipeline_demo_mode": not pipeline_service.is_configured(),
    }
