"""ABSA inference — load checkpoint once, run single-text prediction."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import torch
from transformers import AutoTokenizer

# Reuse training architecture and helpers (same repo).
from .postprocess import PostprocessConfig, postprocess_predictions
from .train import (
    ASPECTS,
    ABSAModel,
    autocast_context,
    build_predicted_span_inputs,
    nfc,
)

SENTIMENT_LABELS = ["Negative", "Positive", "Neutral"]
SENTIMENT_API = ["negative", "positive", "neutral"]

ASPECT_DISPLAY: dict[str, str] = {
    "Fashion": "Fashion",
    "Electronics": "Electronics",
    "General": "General",
    "Service": "Service",
    "Ship": "Delivery",
    "Price": "Price",
    "App": "App",
}


def _load_config(model_dir: Path) -> dict[str, Any]:
    for name in ("config.json", "run_config.json"):
        path = model_dir / name
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    raise FileNotFoundError(f"No config.json or run_config.json in {model_dir}")


def _extract_target(text: str, offsets: list, start_tok: int, end_tok: int) -> tuple[str, int, int]:
    """Char span from token span."""
    char_start = int(offsets[start_tok][0])
    char_end = int(offsets[end_tok][1])
    return text[char_start:char_end], char_start, char_end


def load_model(model_dir: str | Path, device: str | None = None) -> dict[str, Any]:
    """Load tokenizer + weights once at startup."""
    model_dir = Path(model_dir)
    checkpoint = model_dir / "best_model.pt"
    if not checkpoint.exists():
        raise FileNotFoundError(f"Missing checkpoint: {checkpoint}")

    config = _load_config(model_dir)
    max_ops = int(config.get("max_ops", 8))
    max_len = int(config.get("max_len", 224))
    max_context_window = int(config.get("max_context_window", 25))
    model_name = config.get("model_name", "Fsoft-AIC/videberta-base")

    dev = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = ABSAModel(model_name, max_ops)
    state = torch.load(checkpoint, map_location=dev, weights_only=True)
    model.load_state_dict(state)
    model.eval()
    model.float()
    model.to(dev)

    post_cfg = PostprocessConfig.from_dict(config.get("postprocess"))

    return {
        "model": model,
        "tokenizer": tokenizer,
        "device": dev,
        "max_ops": max_ops,
        "max_len": max_len,
        "max_context_window": max_context_window,
        "config": config,
        "postprocess": post_cfg,
    }


def model_fn(model_dir: str | Path, device: str | None = None) -> dict[str, Any]:
    """Alias for SageMaker-style naming used by legacy backend."""
    return load_model(model_dir, device=device)


def predict_fn(text: str, bundle: dict[str, Any]) -> dict[str, Any]:
    """Run ABSA on one review string."""
    return predict_text(text, bundle)


def predict_text(text: str, bundle: dict[str, Any]) -> dict[str, Any]:
    t0 = time.perf_counter()
    model = bundle["model"]
    tokenizer = bundle["tokenizer"]
    device = bundle["device"]
    max_ops = bundle["max_ops"]
    max_len = bundle["max_len"]
    max_context_window = bundle["max_context_window"]

    text = nfc(text.strip())
    if not text:
        return {
            "opinions": [],
            "global_sentiment": "Neutral",
            "global_confidence": 0.0,
            "latency_ms": 0,
        }

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
    offsets = enc["offset_mapping"][0].tolist()
    spec_mask = enc["special_tokens_mask"][0].bool().tolist()

    with torch.inference_mode():
        with autocast_context(device):
            _, emiss, _, glob_logits, cached = model(ids, mask)

        bio_p = model.crf.decode(emiss, mask=mask.bool())
        seq_len = int(mask[0].sum())

        pred_set, pred_mask_row, pred_aspect_row, pred_clause_row = build_predicted_span_inputs(
            bio_p[0],
            enc["offset_mapping"][0].to(device),
            torch.tensor(spec_mask, device=device),
            text,
            seq_len,
            max_ops,
            max_context_window,
            device,
        )

        pred_sm = pred_mask_row.unsqueeze(0)
        pred_sp_asp = pred_aspect_row.unsqueeze(0)
        pred_clause_pos = pred_clause_row.unsqueeze(0)

        with autocast_context(device):
            _, _, sent_logits, _, _ = model(
                ids,
                mask,
                span_mask=pred_sm,
                cached_seq=cached,
                span_aspect=pred_sp_asp,
                span_clause_pos=pred_clause_pos,
                offsets=enc["offset_mapping"].to(device),
                texts=[text],
            )

    glob_probs = torch.softmax(glob_logits[0], dim=-1)

    raw_opinions: list[dict[str, Any]] = []
    sorted_spans = sorted(pred_set)

    for si, (ps, pe, aspect) in enumerate(sorted_spans[:max_ops]):
        if aspect not in ASPECTS:
            continue
        target, char_start, char_end = _extract_target(text, offsets, ps, pe)
        target = target.strip()
        if not target:
            continue

        if sent_logits is not None and si < sent_logits.shape[1]:
            probs = torch.softmax(sent_logits[0, si], dim=-1)
            prob_vec = probs.detach().float().cpu().tolist()
            sent_id = int(probs.argmax().item())
            confidence = float(probs[sent_id].item())
        else:
            prob_vec = [0.0, 0.0, 1.0]
            sent_id = 2
            confidence = 0.0

        raw_opinions.append({
            "target": target,
            "aspect": ASPECT_DISPLAY.get(aspect, aspect),
            "aspect_raw": aspect,
            "sentiment": SENTIMENT_LABELS[sent_id],
            "confidence": round(confidence, 4),
            "start": char_start,
            "end": char_end,
            "_sent_id": sent_id,
            "_probs": prob_vec,
        })

    post_cfg = bundle.get("postprocess") or PostprocessConfig()
    opinions, glob_id, glob_conf = postprocess_predictions(
        raw_opinions,
        glob_probs,
        post_cfg,
    )

    latency_ms = int((time.perf_counter() - t0) * 1000)

    return {
        "opinions": opinions,
        "global_sentiment": SENTIMENT_LABELS[glob_id],
        "global_confidence": round(glob_conf, 4),
        "latency_ms": latency_ms,
    }
