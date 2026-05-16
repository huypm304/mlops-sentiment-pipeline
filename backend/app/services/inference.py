from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Repo root on path so `model` package resolves
_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from model.inference import load_model, predict_text

from backend.app.config.settings import MODEL_DIR

_bundle: dict[str, Any] | None = None


def get_model_bundle() -> dict[str, Any]:
    global _bundle
    if _bundle is None:
        raise RuntimeError("Model not loaded. Server may still be starting.")
    return _bundle


def init_model(device: str | None = None) -> None:
    """Load checkpoint once at application startup."""
    global _bundle
    _bundle = load_model(MODEL_DIR, device=device or "cpu")
    print(f"ABSA model loaded from {MODEL_DIR} on {_bundle['device']}")


def run_predict(text: str) -> dict[str, Any]:
    return predict_text(text, get_model_bundle())
