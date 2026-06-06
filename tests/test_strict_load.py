"""Test that the checkpoint loads with strict=True.

Skipped if model/best_model.pt is not present (CI without artifacts).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

CHECKPOINT = Path(__file__).resolve().parents[1] / "model" / "best_model.pt"


@pytest.mark.skipif(not CHECKPOINT.is_file(), reason="best_model.pt not present")
def test_strict_load():
    import torch
    from src.absa.model import ABSAModel

    device = torch.device("cpu")
    model = ABSAModel("Fsoft-AIC/videberta-base", max_ops=6)

    state = torch.load(CHECKPOINT, map_location=device)
    if isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]
    cleaned = {(k[len("module."):] if k.startswith("module.") else k): v for k, v in state.items()}

    # This must NOT raise RuntimeError
    missing, unexpected = model.load_state_dict(cleaned, strict=True)

    assert not missing,    f"Missing keys in checkpoint: {missing}"
    assert not unexpected, f"Unexpected keys in checkpoint: {unexpected}"
    print("strict=True load: OK")


@pytest.mark.skipif(not CHECKPOINT.is_file(), reason="best_model.pt not present")
def test_state_dict_key_count():
    """Verify number of parameter tensors is consistent."""
    import torch
    from src.absa.model import ABSAModel

    model = ABSAModel("Fsoft-AIC/videberta-base", max_ops=6)
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
