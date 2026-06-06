"""Production vs training baseline drift for retrain signals."""

from __future__ import annotations

import json
import time
from collections import Counter, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.config.settings import REPO_ROOT

ASPECT_ORDER = [
    "Fashion",
    "Electronics",
    "General",
    "Service",
    "Ship",
    "Price",
    "App",
]
SENTIMENT_KEYS = ["negative", "positive", "neutral"]
SENTIMENT_MAP = {0: "negative", 1: "positive", 2: "neutral"}

BASELINE_PATH = REPO_ROOT / "reports" / "monitoring" / "train_baseline.json"
INFERENCE_LOG_PATH = REPO_ROOT / "reports" / "monitoring" / "inference_log.jsonl"
TRAIN_DATASET = REPO_ROOT / "model" / "data_train.jsonl"

DRIFT_THRESHOLD = 0.18
MIN_PRODUCTION_SAMPLES = 5

_inference_log: deque[dict[str, Any]] = deque(maxlen=2000)
_baseline_cache: dict[str, Any] | None = None


def _normalize_sentiment(label: str) -> str:
    s = label.strip().lower()
    if s in SENTIMENT_KEYS:
        return s
    if s in ("neg", "negative", "0"):
        return "negative"
    if s in ("pos", "positive", "1"):
        return "positive"
    return "neutral"


def _dist_from_counter(counter: Counter[str], keys: list[str]) -> dict[str, float]:
    total = sum(counter.get(k, 0) for k in keys) or 1
    return {k: round(counter.get(k, 0) / total, 4) for k in keys}


def _l1_drift(a: dict[str, float], b: dict[str, float], keys: list[str]) -> float:
    return round(sum(abs(a.get(k, 0) - b.get(k, 0)) for k in keys) / 2, 4)


def _load_jsonl(path: Path, max_lines: int | None = None) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.is_file():
        return records
    with path.open(encoding="utf-8") as f:
        for i, line in enumerate(f):
            if max_lines is not None and i >= max_lines:
                break
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def _build_baseline_from_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    aspect_c: Counter[str] = Counter()
    global_c: Counter[str] = Counter()
    lengths: list[int] = []

    for rec in records:
        text = rec.get("text") or ""
        lengths.append(len(str(text)))
        gs = rec.get("global_sentiment")
        if gs in SENTIMENT_MAP:
            global_c[SENTIMENT_MAP[int(gs)]] += 1
        elif isinstance(gs, str):
            global_c[_normalize_sentiment(gs)] += 1

        for op in rec.get("opinions") or []:
            asp = op.get("aspect")
            if asp in ASPECT_ORDER:
                aspect_c[str(asp)] += 1
            sent = op.get("sentiment")
            if sent in SENTIMENT_MAP:
                pass  # opinion-level tracked via aspects only for aspect chart
            elif isinstance(sent, str):
                pass

    return {
        "source": str(TRAIN_DATASET),
        "sample_size": len(records),
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "aspect_distribution": _dist_from_counter(aspect_c, ASPECT_ORDER),
        "global_sentiment_distribution": _dist_from_counter(global_c, SENTIMENT_KEYS),
        "avg_text_length": round(sum(lengths) / len(lengths), 1) if lengths else 0,
    }


def get_train_baseline(*, refresh: bool = False) -> dict[str, Any]:
    global _baseline_cache
    if _baseline_cache is not None and not refresh:
        return _baseline_cache

    if BASELINE_PATH.is_file() and not refresh:
        _baseline_cache = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        return _baseline_cache

    records = _load_jsonl(TRAIN_DATASET, max_lines=8000)
    if not records:
        records = _load_jsonl(REPO_ROOT / "model" / "demo_10.jsonl")
    baseline = _build_baseline_from_records(records)
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8")
    _baseline_cache = baseline
    return baseline


