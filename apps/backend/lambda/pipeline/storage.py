"""DynamoDB + S3 helpers for pipeline Lambda (delegates to shared registry)."""

from __future__ import annotations

import json
from typing import Any

from registry.store import RegistryStore, now_iso

_store: RegistryStore | None = None


def _get_store() -> RegistryStore:
    global _store
    if _store is None:
        _store = RegistryStore()
    return _store


def put_json_s3(key: str, payload: dict[str, Any]) -> str:
    return _get_store().put_json_s3(key, payload)


def put_training_run(record: dict[str, Any]) -> None:
    if not _get_store().config.training_runs_table:
        return
    _get_store().put_training_run(record)


def update_training_run(run_id: str, created_at: str, updates: dict[str, Any]) -> None:
    if not _get_store().config.training_runs_table:
        return
    _get_store().update_training_run(run_id, created_at, updates)


def put_approval_request(record: dict[str, Any]) -> None:
    if not _get_store().config.approval_table:
        return
    _get_store().put_approval_request(record)


def get_approval_request(approval_id: str) -> dict[str, Any] | None:
    if not _get_store().config.approval_table:
        return None
    return _get_store().get_approval_request(approval_id)


def get_training_run(run_id: str) -> dict[str, Any] | None:
    if not _get_store().config.training_runs_table:
        return None
    return _get_store().get_training_run(run_id)


def list_training_runs(limit: int = 15) -> list[dict[str, Any]]:
    if not _get_store().config.training_runs_table:
        return []
    return _get_store().list_training_runs(limit=limit)


def put_model_record(record: dict[str, Any]) -> None:
    if not _get_store().config.models_table:
        return
    _get_store().put_model(record)


def list_model_records(limit: int = 50, status: str | None = None) -> list[dict[str, Any]]:
    if not _get_store().config.models_table:
        return []
    return _get_store().list_models(limit=limit, status=status)


def get_store() -> RegistryStore:
    return _get_store()


def resolve_run_created_at(event: dict[str, Any]) -> str:
    if event.get("created_at"):
        return str(event["created_at"])
    run = get_training_run(str(event.get("run_id", "")))
    if run and run.get("created_at"):
        return str(run["created_at"])
    return now_iso()
