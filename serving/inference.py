"""SageMaker PyTorch inference entry point for Vietnamese ABSA.

Packaged inside model.tar.gz under ``code/inference.py`` with ``src/absa/``.
Model weights and configs live at the tarball root (``best_model.pt``, etc.).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


def _ensure_code_path() -> None:
    code_dir = Path(__file__).resolve().parent
    root = str(code_dir)
    if root not in sys.path:
        sys.path.insert(0, root)


def model_fn(model_dir: str) -> dict[str, Any]:
    """Load checkpoint once when the endpoint starts."""
    _ensure_code_path()
    from src.absa.inference import load_model

    device = os.environ.get("ABSA_DEVICE", "cpu")
    return load_model(model_dir, device=device, strict=True)


def input_fn(request_body: bytes | str, content_type: str) -> str:
    if content_type not in ("application/json", "application/json; charset=utf-8"):
        raise ValueError(f"Unsupported content type: {content_type}")

    payload = json.loads(request_body)
    if isinstance(payload, str):
        text = payload
    elif isinstance(payload, dict):
        text = payload.get("text", "")
    else:
        raise ValueError("Request body must be JSON object with 'text' or a JSON string")

    text = str(text).strip()
    if not text:
        raise ValueError("text is required")
    return text


def predict_fn(text: str, bundle: dict[str, Any]) -> dict[str, Any]:
    _ensure_code_path()
    from src.absa.inference import predict_one

    return predict_one(text, bundle)


def output_fn(prediction: dict[str, Any], accept: str) -> tuple[str, str]:
    if accept not in ("application/json", "application/json; charset=utf-8"):
        raise ValueError(f"Unsupported accept type: {accept}")
    return json.dumps(prediction, ensure_ascii=False), "application/json"
