"""Backend facade for the shared DynamoDB registry."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from registry.config import RegistryConfig, load_config
from registry.store import RegistryStore, now_iso

__all__ = ["RegistryStore", "get_store", "is_enabled", "now_iso"]


@lru_cache(maxsize=1)
def _config() -> RegistryConfig:
    return load_config()


def is_enabled() -> bool:
    return _config().enabled


def get_store() -> RegistryStore | None:
    config = _config()
    if not config.enabled:
        return None
    return RegistryStore(config)


def clear_cache() -> None:
    _config.cache_clear()


def map_dataset_list_item(record: dict[str, Any]) -> dict[str, Any]:
    status = str(record.get("status", "pending")).lower()
    if status == "audit_passed":
        status = "audited"
    return {
        "dataset_id": record.get("dataset_id", ""),
        "name": record.get("name", record.get("dataset_id", "")),
        "status": status,
        "created_at": record.get("created_at", ""),
        "splits": record.get("splits") or [],
        "audit_passed": bool(record.get("audit_passed")),
        "audit_score": record.get("audit_score"),
        "total_rows": int(record.get("num_records", 0)),
    }
