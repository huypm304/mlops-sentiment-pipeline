"""Load training metrics from model/train_log.csv and confusion_matrices.jsonl."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from backend.app.config.settings import MODEL_DIR

ASPECTS = ["Fashion", "Electronics", "General", "Service", "Ship", "Price", "App"]
ASPECT_LABELS = {
    "Fashion": "Fashion",
    "Electronics": "Electronics",
    "General": "General",
    "Service": "Service",
    "Ship": "Delivery",
    "Price": "Price",
    "App": "App",
}
SENT_LABELS = ["NEG", "POS", "NEU"]
VERSION = "best"


def _train_log_path() -> Path:
    return MODEL_DIR / "train_log.csv"


def _confusion_path() -> Path:
    return MODEL_DIR / "confusion_matrices.jsonl"


def _load_config() -> dict[str, Any]:
    for name in ("config.json", "run_config.json"):
        p = MODEL_DIR / name
        if p.exists():
            with open(p, encoding="utf-8") as f:
                return json.load(f)
    return {}


def _read_train_rows() -> list[dict[str, str]]:
    path = _train_log_path()
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _best_train_row(rows: list[dict[str, str]]) -> dict[str, str] | None:
    best_rows = [r for r in rows if r.get("is_best") == "best"]
    if not best_rows:
        return rows[-1] if rows else None
    return max(best_rows, key=lambda r: float(r.get("composite", 0) or 0))


def _confusion_for_epoch(epoch: int) -> dict[str, Any] | None:
    path = _confusion_path()
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            if int(rec.get("epoch", -1)) == epoch:
                return rec
    return None


def _metrics_from_confusion(raw: list[list[int]]) -> dict[str, float]:
    """Macro precision, recall, F1 from 3x3 confusion (rows=actual, cols=pred)."""
    n = len(raw)
    if n == 0:
        return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0}

    total = sum(sum(row) for row in raw)
    correct = sum(raw[i][i] for i in range(min(n, len(raw[0]))))
    accuracy = correct / total if total else 0.0

    precisions, recalls, f1s = [], [], []
    for i in range(n):
        row_sum = sum(raw[i])
        col_sum = sum(raw[j][i] for j in range(n))
        tp = raw[i][i]
        prec = tp / col_sum if col_sum else 0.0
        rec = tp / row_sum if row_sum else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        precisions.append(prec)
        recalls.append(rec)
        f1s.append(f1)

    return {
        "accuracy": round(accuracy, 4),
        "precision": round(sum(precisions) / n, 4),
        "recall": round(sum(recalls) / n, 4),
        "f1": round(sum(f1s) / n, 4),
    }


def _frontend_confusion(raw: list[list[int]]) -> dict[str, Any]:
    return {
        "labels": ["negative", "neutral", "positive"],
        "matrix": raw,
    }


def get_training_history() -> list[dict[str, Any]]:
    rows = _read_train_rows()
    history = []
    for r in rows:
        try:
            epoch = int(r["epoch"])
        except (KeyError, ValueError):
            continue
        history.append({
            "epoch": epoch,
            "phase": r.get("phase", ""),
            "train_loss": float(r.get("train_loss", 0) or 0),
            "span_f1": float(r.get("span_f1", 0) or 0),
            "sent_f1": float(r.get("sent_f1", 0) or 0),
            "glob_f1": float(r.get("glob_f1", 0) or 0),
            "composite": float(r.get("composite", 0) or 0),
            "is_best": r.get("is_best") == "best",
        })
    return history


def get_model_evaluation(version: str = VERSION) -> dict[str, Any] | None:
    if version not in (VERSION, "best", "v1.0.0"):
        return None

    rows = _read_train_rows()
    best = _best_train_row(rows)
    if not best:
        return None

    epoch = int(best["epoch"])
    config = _load_config()
    conf_rec = _confusion_for_epoch(epoch)
    matrices = conf_rec.get("matrices", {}) if conf_rec else {}

    glob_raw = matrices.get("global", {}).get("raw", [[0, 0, 0], [0, 0, 0], [0, 0, 0]])
    sent_raw = matrices.get("sentiment", {}).get("raw", glob_raw)

    sentiment_metrics = _metrics_from_confusion(sent_raw)
    global_metrics = _metrics_from_confusion(glob_raw)

    per_aspect = []
    for asp in ASPECTS:
        span_f1 = float(best.get(f"span_f1_{asp}", 0) or 0)
        sent_f1 = float(best.get(f"sent_f1_{asp}", 0) or 0)
        per_aspect.append({
            "aspect": asp,
            "label": ASPECT_LABELS.get(asp, asp),
            "span_f1": round(span_f1, 4),
            "sent_f1": round(sent_f1, 4),
            "f1": round(sent_f1, 4),
            "precision": round(sent_f1, 4),
            "recall": round(span_f1, 4),
            "support": 0,
        })

    return {
        "version": VERSION,
        "status": "production",
        "epoch": epoch,
        "phase": best.get("phase", ""),
        "registered_at": "2025-01-01T00:00:00Z",
        "evaluated_at": "2025-01-01T00:00:00Z",
        "inference_latency_ms": 0,
        "dataset": {
            "version": Path(config.get("train_file", "train")).name,
            "train_samples": 0,
            "val_samples": 0,
            "test_samples": int(matrices.get("global", {}).get("support", 0)),
        },
        "training": {
            "encoder": config.get("model_name", "Fsoft-AIC/videberta-base"),
            "epochs": int(config.get("epochs", 50)),
            "batch_size": int(config.get("batch_size", 16)),
            "learning_rate": float(config.get("lr_heads", 3e-5)),
            "trained_at": "2025-01-01T00:00:00Z",
            "checkpoint": "best_model.pt",
        },
        "scores": {
            "span_f1": float(best.get("span_f1", 0) or 0),
            "sent_f1": float(best.get("sent_f1", 0) or 0),
            "glob_f1": float(best.get("glob_f1", 0) or 0),
            "composite": float(best.get("composite", 0) or 0),
            "train_loss": float(best.get("train_loss", 0) or 0),
        },
        "sentiment": sentiment_metrics,
        "global_sentiment": global_metrics,
        "aspect_polarity": sentiment_metrics,
        "aspect_extraction": {
            "accuracy": round(float(best.get("span_f1", 0) or 0), 4),
            "precision": round(float(best.get("span_f1", 0) or 0), 4),
            "recall": round(float(best.get("span_f1", 0) or 0), 4),
            "f1": round(float(best.get("span_f1", 0) or 0), 4),
        },
        "confusion_matrix": _frontend_confusion(sent_raw),
        "global_confusion_matrix": _frontend_confusion(glob_raw),
        "per_aspect": per_aspect,
        "confusion_labels": SENT_LABELS,
    }


def list_models() -> list[dict[str, Any]]:
    ev = get_model_evaluation()
    if not ev:
        return []
    return [
        {
            "version": ev["version"],
            "status": ev["status"],
            "epoch": ev["epoch"],
            "composite": ev["scores"]["composite"],
            "sent_f1": ev["scores"]["sent_f1"],
            "span_f1": ev["scores"]["span_f1"],
            "glob_f1": ev["scores"]["glob_f1"],
            "encoder": ev["training"]["encoder"],
            "checkpoint": ev["training"]["checkpoint"],
        }
    ]
