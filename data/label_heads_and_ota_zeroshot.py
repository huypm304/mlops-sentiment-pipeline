#!/usr/bin/env python3
"""Zero-shot label JSONL dataset with 4 heads (no keyword heuristics).

Fills:
- aspect_detection: subset of [Product, Price, Ship, Service, App]
- aspect_sentiment: per detected aspect (0 neg, 1 pos, 2 neu)
- global_sentiment: kept as-is
- ota_tags: BIO tags aligned to whitespace tokenization (len == len(text.split()))

Approach:
- Aspect detection: zero-shot multi-label classification using an XNLI model.
- Aspect sentiment: NLI scoring against hypotheses per aspect (pos/neg/neu).
- OTA targets: unsupervised keyphrase extraction (RAKE-like) over whitespace tokens,
  then mark top non-overlapping spans with BIO tags.

This is intended as a stronger baseline than keyword matching while staying fully
rule-free w.r.t. domain keywords.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

ASPECT_ORDER: list[str] = ["Product", "Price", "Ship", "Service", "App"]

# Zero-shot labels in Vietnamese mapped to canonical aspects.
ASPECT_LABELS_VI: list[str] = ["sản phẩm", "giá cả", "giao hàng", "dịch vụ", "ứng dụng"]
ASPECT_VI_TO_CANON: dict[str, str] = {
    "sản phẩm": "Product",
    "giá cả": "Price",
    "giao hàng": "Ship",
    "dịch vụ": "Service",
    "ứng dụng": "App",
}

# A small Vietnamese stopword list for keyphrase extraction.
# (Not domain-specific; kept minimal and safe.)
STOPWORDS: set[str] = {
    "a",
    "à",
    "ạ",
    "ae",
    "ai",
    "anh",
    "bạn",
    "bởi",
    "bị",
    "cả",
    "các",
    "cái",
    "cần",
    "chỉ",
    "cho",
    "chưa",
    "chứ",
    "có",
    "cũng",
    "của",
    "cùng",
    "cứ",
    "đang",
    "để",
    "đến",
    "đi",
    "đó",
    "được",
    "đừng",
    "em",
    "gì",
    "giờ",
    "giữa",
    "hay",
    "hết",
    "hơn",
    "họ",
    "khá",
    "khi",
    "không",
    "là",
    "lại",
    "lên",
    "luôn",
    "mà",
    "mình",
    "mỗi",
    "một",
    "mọi",
    "muốn",
    "này",
    "nên",
    "nhé",
    "như",
    "nữa",
    "nếu",
    "ngày",
    "người",
    "nhiều",
    "những",
    "nói",
    "ở",
    "ra",
    "rất",
    "rồi",
    "sao",
    "sẽ",
    "so",
    "tại",
    "thì",
    "thôi",
    "thật",
    "tôi",
    "trên",
    "trong",
    "từ",
    "và",
    "vậy",
    "vì",
    "với",
    "vừa",
    "vẫn",
}


def tokenize(text: str) -> list[str]:
    return text.split()


def _norm(tok: str) -> str:
    return tok.strip().lower()


_WORD_RE = re.compile(r"^[\wÀ-ỹ_]+$", flags=re.UNICODE)


def _is_candidate(tok: str) -> bool:
    t = _norm(tok)
    if not t:
        return False
    if t in STOPWORDS:
        return False
    if t.isdigit():
        return False
    if not _WORD_RE.match(t):
        return False
    # Avoid tagging 1-char noise.
    if len(t) <= 1:
        return False
    return True


@dataclass
class NLI:
    tokenizer: AutoTokenizer
    model: AutoModelForSequenceClassification
    entailment_id: int


def _infer_entailment_id(model: AutoModelForSequenceClassification, tokenizer: AutoTokenizer) -> int:
    # Try to infer which label corresponds to entailment.
    cfg = getattr(model, "config", None)
    label2id = getattr(cfg, "label2id", {}) or {}
    # Common mappings
    for key in ("ENTAILMENT", "entailment", "LABEL_2"):
        if key in label2id:
            return int(label2id[key])
    # If id2label exists, search
    id2label = getattr(cfg, "id2label", {}) or {}
    for i, lab in id2label.items():
        if str(lab).lower() == "entailment":
            return int(i)
    # Fallback: many NLI models use [contradiction, neutral, entailment]
    return 2


def nli_score_entailment(nli: NLI, premise: str, hypothesis: str) -> float:
    inputs = nli.tokenizer(premise, hypothesis, return_tensors="pt", truncation=True)
    with torch.no_grad():
        logits = nli.model(**inputs).logits[0]
        probs = torch.softmax(logits, dim=-1)
    return float(probs[nli.entailment_id].item())


def detect_aspects_zero_shot(zs, text: str, threshold: float = 0.55) -> list[str]:
    out = zs(text, ASPECT_LABELS_VI, multi_label=True)
    # out['labels'] sorted by score desc
    detected: list[str] = []
    for lab, score in zip(out["labels"], out["scores"]):
        if score >= threshold:
            detected.append(ASPECT_VI_TO_CANON[lab])
    # Keep canonical order
    detected = [a for a in ASPECT_ORDER if a in set(detected)]

    # If nothing passes threshold but the model is confident about a single label,
    # take top-1 with a softer threshold.
    if not detected and out["labels"]:
        top_lab = out["labels"][0]
        top_score = float(out["scores"][0])
        if top_score >= 0.40:
            detected = [ASPECT_VI_TO_CANON[top_lab]]

    return detected


def aspect_sentiment_nli(nli: NLI, text: str, aspect: str, global_sentiment: int) -> int:
    # Hypotheses are Vietnamese and include aspect context.
    aspect_vi = {
        "Product": "sản phẩm",
        "Price": "giá cả",
        "Ship": "giao hàng",
        "Service": "dịch vụ",
        "App": "ứng dụng",
    }[aspect]

    hyps = {
        1: f"Nhận xét này về {aspect_vi} là tích cực.",
        0: f"Nhận xét này về {aspect_vi} là tiêu cực.",
        2: f"Nhận xét này về {aspect_vi} là trung lập.",
    }

    scores = {k: nli_score_entailment(nli, text, h) for k, h in hyps.items()}
    best = max(scores.items(), key=lambda kv: kv[1])[0]

    # If the model is not confident, fall back to global_sentiment.
    if float(scores[best]) < 0.40:
        return int(global_sentiment)
    return int(best)


def extract_keyphrases_rake(tokens: Sequence[str], max_phrases: int = 2, max_len: int = 3) -> list[tuple[int, int]]:
    """Return list of (start, end_exclusive) spans in token indices."""
    # Build candidate phrases: contiguous runs of candidate tokens.
    candidates: list[list[str]] = []
    candidate_spans: list[tuple[int, int]] = []

    i = 0
    while i < len(tokens):
        if _is_candidate(tokens[i]):
            j = i
            while j < len(tokens) and _is_candidate(tokens[j]):
                j += 1
            # Split long runs into up to max_len chunks (prefer shorter phrases).
            run = tokens[i:j]
            # Generate phrases up to max_len within the run.
            for start in range(0, len(run)):
                for L in range(1, max_len + 1):
                    if start + L <= len(run):
                        candidates.append([_norm(t) for t in run[start : start + L]])
                        candidate_spans.append((i + start, i + start + L))
            i = j
        else:
            i += 1

    if not candidates:
        return []

    # RAKE scoring
    freq: dict[str, int] = {}
    degree: dict[str, int] = {}
    for phrase in candidates:
        unique = phrase
        deg = max(1, len(unique) - 1)
        for w in unique:
            freq[w] = freq.get(w, 0) + 1
            degree[w] = degree.get(w, 0) + deg

    word_score = {w: (degree[w] + freq[w]) / freq[w] for w in freq}

    phrase_scores: list[tuple[float, int]] = []
    for idx, phrase in enumerate(candidates):
        score = sum(word_score.get(w, 0.0) for w in phrase)
        # Slightly prefer longer phrases (still capped by max_len)
        score *= 1.0 + 0.10 * (len(phrase) - 1)
        phrase_scores.append((score, idx))

    phrase_scores.sort(reverse=True, key=lambda x: x[0])

    # Pick top non-overlapping spans.
    chosen: list[tuple[int, int]] = []
    occupied = [False] * len(tokens)

    for score, idx in phrase_scores:
        if len(chosen) >= max_phrases:
            break
        s, e = candidate_spans[idx]
        if s >= e:
            continue
        if any(occupied[k] for k in range(s, e)):
            continue
        # Filter out ultra-short low-signal phrases.
        if score < 2.0:
            continue
        for k in range(s, e):
            occupied[k] = True
        chosen.append((s, e))

    chosen.sort()
    return chosen


def label_ota_from_phrases(tokens: Sequence[str]) -> list[str]:
    tags = ["O"] * len(tokens)
    spans = extract_keyphrases_rake(tokens)
    for s, e in spans:
        if s < 0 or e > len(tokens) or s >= e:
            continue
        tags[s] = "B-OTA"
        for i in range(s + 1, e):
            tags[i] = "I-OTA"
    return tags


def iter_jsonl(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            obj = json.loads(line)
            if "text" not in obj or "heads" not in obj:
                raise ValueError(f"Missing keys at line {line_no}")
            if not isinstance(obj["heads"], dict):
                raise ValueError(f"heads must be dict at line {line_no}")
            yield obj


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inplace", action="store_true", help="Rewrite input file in place")
    ap.add_argument("--model", default="joeddav/xlm-roberta-base-xnli", help="XNLI/NLI model for zero-shot")
    ap.add_argument("--aspect-threshold", type=float, default=0.55)
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path, nargs="?")
    args = ap.parse_args()

    inp: Path = args.input
    out: Path
    if args.inplace:
        out = inp
    else:
        if args.output is None:
            raise SystemExit("output is required unless --inplace")
        out = args.output

    device = -1
    zs = pipeline(
        "zero-shot-classification",
        model=args.model,
        device=device,
    )

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForSequenceClassification.from_pretrained(args.model)
    model.eval()
    entailment_id = _infer_entailment_id(model, tokenizer)
    nli = NLI(tokenizer=tokenizer, model=model, entailment_id=entailment_id)

    new_lines: list[str] = []
    for obj in iter_jsonl(inp):
        text = str(obj["text"])
        heads = obj["heads"]

        global_sent = heads.get("global_sentiment")
        if global_sent not in (0, 1, 2):
            raise ValueError(f"Invalid global_sentiment: {global_sent!r} for text={text!r}")

        tokens = tokenize(text)

        aspects = detect_aspects_zero_shot(zs, text, threshold=float(args.aspect_threshold))

        aspect_sent: dict[str, int] = {}
        for a in aspects:
            aspect_sent[a] = aspect_sentiment_nli(nli, text, a, int(global_sent))

        ota = label_ota_from_phrases(tokens)
        if len(ota) != len(tokens):
            raise AssertionError("ota_tags length mismatch")

        obj["heads"] = {
            "aspect_detection": aspects,
            "aspect_sentiment": aspect_sent,
            "global_sentiment": global_sent,
            "ota_tags": ota,
        }

        new_lines.append(json.dumps(obj, ensure_ascii=False) + "\n")

    tmp_path = out
    if args.inplace:
        tmp_path = out.with_suffix(out.suffix + ".tmp")

    tmp_path.write_text("".join(new_lines), encoding="utf-8")

    if args.inplace:
        tmp_path.replace(out)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
