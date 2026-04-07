#!/usr/bin/env python3
"""Offline labeler for JSONL dataset with 4 heads (no domain keyword rules).

Fills:
- aspect_detection: subset of [Product, Price, Ship, Service, App]
- aspect_sentiment: per detected aspect (0 neg, 1 pos, 2 neu)
- global_sentiment: kept as-is
- ota_tags: BIO tags aligned to whitespace tokenization

Constraints:
- Must NOT rely on hand-crafted domain keyword lists.
- Must keep global_sentiment unchanged.
- Must satisfy len(ota_tags) == len(text.split()).

Method:
- Aspect detection: supervised multi-label classifier trained from
  data/processed/aspect.csv (TF-IDF char ngrams + LogisticRegression OVR).
- Aspect sentiment: set equal to global_sentiment for each detected aspect.
- OTA targets: extract noun phrases with underthesea.chunk() and mark up to
  a small number of non-overlapping noun-phrase spans as opinion targets.

This is designed to be deterministic, offline, and more robust than keyword
matching, while still lightweight.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier

from underthesea import chunk

ASPECT_ORDER: list[str] = ["Product", "Price", "Ship", "Service", "App"]

CSV_ASPECT_COLUMNS: list[tuple[str, str]] = [
    ("is_PRODUCT", "Product"),
    ("is_PRICE", "Price"),
    ("is_SHIPPING", "Ship"),
    ("is_SERVICE", "Service"),
    ("is_PLATFORM", "App"),
]

# Minimal stopwords for OTA candidate filtering (not domain-specific)
STOPWORDS: set[str] = {
    "a",
    "à",
    "ạ",
    "ai",
    "anh",
    "bạn",
    "bị",
    "cả",
    "các",
    "cái",
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
    "hay",
    "hết",
    "hơn",
    "họ",
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


def _is_candidate_token(tok: str) -> bool:
    t = _norm(tok)
    if not t:
        return False
    if t in STOPWORDS:
        return False
    if t.isdigit():
        return False
    if not _WORD_RE.match(t):
        return False
    if len(t) <= 1:
        return False
    return True


@dataclass
class AspectModel:
    vectorizer: TfidfVectorizer
    clf: OneVsRestClassifier
    labels: list[str]  # canonical aspect order aligned to clf outputs


def train_aspect_model(aspect_csv: Path) -> AspectModel:
    df = pd.read_csv(aspect_csv)
    if "feedback_text" not in df.columns:
        raise ValueError("aspect.csv must contain feedback_text")

    y_cols = [c for c, _ in CSV_ASPECT_COLUMNS]
    for c in y_cols:
        if c not in df.columns:
            raise ValueError(f"aspect.csv missing column: {c}")

    texts = df["feedback_text"].fillna("").astype(str).tolist()
    Y = df[y_cols].fillna(0).astype(int).to_numpy()

    # Char n-grams work well for Vietnamese (robust to segmentation / typos).
    vectorizer = TfidfVectorizer(
        analyzer="char",
        ngram_range=(3, 6),
        min_df=2,
        max_features=200_000,
    )

    X = vectorizer.fit_transform(texts)

    base = LogisticRegression(
        max_iter=1000,
        n_jobs=-1,
        class_weight="balanced",
        solver="lbfgs",
    )
    clf = OneVsRestClassifier(base)
    clf.fit(X, Y)

    labels = [canon for _, canon in CSV_ASPECT_COLUMNS]
    return AspectModel(vectorizer=vectorizer, clf=clf, labels=labels)


def load_or_train_aspect_model(cache_path: Path, aspect_csv: Path) -> AspectModel:
    if cache_path.exists():
        obj = joblib.load(cache_path)
        return AspectModel(**obj)

    model = train_aspect_model(aspect_csv)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "vectorizer": model.vectorizer,
            "clf": model.clf,
            "labels": model.labels,
        },
        cache_path,
    )
    return model


def predict_aspects(model: AspectModel, text: str, threshold: float) -> list[str]:
    X = model.vectorizer.transform([text])
    # predict_proba returns list for some estimators; normalize to ndarray
    probs = model.clf.predict_proba(X)
    probs = np.asarray(probs)[0]

    detected = [lab for lab, p in zip(model.labels, probs) if float(p) >= threshold]

    # Canonical order
    detected_set = set(detected)
    return [a for a in ASPECT_ORDER if a in detected_set]


def extract_np_spans_underthesea(tokens: Sequence[str], text: str) -> list[tuple[int, int]]:
    """Extract noun-phrase spans aligned to whitespace tokens.

    Returns spans (start, end_exclusive) in token indices.
    If alignment fails, returns empty list.
    """
    ch = chunk(text)
    ch_tokens = [w for (w, _pos, _chunk) in ch]

    # Strict alignment to whitespace tokens.
    # If token lists differ, we refuse to map spans (avoid off-by-one errors).
    if list(tokens) != ch_tokens:
        return []

    spans: list[tuple[int, int]] = []
    i = 0
    while i < len(ch):
        w, pos, ck = ch[i]
        if ck == "B-NP":
            j = i + 1
            while j < len(ch) and ch[j][2] == "I-NP":
                j += 1
            spans.append((i, j))
            i = j
        else:
            i += 1

    # Filter spans to ones with at least one candidate token
    filtered: list[tuple[int, int]] = []
    for s, e in spans:
        span_toks = tokens[s:e]
        if any(_is_candidate_token(t) for t in span_toks):
            filtered.append((s, e))
    return filtered


def choose_ota_spans(tokens: Sequence[str], text: str, max_spans: int = 2) -> list[tuple[int, int]]:
    spans = extract_np_spans_underthesea(tokens, text)

    def score_span(s: int, e: int) -> float:
        span = tokens[s:e]
        score = float(e - s)
        score += 0.5 * sum(1 for t in span if "_" in t)
        score += 0.2 * sum(1 for t in span if _is_candidate_token(t))
        # Prefer earlier spans slightly
        score += 0.05 * max(0, (10 - s))
        return score

    spans_scored = sorted(((score_span(s, e), s, e) for s, e in spans), reverse=True)

    chosen: list[tuple[int, int]] = []
    occupied = [False] * len(tokens)
    for _sc, s, e in spans_scored:
        if len(chosen) >= max_spans:
            break
        if any(occupied[i] for i in range(s, e)):
            continue
        for i in range(s, e):
            occupied[i] = True
        chosen.append((s, e))

    if chosen:
        return sorted(chosen)

    # Fallback: tag up to 2 standalone candidate tokens (still no domain keywords)
    fallback: list[tuple[int, int]] = []
    for i, t in enumerate(tokens):
        if _is_candidate_token(t):
            fallback.append((i, i + 1))
        if len(fallback) >= max_spans:
            break
    return fallback


def label_ota(tokens: Sequence[str], text: str) -> list[str]:
    tags = ["O"] * len(tokens)
    spans = choose_ota_spans(tokens, text)
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
    ap.add_argument(
        "--aspect-csv",
        type=Path,
        default=Path("data/processed/aspect.csv"),
        help="Path to aspect-labeled CSV",
    )
    ap.add_argument(
        "--aspect-model-cache",
        type=Path,
        default=Path("data/models/aspect_model.joblib"),
        help="Cache path for trained aspect model",
    )
    ap.add_argument("--aspect-threshold", type=float, default=0.55)
    ap.add_argument("--max-ota-spans", type=int, default=2)
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

    aspect_model = load_or_train_aspect_model(args.aspect_model_cache, args.aspect_csv)

    new_lines: list[str] = []
    for obj in iter_jsonl(inp):
        text = str(obj["text"])
        heads = obj["heads"]

        global_sent = heads.get("global_sentiment")
        if global_sent not in (0, 1, 2):
            raise ValueError(f"Invalid global_sentiment: {global_sent!r} for text={text!r}")

        tokens = tokenize(text)

        aspects = predict_aspects(aspect_model, text, threshold=float(args.aspect_threshold))
        aspect_sent = {a: int(global_sent) for a in aspects}

        ota = label_ota(tokens, text)
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
