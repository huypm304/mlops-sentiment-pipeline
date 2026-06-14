"""Shared utilities — extracted from train/train.py + IO helpers."""

from __future__ import annotations

import hashlib
import json
import random
import re
import unicodedata
from contextlib import nullcontext
from pathlib import Path
from typing import Any

import numpy as np
import torch
from transformers import AutoTokenizer

CONTRAST_WORDS = {
    "nhưng",
    "tuy",
    "dù",
    "mà",
    "song",
    "còn",
    "tuy nhiên",
    "thế mà",
    "thế nhưng",
}

# ---------------------------------------------------------------------------
# Repo root — usable by scripts that live one level below root
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# From train/train.py — verbatim
# ---------------------------------------------------------------------------

def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def is_gold_contrast(span_sent_tensor: torch.Tensor) -> bool:
    values = span_sent_tensor[span_sent_tensor != -100]
    return len(values) >= 2 and len(values.unique()) >= 2


def autocast_context(device: torch.device):
    if device.type == "cuda":
        return torch.autocast(device_type="cuda", dtype=torch.float16)
    return nullcontext()


def overlaps(a_start, a_end, b_start, b_end):
    return max(a_start, b_start) < min(a_end, b_end)


def find_contrast_char_spans(text: str):
    text_l = text.lower()
    spans = []
    for phrase in CONTRAST_WORDS:
        pattern = r"\\b" + re.sub(r"\\s+", r"(?:\\s+|_)", re.escape(phrase)) + r"\\b"
        for match in re.finditer(pattern, text_l):
            spans.append((match.start(), match.end()))
    spans.sort()
    return spans


def compute_clause_position(span_start, span_end, offsets_row, text, seq_len):
    contrast_spans = find_contrast_char_spans(text)
    if not contrast_spans:
        return 0

    contrast_token_positions = []
    for idx in range(seq_len):
        cs = int(offsets_row[idx][0])
        ce = int(offsets_row[idx][1])
        if cs == ce:
            continue
        if any(overlaps(cs, ce, ss, se) for ss, se in contrast_spans):
            contrast_token_positions.append(idx)

    if not contrast_token_positions:
        return 0

    contrast_pos = sum(contrast_token_positions) / len(contrast_token_positions)
    center = 0.5 * (span_start + span_end)
    return 1 if center < contrast_pos else 2


def build_offsets_from_tokens(text, tokens, special_tokens_mask):
    text_l = text.lower()
    cursor = 0
    offsets = []

    for tok, is_special in zip(tokens, special_tokens_mask):
        if is_special:
            offsets.append((0, 0))
            continue

        piece = tok or ""
        if piece.startswith("##"):
            piece = piece[2:]

        piece = piece.replace("▁", " ").replace("Ġ", " ")
        piece = piece.strip()

        if not piece:
            offsets.append((0, 0))
            continue

        piece_l = piece.lower()
        idx = text_l.find(piece_l, cursor)
        if idx == -1:
            idx = text_l.find(piece_l)

        if idx == -1:
            offsets.append((0, 0))
            continue

        start = idx
        end = idx + len(piece)
        offsets.append((start, end))
        cursor = end

    return offsets


def load_tokenizer(tokenizer_source: str | Path):
    tokenizer = AutoTokenizer.from_pretrained(str(tokenizer_source), use_fast=True)

    if not getattr(tokenizer, "is_fast", False):
        try:
            tokenizer = AutoTokenizer.from_pretrained(
                str(tokenizer_source), use_fast=True, from_slow=True,
            )
        except TypeError:
            pass

    return tokenizer


def resolve_checkpoint(model_dir: Path) -> Path:
    direct = model_dir / "best_model.pt"
    if direct.is_file():
        return direct

    pointer = model_dir / "pointer.txt"
    if pointer.is_file():
        for line in pointer.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("path="):
                path = Path(line.split("=", 1)[1].strip())
                if path.is_file():
                    return path
                raise FileNotFoundError(f"Checkpoint in pointer.txt not found: {path}")

    raise FileNotFoundError(
        f"Missing checkpoint in {model_dir} (expected best_model.pt or pointer.txt)"
    )


def resolve_config_source(model_dir: Path, run_config: dict) -> str | Path:
    for name in ("backbone", "encoder"):
        local = model_dir / name
        if local.is_dir() and (local / "config.json").is_file():
            return local

    model_name = run_config.get("model_name")
    if not model_name:
        raise ValueError(
            f"run_config.json in {model_dir} must contain model_name "
            "(architecture config only; weights come from best_model.pt)"
        )
    return model_name


def resolve_tokenizer_source(model_dir: Path, run_config: dict) -> str | Path:
    local = model_dir / "tokenizer"
    if local.is_dir() and (local / "tokenizer_config.json").is_file():
        return local
    return resolve_config_source(model_dir, run_config)


# ---------------------------------------------------------------------------
# New IO helpers
# ---------------------------------------------------------------------------

def get_device(device_str: str | None = None) -> torch.device:
    if device_str:
        return torch.device(device_str)
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def md5_file(path: str | Path, chunk_size: int = 1 << 20) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: str | Path) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(obj: Any, path: str | Path, indent: int = 2) -> None:
    ensure_dir(Path(path).parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)


def load_jsonl(path: str | Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def save_jsonl(records: list[dict], path: str | Path) -> None:
    ensure_dir(Path(path).parent)
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
