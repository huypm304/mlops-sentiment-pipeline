"""Load training metrics from model/train_log.csv and confusion_matrices.jsonl."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
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
VERSION = "absa-v1"
PRIMARY_METRIC = "tas_relaxed_f1"


def _float(row: dict[str, str], *keys: str) -> float:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            try:
                return float(value)
            except ValueError:
                continue
    return 0.0


def _train_log_path() -> Path:
    return MODEL_DIR / "train_log.csv"


def _confusion_path() -> Path:
    return MODEL_DIR / "confusion_matrices.jsonl"


def _artifact_timestamp(path: Path | None = None) -> str:
    target = path or _train_log_path()
    if target.exists():
        ts = datetime.fromtimestamp(target.stat().st_mtime, tz=timezone.utc)
        return ts.isoformat().replace("+00:00", "Z")
    return ""


def _scores_from_row(row: dict[str, str]) -> dict[str, float]:
    """Map train_log.csv columns to canonical evaluation score names."""
    return {
        "tas_strict_f1": _float(row, "tas_strict_f1"),
        "tas_relaxed_f1": _float(row, "tas_relaxed_f1", "composite"),
        "span_f1": _float(row, "span_f1"),
        "sent_matched_f1": _float(row, "sent_matched_f1", "sent_f1"),
        "sent_goldspan_f1": _float(row, "sent_goldspan_f1"),
        "global_f1": _float(row, "global_f1", "glob_f1"),
        "train_loss": _float(row, "train_loss"),
    }


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
    if not rows:
        return None
    best_rows = [r for r in rows if r.get("is_best") == "best"]
    candidates = best_rows or rows
    return max(candidates, key=lambda r: _float(r, "tas_relaxed_f1", "composite"))


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


def _history_from_row(row: dict[str, str], epoch: int) -> dict[str, Any]:
    scores = _scores_from_row(row)
    return {
        "epoch": epoch,
        "phase": row.get("phase", ""),
        **scores,
        "is_best": row.get("is_best") == "best",
    }


def get_training_history() -> list[dict[str, Any]]:
    rows = _read_train_rows()
    history = []
    for r in rows:
        try:
            epoch = int(r["epoch"])
        except (KeyError, ValueError):
            continue
        history.append(_history_from_row(r, epoch))
    return history


def get_model_evaluation(version: str = VERSION) -> dict[str, Any] | None:
    if version not in (VERSION, "best", "v1.0.0", "absa-v1"):
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

    scores = _scores_from_row(best)
    artifact_ts = _artifact_timestamp()

    return {
        "version": VERSION,
        "status": "production",
        "epoch": epoch,
        "phase": best.get("phase", ""),
        "primary_metric": PRIMARY_METRIC,
        "registered_at": artifact_ts,
        "evaluated_at": artifact_ts,
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
            "trained_at": artifact_ts,
            "checkpoint": "best_model.pt",
        },
        "scores": scores,
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
    from backend.app.services import registry_db

    store = registry_db.get_store()
    if store is not None and store.config.models_table:
        rows = store.list_models(limit=20)
        if rows:
            return [
                {
                    "version": row.get("model_id", row.get("version", "absa-v1")),
                    "status": str(row.get("status", "production")).lower(),
                    "primary_metric": "global_f1",
                    "global_f1": float((row.get("metrics") or {}).get("global_f1", 0)),
                    "span_f1": float((row.get("metrics") or {}).get("span_f1", 0)),
                    "tas_relaxed_f1": float((row.get("metrics") or {}).get("tas_f1", 0)),
                    "encoder": row.get("source", "sagemaker_training"),
                    "checkpoint": row.get("artifact_prefix", ""),
                }
                for row in rows
            ]

    ev = get_model_evaluation()
    if not ev:
        return []
    scores = ev["scores"]
    return [
        {
            "version": ev["version"],
            "status": ev["status"],
            "epoch": ev["epoch"],
            "primary_metric": PRIMARY_METRIC,
            "tas_strict_f1": scores["tas_strict_f1"],
            "tas_relaxed_f1": scores["tas_relaxed_f1"],
            "span_f1": scores["span_f1"],
            "sent_matched_f1": scores["sent_matched_f1"],
            "sent_goldspan_f1": scores["sent_goldspan_f1"],
            "global_f1": scores["global_f1"],
            "encoder": ev["training"]["encoder"],
            "checkpoint": ev["training"]["checkpoint"],
        }
    ]
