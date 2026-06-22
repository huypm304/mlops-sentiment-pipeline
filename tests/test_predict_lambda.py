"""Unit tests for predict Lambda handler (stub + SageMaker invoke path)."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "backend" / "lambda" / "predict"))
sys.path.insert(0, str(ROOT))

handler = importlib.import_module("handler")


@pytest.fixture(autouse=True)
def _reset_handler_state():
    handler._ENABLE_SAGEMAKER = False
    handler._ENDPOINT = ""
    handler._sagemaker_client = None
    yield


def test_health_reports_stub_mode():
    response = handler.lambda_handler({"rawPath": "/health"}, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["model"] == "local_stub"
    assert body["sagemaker_enabled"] is False


def test_predict_stub_when_sagemaker_disabled():
    response = handler.lambda_handler(
        {"rawPath": "/predict", "body": json.dumps({"text": "Giá tốt"})},
        None,
    )
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["opinions"] == []
    assert body["global_sentiment"] == "neutral"
    assert "note" in body


def test_predict_requires_text():
    response = handler.lambda_handler({"rawPath": "/predict", "body": "{}"}, None)
    assert response["statusCode"] == 400


def test_predict_invokes_sagemaker_when_enabled():
    handler._ENABLE_SAGEMAKER = True
    handler._ENDPOINT = "absa-mlops-demo-endpoint"
    sm_payload = {
        "opinions": [
            {
                "target": "giá",
                "aspect": "Price",
                "sentiment": "POS",
                "confidence": 0.91,
                "raw_confidence": 0.91,
                "calibrated_confidence": 0.91,
                "start": 0,
                "end": 3,
            }
        ],
        "global_sentiment": "POS",
        "global_confidence": 0.88,
        "global_raw_confidence": 0.88,
        "model_version": "absa-v2b",
        "latency_ms": 120,
    }

    with patch.object(handler, "_invoke_sagemaker", return_value=sm_payload) as invoke:
        response = handler.lambda_handler(
            {"rawPath": "/predict", "body": json.dumps({"text": "Giá tốt"})},
            None,
        )

    invoke.assert_called_once_with("Giá tốt")
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert len(body["opinions"]) == 1
    assert body["global_sentiment"] == "positive"
    assert body["opinions"][0]["sentiment"] == "positive"
    assert body["model_version"] == "absa-v2b"
    assert "note" not in body


def test_predict_returns_503_when_sagemaker_invoke_fails():
    handler._ENABLE_SAGEMAKER = True
    handler._ENDPOINT = "absa-mlops-demo-endpoint"

    with patch.object(handler, "_invoke_sagemaker", side_effect=RuntimeError("endpoint down")):
        response = handler.lambda_handler(
            {"rawPath": "/predict", "body": json.dumps({"text": "Giá tốt"})},
            None,
        )

    assert response["statusCode"] == 503
    body = json.loads(response["body"])
    assert "endpoint down" in body["detail"]
