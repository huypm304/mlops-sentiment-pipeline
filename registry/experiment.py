"""Experiment tracking — package training outputs and publish to S3 / local index."""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from registry.paths import (
    RUN_ARTIFACT_FILES,
    evaluation_report_key,
    training_run_key,
    training_run_uri,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCAL_EXPERIMENTS_DIR = REPO_ROOT / "experiments"
LOCAL_RUNS_INDEX = LOCAL_EXPERIMENTS_DIR / "index.json"

METRIC_KEYS = (
    "tas_strict_f1",
    "tas_relaxed_f1",
    "span_f1",
    "sent_matched_f1",
    "sent_goldspan_f1",
    "global_f1",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def default_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"run-{stamp}-{datetime.now(timezone.utc).strftime('%H%M%S')}"


def _float(row: dict[str, str], *keys: str) -> float:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            try:
                return float(value)
            except ValueError:
                continue
    return 0.0


def _read_train_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _best_epoch_row(rows: list[dict[str, str]]) -> dict[str, str] | None:
    for row in reversed(rows):
        if row.get("is_best") == "best":
            return row
    if not rows:
        return None
    return max(rows, key=lambda row: _float(row, "tas_relaxed_f1", "global_f1"))


def _metrics_from_row(row: dict[str, str] | None) -> dict[str, float]:
    if not row:
        return {}
    return {
        "tas_strict_f1": _float(row, "tas_strict_f1"),
        "tas_relaxed_f1": _float(row, "tas_relaxed_f1"),
        "span_f1": _float(row, "span_f1"),
        "sent_matched_f1": _float(row, "sent_matched_f1"),
        "sent_goldspan_f1": _float(row, "sent_goldspan_f1"),
        "global_f1": _float(row, "global_f1"),
    }


def _load_run_config(model_dir: Path) -> dict[str, Any]:
    for name in ("run_config.json", "config.json"):
        path = model_dir / name
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _training_config_summary(config: dict[str, Any]) -> dict[str, Any]:
    return {
        key: config[key]
        for key in (
            "epochs",
            "batch_size",
            "lr_backbone",
            "lr_heads",
            "model_name",
            "patience",
            "lambda_bio",
            "lambda_sent",
            "lambda_global",
        )
        if key in config
    }


def build_classification_report(
    *,
    run_id: str,
    model_dir: Path,
    dataset_id: str | None = None,
) -> dict[str, Any]:
    rows = _read_train_rows(model_dir / "train_log.csv")
    best = _best_epoch_row(rows)
    config = _load_run_config(model_dir)
    metrics = _metrics_from_row(best)
    report: dict[str, Any] = {
        "run_id": run_id,
        "dataset_id": dataset_id,
        "generated_at": now_iso(),
        "config": _training_config_summary(config),
        "best_epoch": int(best.get("epoch", 0)) if best else 0,
        "metrics": metrics,
    }
    if best:
        report["per_aspect_span_f1"] = {
            aspect: _float(best, f"span_f1_{aspect}") for aspect in (
                "Fashion", "Electronics", "General", "Service", "Ship", "Price", "App"
            )
        }
        report["per_aspect_sent_f1"] = {
            aspect: _float(best, f"sent_f1_{aspect}") for aspect in (
                "Fashion", "Electronics", "General", "Service", "Ship", "Price", "App"
            )
        }
    return report


def build_summary(
    *,
    run_id: str,
    model_dir: Path,
    dataset_id: str | None = None,
    status: str = "COMPLETED",
) -> dict[str, Any]:
    report = build_classification_report(run_id=run_id, model_dir=model_dir, dataset_id=dataset_id)
    return {
        "run_id": run_id,
        "status": status,
        "dataset_id": dataset_id,
        "generated_at": report["generated_at"],
        "best_epoch": report["best_epoch"],
        "config": report["config"],
        "metrics": report["metrics"],
        "artifacts": list(RUN_ARTIFACT_FILES),
    }


def _generate_figures(model_dir: Path, work_dir: Path) -> None:
    work_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = work_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    train_log = model_dir / "train_log.csv"
    confusion = model_dir / "best_confusion_matrices.json"
    if not confusion.is_file():
        confusion = model_dir / "confusion_matrices.jsonl"

    if train_log.is_file():
        subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "scripts/make_learning_curves.py"),
                "--train-log",
                str(train_log),
                "--output-dir",
                str(figures_dir),
            ],
            check=False,
        )

    if confusion.is_file():
        subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "scripts/make_confusion_plots.py"),
                "--confusion-file",
                str(confusion),
                "--output-dir",
                str(figures_dir),
            ],
            check=False,
        )


