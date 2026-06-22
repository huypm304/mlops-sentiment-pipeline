"""Inference pipeline for ABSA — 2-pass (BIO → spans → sentiment/global).

Load flow (no HF base weights):
  1. Read run_config.json from model_dir
  2. Build empty backbone via AutoModel.from_config()
  3. Load all weights from best_model.pt (or pointer.txt)

load_model() uses strict=True; architecture mismatch raises RuntimeError.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import torch

from .dataset import build_predicted_span_inputs
from .labels import SENT_ID2LABEL
from .model import ABSAModel
from .postprocess import PostprocessConfig, postprocess_predictions
from .utils import (
    autocast_context,
    build_offsets_from_tokens,
    load_tokenizer,
    nfc,
    resolve_checkpoint,
    resolve_config_source,
    resolve_tokenizer_source,
)

__all__ = [
    "MODEL_VERSION",
    "load_tokenizer",
    "load_model",
    "predict_one",
    "predict_batch",
    "encode_text",
]

MODEL_VERSION = "absa-v2b"


def encode_text(text, tokenizer, max_len, device):
    text = nfc(text)

    if getattr(tokenizer, "is_fast", False):
        enc = tokenizer(
            text,
            max_length=max_len,
            padding="max_length",
            truncation=True,
            return_offsets_mapping=True,
            return_special_tokens_mask=True,
            return_tensors="pt",
        )
        offsets = enc["offset_mapping"][0]
    else:
        enc = tokenizer(
            text,
            max_length=max_len,
            padding="max_length",
            truncation=True,
            return_special_tokens_mask=True,
            return_tensors="pt",
        )
        toks = tokenizer.convert_ids_to_tokens(enc["input_ids"][0].tolist())
        spec_list = enc["special_tokens_mask"][0].tolist()
        offsets = build_offsets_from_tokens(text, toks, spec_list)

    ids = enc["input_ids"].to(device)
    mask = enc["attention_mask"].to(device)
    if isinstance(offsets, torch.Tensor):
        offsets_t = offsets.to(device)
    else:
        offsets_t = torch.tensor(offsets, device=device)
    spec_mask_t = enc["special_tokens_mask"][0].bool().to(device)
    return text, ids, mask, offsets_t, spec_mask_t


def load_model(
    model_dir: str | Path,
    device: str | None = None,
    model_name: str | None = None,
    max_ops: int | None = None,
    strict: bool = True,
) -> dict[str, Any]:
    """Load trained checkpoint from model_dir."""
    model_dir = Path(model_dir)
    config: dict = {}
    for cfg_name in ("run_config.json", "config.json"):
        cfg_path = model_dir / cfg_name
        if cfg_path.is_file():
            with open(cfg_path, encoding="utf-8") as f:
                config = json.load(f)
            break

    if not config and model_name is None:
        raise FileNotFoundError(f"Missing run_config.json in {model_dir}")

    if model_name:
        config = {**config, "model_name": model_name}

    _max_len = int(config.get("max_len", 192))
    _max_ops = max_ops if max_ops is not None else int(config.get("max_ops", 6))
    _max_context_window = int(config.get("max_context_window", 25))
    config_source = resolve_config_source(model_dir, config)
    tokenizer_source = resolve_tokenizer_source(model_dir, config)

    dev = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
    tokenizer = load_tokenizer(tokenizer_source)
    model = ABSAModel(config_source, _max_ops).to(dev)
    checkpoint = resolve_checkpoint(model_dir)

    state = torch.load(checkpoint, map_location=dev)
    if isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]

    cleaned = {}
    for k, v in state.items():
        cleaned[k[len("module."):] if k.startswith("module.") else k] = v

    try:
        model.load_state_dict(cleaned, strict=strict)
    except RuntimeError as exc:
        raise RuntimeError(
            f"Checkpoint architecture mismatch (strict={strict}). "
            f"Ensure model class matches the saved checkpoint.\n{exc}"
        ) from exc

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
        "model_name": config.get("model_name"),
    }


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
    text, ids, mask, offsets, spec_mask = encode_text(text, tokenizer, max_len, device)

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

    with autocast_context(device):
        _, _, sent_logits, global_logits, _, _ = model(
            ids,
            mask,
            span_mask=pred_span_mask.unsqueeze(0),
            cached_seq=cached,
            span_aspect=pred_span_aspect.unsqueeze(0),
            span_clause_pos=pred_clause_pos.unsqueeze(0),
            offsets=offsets.unsqueeze(0),
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
    return [predict_one(t, bundle) for t in texts]
