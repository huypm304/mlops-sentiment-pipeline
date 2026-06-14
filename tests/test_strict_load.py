"""Test that the checkpoint loads with strict=True.

Skipped if model/best_model.pt is not present (CI without artifacts).
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

MODEL_DIR = Path(__file__).resolve().parents[1] / "model"
CHECKPOINT = MODEL_DIR / "best_model.pt"
RUN_CONFIG = MODEL_DIR / "run_config.json"


def _config_source():
    if RUN_CONFIG.is_file():
        return json.loads(RUN_CONFIG.read_text(encoding="utf-8")).get("model_name")
    return "vinai/phobert-base"


@pytest.mark.skipif(not CHECKPOINT.is_file(), reason="best_model.pt not present")
def test_strict_load():
    import torch
    from src.absa.model import ABSAModel

    device = torch.device("cpu")
    model = ABSAModel(_config_source(), max_ops=6)

    state = torch.load(CHECKPOINT, map_location=device)
    if isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]
    cleaned = {(k[len("module."):] if k.startswith("module.") else k): v for k, v in state.items()}

    missing, unexpected = model.load_state_dict(cleaned, strict=True)

    assert not missing, f"Missing keys in checkpoint: {missing}"
    assert not unexpected, f"Unexpected keys in checkpoint: {unexpected}"


@pytest.mark.skipif(not CHECKPOINT.is_file(), reason="best_model.pt not present")
def test_state_dict_key_count():
    import torch
    from src.absa.model import ABSAModel

    model = ABSAModel(_config_source(), max_ops=6)
    model_keys = set(model.state_dict().keys())

    state = torch.load(CHECKPOINT, map_location="cpu")
    if isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]
    ckpt_keys = {(k[len("module."):] if k.startswith("module.") else k) for k in state.keys()}

    assert model_keys == ckpt_keys, (
        f"Key mismatch:\n"
        f"  In model not in ckpt: {model_keys - ckpt_keys}\n"
        f"  In ckpt not in model: {ckpt_keys - model_keys}"
    )
