"""Inference pipeline for ABSA — 2-pass (BIO → spans → sentiment/global).

Follows the same forward logic as evaluate() in evaluation.py:
  Pass 1: encode → BIO decode
  Pass 2: predicted spans → sent_logits + global_logits

load_model() uses strict=True; architecture mismatch raises RuntimeError.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import torch
from transformers import AutoTokenizer

from .dataset import build_predicted_span_inputs, extract_spans
from .labels import ASPECTS, SENT_ID2LABEL
from .model import ABSAModel
from .postprocess import PostprocessConfig, postprocess_predictions
from .utils import autocast_context, nfc

MODEL_VERSION = "absa-v2b"


# ---------------------------------------------------------------------------
# Load helpers
# ---------------------------------------------------------------------------

def load_tokenizer(model_name: str) -> Any:
    return AutoTokenizer.from_pretrained(model_name)


def load_model(
    model_dir: str | Path,
    device: str | None = None,
    model_name: str | None = None,
    max_ops: int | None = None,
    strict: bool = True,
) -> dict[str, Any]:
    """Load checkpoint and return a bundle dict.

    Raises RuntimeError on architecture mismatch when strict=True.
    Never use strict=False to hide key mismatches.
    """
    model_dir = Path(model_dir)
    config: dict = {}
    for cfg_name in ("run_config.json", "config.json"):
        cfg_path = model_dir / cfg_name
        if cfg_path.is_file():
            with open(cfg_path, encoding="utf-8") as f:
                config = json.load(f)
            break

    _model_name = model_name or config.get("model_name", "Fsoft-AIC/videberta-base")
    _max_len = int(config.get("max_len", 192))
    _max_ops = max_ops if max_ops is not None else int(config.get("max_ops", 6))
    _max_context_window = int(config.get("max_context_window", 25))

    dev = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
    tokenizer = AutoTokenizer.from_pretrained(_model_name)
    model = ABSAModel(_model_name, _max_ops).to(dev)

    checkpoint = model_dir / "best_model.pt"
    if not checkpoint.is_file():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint}")

    state = torch.load(checkpoint, map_location=dev)
    if isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]

    # Strip DataParallel prefix if present
    cleaned = {}
    for k, v in state.items():
        cleaned[k[len("module."):] if k.startswith("module.") else k] = v

    try:
        model.load_state_dict(cleaned, strict=strict)
    except RuntimeError as exc:
        raise RuntimeError(
            f"Checkpoint architecture mismatch (strict=True). "
            f"Ensure model class matches the saved checkpoint.\n{exc}"
        ) from exc

    # Match train/train.py: model = ABSAModel(...).to(device).float()
    # Required to avoid LSTM dtype mismatch when backbone emits lower precision.
    model.float()
    model.eval()

    pp_cfg = PostprocessConfig()
    pp_path = model_dir / "postprocess_config.json"
    if pp_path.is_file():
        with open(pp_path, encoding="utf-8") as f:
            pp_cfg = PostprocessConfig.from_dict(json.load(f))

    return {
        "model": model,
        "tokenizer": tokenizer,
        "device": dev,
        "max_len": _max_len,
        "max_ops": _max_ops,
        "max_context_window": _max_context_window,
        "postprocess_config": pp_cfg,
        "model_version": MODEL_VERSION,
        "model_name": _model_name,
    }


# ---------------------------------------------------------------------------
# Single-text inference
# ---------------------------------------------------------------------------

@torch.inference_mode()
def _raw_infer(
    text: str,
    model: ABSAModel,
    tokenizer,
    device: torch.device,
    max_len: int = 192,
    max_ops: int = 6,
    max_context_window: int = 25,
) -> dict[str, Any]:
    """Run 2-pass inference; return raw (pre-postprocess) outputs."""
    text = nfc(text)

    enc = tokenizer(
        text,
        max_length=max_len,
        padding="max_length",
        truncation=True,
        return_offsets_mapping=True,
        return_special_tokens_mask=True,
        return_tensors="pt",
    )

    ids = enc["input_ids"].to(device)
    mask = enc["attention_mask"].to(device)
    offsets = enc["offset_mapping"][0].to(device)
    spec_mask = enc["special_tokens_mask"][0].bool().to(device)

    with autocast_context(device):
        _, emiss, _, _, cached, _ = model(ids, mask)

    bio_pred = model.crf.decode(emiss.float(), mask=mask.bool())[0]
    seq_len = int(mask[0].sum().item())

    pred_spans, pred_span_mask, pred_span_aspect, pred_clause_pos = build_predicted_span_inputs(
        decoded_seq=bio_pred,
        offsets_row=offsets,
        spec_mask_row=spec_mask,
        text=text,
        seq_len=seq_len,
        max_ops=max_ops,
        max_context_window=max_context_window,
        device=device,
    )

    offsets_b = offsets.unsqueeze(0)
    with autocast_context(device):
        _, _, sent_logits, global_logits, _, _ = model(
            ids,
            mask,
            span_mask=pred_span_mask.unsqueeze(0),
            cached_seq=cached,
            span_aspect=pred_span_aspect.unsqueeze(0),
            span_clause_pos=pred_clause_pos.unsqueeze(0),
            offsets=offsets_b,
            texts=[text],
        )

    global_probs = torch.softmax(global_logits[0], dim=-1).detach().cpu().tolist()
    sorted_spans = sorted(pred_spans)[:max_ops]

    raw_opinions = []
    for slot_idx, (tok_s, tok_e, aspect) in enumerate(sorted_spans):
        sent_prob_t = torch.softmax(sent_logits[0, slot_idx], dim=-1).detach().cpu()
        probs = sent_prob_t.tolist()
        sent_id = int(sent_prob_t.argmax().item())
        conf = float(probs[sent_id])

        char_s = int(offsets[tok_s][0].item())
        char_e = int(offsets[tok_e][1].item())
        raw_target = text[char_s:char_e]
        leading = len(raw_target) - len(raw_target.lstrip())
        target_text = raw_target.strip()
        char_s = char_s + leading
        char_e = char_s + len(target_text)

        raw_opinions.append({
            "target": target_text,
            "aspect": aspect,
            "sentiment": SENT_ID2LABEL[sent_id],
            "sentiment_id": sent_id,
            "confidence": round(conf, 4),
            "raw_confidence": round(conf, 4),
            "start": char_s,
            "end": char_e,
            "probs": {
                "NEG": round(probs[0], 4),
                "POS": round(probs[1], 4),
                "NEU": round(probs[2], 4),
            },
            "_probs": probs,
            "_sent_id": sent_id,
        })

    return {"opinions": raw_opinions, "global_probs": global_probs}


def predict_one(
    text: str,
    bundle: dict[str, Any],
) -> dict[str, Any]:
    """Predict a single text; returns full response schema."""
    started = time.perf_counter()

    raw = _raw_infer(
        text,
        bundle["model"],
        bundle["tokenizer"],
        bundle["device"],
        max_len=bundle["max_len"],
        max_ops=bundle["max_ops"],
        max_context_window=bundle["max_context_window"],
    )

    result = postprocess_predictions(
        opinions=raw["opinions"],
        glob_probs=raw["global_probs"],
        text=text,
        cfg=bundle.get("postprocess_config"),
        model_version=bundle.get("model_version", MODEL_VERSION),
    )

    result["latency_ms"] = int((time.perf_counter() - started) * 1000)
    return result


def predict_batch(
    texts: list[str],
    bundle: dict[str, Any],
) -> list[dict[str, Any]]:
    """Predict a list of texts sequentially."""
    return [predict_one(t, bundle) for t in texts]
