"""Smoke test: predict a Vietnamese sentence and check output schema.

Skipped if best_model.pt is not present.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

CHECKPOINT = Path(__file__).resolve().parents[1] / "model" / "best_model.pt"
MODEL_DIR = CHECKPOINT.parent


@pytest.mark.skipif(not CHECKPOINT.is_file(), reason="best_model.pt not present")
def test_predict_one_schema():
    from src.absa.inference import load_model, predict_one

    bundle = load_model(MODEL_DIR, device="cpu", strict=True)
    text = "Giá mềm, chất vải mát, nhưng giao hàng làm mình chờ hơi lâu."
    result = predict_one(text, bundle)

    # Schema checks
    assert "text" in result
    assert "opinions" in result
    assert "global_sentiment" in result
    assert "global_sentiment_id" in result
    assert "global_confidence" in result
    assert "global_probs" in result
    assert "model_version" in result
    assert "need_review" in result
    assert "guardrail_status" in result
    assert result["guardrail_status"] in ("PASS", "REVIEW")

    # Global sentiment must be valid
    assert result["global_sentiment"] in ("NEG", "POS", "NEU")
    assert result["global_sentiment_id"] in (0, 1, 2)
    assert 0.0 <= result["global_confidence"] <= 1.0

    # Global probs must sum to ~1
    gp = result["global_probs"]
    assert abs(gp["NEG"] + gp["POS"] + gp["NEU"] - 1.0) < 0.05

    # Opinion schema
    for op in result["opinions"]:
        assert "target" in op
        assert "aspect" in op
        assert "sentiment" in op
        assert "sentiment_id" in op
        assert "confidence" in op
        assert "probs" in op
        assert op["sentiment"] in ("NEG", "POS", "NEU")
        assert op["sentiment_id"] in (0, 1, 2)


@pytest.mark.skipif(not CHECKPOINT.is_file(), reason="best_model.pt not present")
def test_predict_one_expected_aspects():
    """The test sentence should produce Price, Fashion, and/or Ship aspects."""
    from src.absa.inference import load_model, predict_one

    bundle = load_model(MODEL_DIR, device="cpu", strict=True)
    text = "Giá mềm, chất vải mát, nhưng giao hàng làm mình chờ hơi lâu."
    result = predict_one(text, bundle)

    found_aspects = {op["aspect"] for op in result["opinions"]}
    # At least one of the expected aspects should be detected
    expected = {"Price", "Fashion", "Ship"}
    assert found_aspects & expected, (
        f"Expected at least one of {expected} but found {found_aspects}. "
        "Model may not have loaded correctly."
    )


@pytest.mark.skipif(not CHECKPOINT.is_file(), reason="best_model.pt not present")
def test_predict_batch():
    from src.absa.inference import load_model, predict_batch

    bundle = load_model(MODEL_DIR, device="cpu", strict=True)
    texts = [
        "Giá mềm nhưng giao hàng chậm.",
        "App rất mượt.",
    ]
    results = predict_batch(texts, bundle)

    assert len(results) == 2
    for r in results:
        assert "text" in r
        assert "global_sentiment" in r
