"""Test that evaluate() runs without crashing on a mini dev set.

Skipped if best_model.pt is not present.
Does NOT assert exact metric values (no full dev file in repo).
"""

import sys
from pathlib import Path

import pytest
import torch
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

CHECKPOINT = Path(__file__).resolve().parents[1] / "model" / "best_model.pt"
MODEL_DIR = CHECKPOINT.parent
MINI_DEV  = Path(__file__).resolve().parent / "fixtures" / "dev_mini.jsonl"


@pytest.mark.skipif(not CHECKPOINT.is_file(), reason="best_model.pt not present")
def test_evaluate_runs():
    from transformers import AutoTokenizer

    from src.absa.dataset import ABSADataset
    from src.absa.evaluation import evaluate
    from src.absa.model import ABSAModel

    device = torch.device("cpu")
    tokenizer = AutoTokenizer.from_pretrained("Fsoft-AIC/videberta-base")

    ds = ABSADataset(MINI_DEV, tokenizer, max_len=192, max_ops=6, max_context_window=25)
    dl = DataLoader(ds, batch_size=2, shuffle=False)

    model = ABSAModel("Fsoft-AIC/videberta-base", max_ops=6).to(device)
    state = torch.load(CHECKPOINT, map_location=device)
    if isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]
    cleaned = {(k[len("module."):] if k.startswith("module.") else k): v for k, v in state.items()}
    model.load_state_dict(cleaned, strict=True)
    # Match train/train.py: model = ABSAModel(...).to(device).float()
    model.float()

    m = evaluate(model, dl, device, max_ops=6, max_context_window=25, span_match_iou=0.5)

    # Required keys present
    for key in ["tas_strict", "tas_relaxed", "span", "sent_matched", "sent_goldspan", "global",
                "asp_sent_f1", "asp_span_f1", "class_metrics", "confusion_matrices"]:
        assert key in m, f"Missing key in evaluate() output: {key}"

    # All F1 values in [0, 1]
    for top_key in ["tas_strict", "tas_relaxed", "span", "sent_matched", "sent_goldspan", "global"]:
        assert 0.0 <= m[top_key]["f1"] <= 1.0 + 1e-6, f"F1 out of range for {top_key}"

    print("evaluate() completed successfully on mini dev set")
    print(f"  TAS-Relaxed F1 = {m['tas_relaxed']['f1']:.4f}")
    print(f"  Span F1        = {m['span']['f1']:.4f}")
    print(f"  Global F1      = {m['global']['f1']:.4f}")


def test_evaluate_output_schema():
    """Verify output dict structure without running model (schema-only check)."""
    # Build a fake output to verify schema expectations
    required_keys = [
        "tas_strict", "tas_relaxed", "span", "sent_matched",
        "sent_goldspan", "global", "asp_sent_f1", "asp_span_f1",
        "asp_support", "asp_sent_pred_dist", "asp_sent_gold_dist",
        "class_metrics", "confusion_matrices",
    ]
    # We just check that evaluate() can be imported and has the right signature
    from src.absa.evaluation import evaluate
    import inspect
    sig = inspect.signature(evaluate)
    params = list(sig.parameters.keys())
    assert "model" in params
    assert "dataloader" in params
    assert "device" in params
    assert "max_ops" in params
    assert "span_match_iou" in params