def record_inference(
    *,
    global_sentiment: str,
    global_confidence: float,
    opinions: list[dict[str, Any]],
    latency_ms: int,
) -> None:
    aspects = [str(o.get("aspect", "")) for o in opinions if o.get("aspect")]
    op_sents = [_normalize_sentiment(str(o.get("sentiment", "neutral"))) for o in opinions]
    confs = [float(o.get("confidence", 0)) for o in opinions if o.get("confidence") is not None]
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "global_sentiment": _normalize_sentiment(global_sentiment),
        "global_confidence": round(global_confidence, 4),
        "aspects": aspects,
        "opinion_sentiments": op_sents,
        "avg_opinion_confidence": round(sum(confs) / len(confs), 4) if confs else 0.0,
        "latency_ms": latency_ms,
    }
    _inference_log.append(entry)
    try:
        INFERENCE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with INFERENCE_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _production_window(entries: list[dict[str, Any]]) -> dict[str, Any]:
    aspect_c: Counter[str] = Counter()
    global_c: Counter[str] = Counter()
    confs: list[float] = []
    gconfs: list[float] = []

    for e in entries:
        global_c[e.get("global_sentiment", "neutral")] += 1
        gconfs.append(float(e.get("global_confidence", 0)))
        for asp in e.get("aspects") or []:
            if asp in ASPECT_ORDER:
                aspect_c[asp] += 1
        if e.get("avg_opinion_confidence"):
            confs.append(float(e["avg_opinion_confidence"]))

    return {
        "sample_size": len(entries),
        "aspect_distribution": _dist_from_counter(aspect_c, ASPECT_ORDER),
        "global_sentiment_distribution": _dist_from_counter(global_c, SENTIMENT_KEYS),
        "avg_confidence": round(sum(confs) / len(confs), 4) if confs else 0.0,
        "avg_global_confidence": round(sum(gconfs) / len(gconfs), 4) if gconfs else 0.0,
    }


def _hydrate_log_from_disk() -> None:
    if _inference_log or not INFERENCE_LOG_PATH.is_file():
        return
    for line in INFERENCE_LOG_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            _inference_log.append(json.loads(line))
        except json.JSONDecodeError:
            continue


def get_drift_report() -> dict[str, Any]:
    _hydrate_log_from_disk()
    baseline = get_train_baseline()
    entries = list(_inference_log)
    production = _production_window(entries)

    n = production["sample_size"]
    if n < MIN_PRODUCTION_SAMPLES:
        return {
            "status": "insufficient_data",
            "message": f"Need at least {MIN_PRODUCTION_SAMPLES} predictions (have {n})",
            "production_sample_size": n,
            "baseline": baseline,
            "production": production,
            "drift_score": 0.0,
            "aspect_drift": 0.0,
            "sentiment_drift": 0.0,
            "confidence_delta": 0.0,
            "suggest_retrain": False,
            "signals": [],
            "comparison": [],
        }

    aspect_drift = _l1_drift(
        baseline["aspect_distribution"],
        production["aspect_distribution"],
        ASPECT_ORDER,
    )
    sentiment_drift = _l1_drift(
        baseline["global_sentiment_distribution"],
        production["global_sentiment_distribution"],
        SENTIMENT_KEYS,
    )
    drift_score = round(0.6 * aspect_drift + 0.4 * sentiment_drift, 4)

    avg_conf = production["avg_global_confidence"]
    confidence_delta = round(0.7 - avg_conf, 4) if avg_conf else 0.0

    signals: list[str] = []
    if aspect_drift >= DRIFT_THRESHOLD:
        signals.append("Aspect distribution shifted vs training data")
    if sentiment_drift >= DRIFT_THRESHOLD:
        signals.append("Global sentiment mix shifted vs training data")
    if avg_conf and avg_conf < 0.55:
        signals.append("Low average prediction confidence")
    if drift_score >= DRIFT_THRESHOLD:
        signals.append("Overall drift exceeds threshold — consider audit & retrain")

    suggest_retrain = drift_score >= DRIFT_THRESHOLD or len(signals) >= 2

    comparison = []
    for asp in ASPECT_ORDER:
        b = baseline["aspect_distribution"].get(asp, 0)
        p = production["aspect_distribution"].get(asp, 0)
        comparison.append(
            {
                "name": asp,
                "baseline": b,
                "production": p,
                "delta": round(p - b, 4),
            }
        )
    for sk in SENTIMENT_KEYS:
        b = baseline["global_sentiment_distribution"].get(sk, 0)
        p = production["global_sentiment_distribution"].get(sk, 0)
        comparison.append(
            {
                "name": f"sentiment:{sk}",
                "baseline": b,
                "production": p,
                "delta": round(p - b, 4),
            }
        )

    status = "alert" if suggest_retrain else "ok"
    if drift_score >= DRIFT_THRESHOLD * 0.7:
        status = "warning"

    return {
        "status": status,
        "message": "Drift within normal range"
        if status == "ok"
        else "Elevated drift — review before next training cycle",
        "production_sample_size": n,
        "baseline": baseline,
        "production": production,
        "drift_score": drift_score,
        "aspect_drift": aspect_drift,
        "sentiment_drift": sentiment_drift,
        "confidence_delta": confidence_delta,
        "threshold": DRIFT_THRESHOLD,
        "suggest_retrain": suggest_retrain,
        "signals": signals,
        "comparison": comparison,
    }