def _resolve_figure(work_dir: Path, canonical: str, candidates: tuple[str, ...]) -> Path | None:
    for name in candidates:
        path = work_dir / "figures" / name
        if path.is_file():
            return path
    return None


def package_run_artifacts(
    *,
    run_id: str,
    model_dir: Path,
    output_dir: Path,
    dataset_id: str | None = None,
    generate_plots: bool = True,
) -> dict[str, Path]:
    """Build the canonical training-runs/{run_id}/ file set locally."""
    output_dir.mkdir(parents=True, exist_ok=True)
    if generate_plots:
        _generate_figures(model_dir, output_dir)

    artifacts: dict[str, Path] = {}

    for src_name in ("run_config.json", "config.json"):
        src = model_dir / src_name
        if src.is_file():
            dst = output_dir / "run_config.json"
            shutil.copy2(src, dst)
            artifacts["run_config.json"] = dst
            break

    train_log = model_dir / "train_log.csv"
    if train_log.is_file():
        dst = output_dir / "train_log.csv"
        shutil.copy2(train_log, dst)
        artifacts["train_log.csv"] = dst

    summary_path = output_dir / "summary.json"
    summary_path.write_text(
        json.dumps(
            build_summary(run_id=run_id, model_dir=model_dir, dataset_id=dataset_id),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    artifacts["summary.json"] = summary_path

    report_path = output_dir / "classification_report.json"
    report_path.write_text(
        json.dumps(
            build_classification_report(run_id=run_id, model_dir=model_dir, dataset_id=dataset_id),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    artifacts["classification_report.json"] = report_path

    learning_src = _resolve_figure(
        output_dir,
        "learning_curve.png",
        ("learning_curve_metrics.png", "learning_curve_tas_relaxed.png", "learning_curve_global_f1.png"),
    )
    if learning_src:
        dst = output_dir / "learning_curve.png"
        shutil.copy2(learning_src, dst)
        artifacts["learning_curve.png"] = dst

    confusion_src = _resolve_figure(
        output_dir,
        "confusion_matrix.png",
        ("sentiment_confusion_matrix.png", "global_confusion_matrix.png"),
    )
    if confusion_src:
        dst = output_dir / "confusion_matrix.png"
        shutil.copy2(confusion_src, dst)
        artifacts["confusion_matrix.png"] = dst

    return artifacts


def _append_local_index(record: dict[str, Any]) -> None:
    LOCAL_EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
    index: list[dict[str, Any]] = []
    if LOCAL_RUNS_INDEX.is_file():
        index = json.loads(LOCAL_RUNS_INDEX.read_text(encoding="utf-8"))
    index = [row for row in index if row.get("run_id") != record.get("run_id")]
    index.insert(0, record)
    LOCAL_RUNS_INDEX.write_text(json.dumps(index[:100], ensure_ascii=False, indent=2), encoding="utf-8")


def load_local_runs(*, limit: int = 15) -> list[dict[str, Any]]:
    if not LOCAL_RUNS_INDEX.is_file():
        return []
    rows = json.loads(LOCAL_RUNS_INDEX.read_text(encoding="utf-8"))
    return rows[:limit]


def publish_training_run(
    *,
    run_id: str,
    model_dir: Path,
    dataset_id: str | None = None,
    store: Any | None = None,
    local_only: bool = False,
    generate_plots: bool = True,
    status: str = "COMPLETED",
    training_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Package artifacts, upload to S3, and register the run in DynamoDB / local index."""
    model_dir = model_dir.resolve()
    work_dir = LOCAL_EXPERIMENTS_DIR / "training-runs" / run_id
    artifacts = package_run_artifacts(
        run_id=run_id,
        model_dir=model_dir,
        output_dir=work_dir,
        dataset_id=dataset_id,
        generate_plots=generate_plots,
    )

    summary = json.loads((work_dir / "summary.json").read_text(encoding="utf-8"))
    metrics = summary.get("metrics") or {}
    config = training_config or _load_run_config(model_dir)
    created_at = now_iso()

    result: dict[str, Any] = {
        "run_id": run_id,
        "artifact_prefix": f"training-runs/{run_id}",
        "metrics": metrics,
        "summary": summary,
        "local_dir": str(work_dir),
        "artifacts": {name: str(path) for name, path in artifacts.items()},
    }

    if local_only or store is None or not getattr(store.config, "artifacts_bucket", ""):
        local_record = {
            "run_id": run_id,
            "created_at": created_at,
            "status": status,
            "dataset_id": dataset_id,
            "artifact_uri": str(work_dir),
            "artifact_prefix": f"experiments/training-runs/{run_id}",
            "training_config": _training_config_summary(config) or config,
            "metrics": metrics,
            "summary": summary,
        }
        _append_local_index(local_record)
        result["artifact_uri"] = str(work_dir)
        result["mode"] = "local"
        return result

    bucket = store.config.artifacts_bucket
    uploaded: dict[str, str] = {}
    content_types = {
        ".json": "application/json",
        ".csv": "text/csv",
        ".png": "image/png",
        ".pt": "application/octet-stream",
    }
    for name, path in artifacts.items():
        suffix = path.suffix.lower()
        key = training_run_key(run_id, name)
        store.put_file_s3(key, path, content_type=content_types.get(suffix, "application/octet-stream"))
        uploaded[name] = f"s3://{bucket}/{key}"

    # Optional checkpoint — keep under models/candidates/{run_id}/
    for weight_name in ("best_model.pt", "pointer.txt"):
        weight = model_dir / weight_name
        if weight.is_file():
            from registry.paths import model_candidate_prefix

            key = f"{model_candidate_prefix(run_id)}/{weight_name}"
            store.put_file_s3(key, weight, content_type="application/octet-stream")
            uploaded[weight_name] = f"s3://{bucket}/{key}"

    artifact_uri = training_run_uri(bucket, run_id)
    eval_report = {
        "run_id": run_id,
        "metrics": metrics,
        "evaluated_at": created_at,
        "mode": "training_run",
        "summary_s3_uri": uploaded.get("summary.json"),
        "classification_report_s3_uri": uploaded.get("classification_report.json"),
    }
    store.put_json_s3(evaluation_report_key(run_id), eval_report)

    if store.config.training_runs_table:
        existing = store.get_training_run(run_id)
        updates = {
            "status": status,
            "dataset_id": dataset_id or (existing or {}).get("dataset_id", ""),
            "artifact_prefix": f"training-runs/{run_id}",
            "artifact_uri": artifact_uri,
            "training_config": _training_config_summary(config) or config,
            "metrics": metrics,
            "best_f1": metrics.get("tas_relaxed_f1") or metrics.get("global_f1"),
            "finished_at": created_at,
        }
        if existing:
            store.update_training_run(run_id, existing["created_at"], updates)
        else:
            store.put_training_run(
                {
                    "run_id": run_id,
                    "created_at": created_at,
                    **updates,
                }
            )

    result.update(
        {
            "artifact_uri": artifact_uri,
            "uploaded": uploaded,
            "mode": "s3",
        }
    )
    return result
