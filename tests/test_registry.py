"""Unit tests for DynamoDB registry helpers."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "backend"))

from registry.convert import from_dynamo, to_dynamo
from registry.store import RegistryStore


def test_to_dynamo_converts_floats():
    item = to_dynamo({"score": 0.75, "count": 3})
    assert item["score"] == Decimal("0.75")
    assert item["count"] == 3


def test_from_dynamo_roundtrip():
    raw = {"metrics": {"global_f1": 0.86}, "epochs": 50}
    restored = from_dynamo(to_dynamo(raw))
    assert restored["metrics"]["global_f1"] == 0.86
    assert restored["epochs"] == 50


def test_update_dataset_skips_reserved_keys():
    calls: list[dict] = []

    class FakeTable:
        def update_item(self, **kwargs):
            calls.append(kwargs)

    store = RegistryStore.__new__(RegistryStore)
    store.config = type("C", (), {"datasets_table": "tbl"})()
    store._table = lambda _name: FakeTable()  # noqa: SLF001

    store.update_dataset(
        "ds-1",
        "2026-01-01T00:00:00Z",
        {
            "dataset_id": "ds-1",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "ignored",
            "status": "PENDING",
        },
    )

    expr = calls[0]["UpdateExpression"]
    assert "#updated_at = :updated_at" in expr
    assert "dataset_id" not in expr
    assert "created_at" not in expr
