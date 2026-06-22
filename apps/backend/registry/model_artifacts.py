"""Load model evaluation artifacts from S3 (train_log.csv, run_config.json, confusion)."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any

from botocore.exceptions import ClientError

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
PRIMARY_METRIC = "tas_relaxed_f1"

DEFAULT_PREFIX_BY_MODEL: dict[str, list[str]] = {
    "absa-v2b": ["models/v1", "models/candidates/run1a_phobert"],
    "absa-v1": ["models/v1"],
}


def resolve_artifact_prefixes(model_id: str, registry_row: dict[str, Any] | None = None) -> list[str]:
    if registry_row and registry_row.get("artifact_prefix"):
        return [str(registry_row["artifact_prefix"]).strip("/")]
    return DEFAULT_PREFIX_BY_MODEL.get(model_id, [f"models/candidates/{model_id}"])


def _float(row: dict[str, str], *keys: str) -> float:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            try:
                return float(value)
            except ValueError:
                continue
    return 0.0


def _scores_from_row(row: dict[str, str]) -> dict[str, float]:
    return {
        "tas_strict_f1": _float(row, "tas_strict_f1"),
        "tas_relaxed_f1": _float(row, "tas_relaxed_f1", "composite"),
        "span_f1": _float(row, "span_f1"),
        "sent_matched_f1": _float(row, "sent_matched_f1", "sent_f1"),
        "sent_goldspan_f1": _float(row, "sent_goldspan_f1"),
        "global_f1": _float(row, "global_f1", "glob_f1"),
        "train_loss": _float(row, "train_loss"),
    }


def _best_train_row(rows: list[dict[str, str]]) -> dict[str, str] | None:
    if not rows:
        return None
    best_rows = [r for r in rows if r.get("is_best") == "best"]
    candidates = best_rows or rows
    return max(candidates, key=lambda r: _float(r, "tas_relaxed_f1", "composite", "global_f1"))


def _parse_train_log(text: str) -> list[dict[str, str]]:
    if not text.strip():
        return []
    return list(csv.DictReader(io.StringIO(text)))


def _parse_config(text: str | None) -> dict[str, Any]:
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def _confusion_for_epoch(lines: list[str], epoch: int) -> dict[str, Any] | None:
    for line in lines:
        if not line.strip():
            continue
        rec = json.loads(line)
        if int(rec.get("epoch", -1)) == epoch:
            return rec
    return None


def _metrics_from_confusion(raw: list[list[int]]) -> dict[str, float]:
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


def build_training_history(train_log_text: str) -> list[dict[str, Any]]:
    history: list[dict[str, Any]] = []
    for row in _parse_train_log(train_log_text):
        try:
            epoch = int(row["epoch"])
        except (KeyError, ValueError):
            continue
        history.append(_history_from_row(row, epoch))
    return history


def build_evaluation_payload(
    *,
    model_id: str,
    train_log_text: str,
    run_config_text: str | None,
    confusion_text: str | None,
    artifact_prefix: str,
    registry_row: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    rows = _parse_train_log(train_log_text)
    best = _best_train_row(rows)
    if not best:
        return None

    epoch = int(best["epoch"])
    config = _parse_config(run_config_text)
    confusion_lines = (confusion_text or "").splitlines()
    conf_rec = _confusion_for_epoch(confusion_lines, epoch)
    matrices = conf_rec.get("matrices", {}) if conf_rec else {}

    glob_raw = matrices.get("global", {}).get("raw", [[0, 0, 0], [0, 0, 0], [0, 0, 0]])
    sent_raw = matrices.get("sentiment", {}).get("raw", glob_raw)

    sentiment_metrics = _metrics_from_confusion(sent_raw)
    global_metrics = _metrics_from_confusion(glob_raw)
    scores = _scores_from_row(best)

    encoder = (
        (registry_row or {}).get("encoder")
        or config.get("model_name")
        or "unknown"
    )
    status = str((registry_row or {}).get("status", "production")).lower()
    registered_at = (registry_row or {}).get("registered_at") or _iso_now()
    evaluated_at = registered_at

    per_aspect = []
    for asp in ASPECTS:
        span_f1 = float(best.get(f"span_f1_{asp}", 0) or 0)
        sent_f1 = float(best.get(f"sent_f1_{asp}", 0) or 0)
        per_aspect.append(
            {
                "aspect": asp,
                "label": ASPECT_LABELS.get(asp, asp),
                "span_f1": round(span_f1, 4),
                "sent_f1": round(sent_f1, 4),
                "f1": round(sent_f1, 4),
                "precision": round(sent_f1, 4),
                "recall": round(span_f1, 4),
                "support": 0,
            }
        )

    bucket = (registry_row or {}).get("_bucket") or ""
    base_uri = f"s3://{bucket}/{artifact_prefix}" if bucket else artifact_prefix

    return {
        "version": model_id,
        "status": status,
        "epoch": epoch,
        "phase": best.get("phase", ""),
        "primary_metric": PRIMARY_METRIC,
        "registered_at": registered_at,
        "evaluated_at": evaluated_at,
        "inference_latency_ms": 0,
        "dataset": {
            "version": (registry_row or {}).get("dataset_id") or "dataset-v1",
            "train_samples": 0,
            "val_samples": 0,
            "test_samples": int(matrices.get("global", {}).get("support", 0)),
        },
        "training": {
            "encoder": encoder,
            "epochs": int(config.get("epochs", 50)),
            "batch_size": int(config.get("batch_size", 16)),
            "learning_rate": float(config.get("lr_heads", 3e-5)),
            "trained_at": registered_at,
            "checkpoint": f"{artifact_prefix}/best_model.pt",
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
        "confusion_labels": ["NEG", "POS", "NEU"],
        "artifacts": {
            "prefix": artifact_prefix,
            "train_log": f"{base_uri}/train_log.csv",
            "run_config": f"{base_uri}/run_config.json",
            "confusion_matrices": f"{base_uri}/confusion_matrices.jsonl",
            "checkpoint": f"{base_uri}/best_model.pt",
        },
    }


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _s3_get_text(s3_client: Any, bucket: str, key: str) -> str | None:
    try:
        resp = s3_client.get_object(Bucket=bucket, Key=key)
        return resp["Body"].read().decode("utf-8")
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in {"NoSuchKey", "404", "NotFound"}:
            return None
        raise


def load_artifacts_from_prefix(
    s3_client: Any,
    bucket: str,
    prefix: str,
) -> tuple[str | None, str | None, str | None]:
    prefix = prefix.strip("/")
    train_log = _s3_get_text(s3_client, bucket, f"{prefix}/train_log.csv")
    run_config = _s3_get_text(s3_client, bucket, f"{prefix}/run_config.json")
    confusion = _s3_get_text(s3_client, bucket, f"{prefix}/confusion_matrices.jsonl")
    return train_log, run_config, confusion


def load_model_evaluation_from_s3(
    s3_client: Any,
    bucket: str,
    model_id: str,
    registry_row: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not bucket:
        return None

    row = dict(registry_row or {})
    row["_bucket"] = bucket

    for prefix in resolve_artifact_prefixes(model_id, registry_row):
        train_log, run_config, confusion = load_artifacts_from_prefix(s3_client, bucket, prefix)
        if not train_log:
            continue
        payload = build_evaluation_payload(
            model_id=model_id,
            train_log_text=train_log,
            run_config_text=run_config,
            confusion_text=confusion,
            artifact_prefix=prefix,
            registry_row=row,
        )
        if payload:
            return payload
    return None


def load_training_history_from_s3(
    s3_client: Any,
    bucket: str,
    model_id: str,
    registry_row: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if not bucket:
        return []

    for prefix in resolve_artifact_prefixes(model_id, registry_row):
        train_log, _, _ = load_artifacts_from_prefix(s3_client, bucket, prefix)
        if train_log:
            return build_training_history(train_log)
    return []


def metrics_summary_from_train_log(train_log_text: str) -> dict[str, float]:
    best = _best_train_row(_parse_train_log(train_log_text))
    if not best:
        return {}
    row_metrics = _scores_from_row(best)
    return {
        "tas_f1": row_metrics["tas_relaxed_f1"],
        "span_f1": row_metrics["span_f1"],
        "sentiment_f1": row_metrics["sent_matched_f1"],
        "global_f1": row_metrics["global_f1"],
    }
