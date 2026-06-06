"""Unit tests for DynamoDB registry helpers."""

from __future__ import annotations

from decimal import Decimal

from registry.convert import from_dynamo, to_dynamo


def test_to_dynamo_converts_floats():
    item = to_dynamo({"score": 0.75, "count": 3})
    assert item["score"] == Decimal("0.75")
    assert item["count"] == 3


def test_from_dynamo_roundtrip():
    raw = {"metrics": {"global_f1": 0.86}, "epochs": 50}
    restored = from_dynamo(to_dynamo(raw))
    assert restored["metrics"]["global_f1"] == 0.86
    assert restored["epochs"] == 50
