#!/usr/bin/env python3
"""Seed DynamoDB model registry from S3 training artifacts.

Metrics are loaded from train_log.csv under the model's artifact_prefix on S3.
Deploy flow: upload artifacts with scripts/upload_model.sh, then seed registry.

    export ARTIFACTS_BUCKET=absa-mlops-demo-artifacts
    python scripts/seed_registry.py --model-id absa-v2b
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "apps" / "backend"))

from registry.model_artifacts import (  # noqa: E402
    load_model_evaluation_from_s3,
    metrics_summary_from_train_log,
    resolve_artifact_prefixes,
)
from registry.store import RegistryStore, now_iso  # noqa: E402


def _load_local_artifacts(model_dir: Path) -> tuple[str | None, dict]:
    train_log_path = model_dir / "train_log.csv"
    config_path = model_dir / "run_config.json"
    if not config_path.is_file():
        config_path = model_dir / "config.json"

    train_log_text = train_log_path.read_text(encoding="utf-8") if train_log_path.is_file() else None
    config: dict = {}
    if config_path.is_file():
        config = json.loads(config_path.read_text(encoding="utf-8"))
    return train_log_text, config


def _demote_other_production(store: RegistryStore, keep_model_id: str) -> None:
    for row in store.list_models(limit=50, status="PRODUCTION"):
        if row.get("model_id") == keep_model_id:
            continue
        store._table(store.config.models_table).update_item(
            Key={"model_id": row["model_id"], "version": row["version"]},
            UpdateExpression="SET #status = :archived",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":archived": "ARCHIVED"},
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed production model metadata in DynamoDB from S3")
    parser.add_argument("--model-id", default="absa-v2b")
    parser.add_argument("--dataset-id", default="dataset-v1")
    parser.add_argument(
        "--artifact-prefix",
        default="",
        help="S3 prefix for train_log.csv (default: models/v1 for absa-v2b)",
    )
    parser.add_argument(
        "--model-dir",
        default="",
        help="Optional local staging dir (dev only — production uses S3)",
    )
    parser.add_argument(
        "--from-local",
        action="store_true",
        help="Load metrics from --model-dir instead of S3 (not for deploy)",
    )
    parser.add_argument("--no-demote-others", action="store_true", help="Keep other PRODUCTION rows unchanged")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    store = RegistryStore()
    if not store.config.models_table:
        print("MODELS_TABLE is not configured", file=sys.stderr)
        return 1

    artifact_prefix = args.artifact_prefix.strip("/") or resolve_artifact_prefixes(args.model_id)[0]
    encoder = "unknown"
    metrics: dict[str, float] = {}

    use_s3 = not args.from_local
    if use_s3:
        if not store.config.artifacts_bucket:
            print("ARTIFACTS_BUCKET is not configured — cannot load metrics from S3", file=sys.stderr)
            return 1
        payload = load_model_evaluation_from_s3(
            store._s3,
            store.config.artifacts_bucket,
            args.model_id,
            {"artifact_prefix": artifact_prefix},
        )
        if payload:
            encoder = payload["training"]["encoder"]
            scores = payload["scores"]
            metrics = {
                "tas_f1": scores["tas_relaxed_f1"],
                "span_f1": scores["span_f1"],
                "sentiment_f1": scores["sent_matched_f1"],
                "global_f1": scores["global_f1"],
            }
    else:
        model_dir = Path(args.model_dir or ROOT / "model")
        train_log_text, config = _load_local_artifacts(model_dir)
        if train_log_text:
            metrics = metrics_summary_from_train_log(train_log_text)
        encoder = config.get("model_name", encoder)

    if not metrics:
        print(
            f"Could not load metrics from s3://{store.config.artifacts_bucket}/{artifact_prefix}/",
            file=sys.stderr,
        )
        print("Upload artifacts first: ./scripts/upload_model.sh <staging-dir>", file=sys.stderr)
        return 1

    version = now_iso()
    bucket = store.config.artifacts_bucket
    record = {
        "model_id": args.model_id,
        "version": version,
        "status": "PRODUCTION",
        "source": "s3_artifacts",
        "encoder": encoder,
        "artifact_uri": f"s3://{bucket}/{artifact_prefix}/" if bucket else artifact_prefix,
        "artifact_prefix": artifact_prefix,
        "dataset_id": args.dataset_id,
        "metrics": metrics,
        "registered_at": version,
    }

    if args.dry_run:
        print(json.dumps(record, indent=2, ensure_ascii=False))
        return 0

    if not args.no_demote_others:
        _demote_other_production(store, args.model_id)

    store.put_model(record)
    print(f"Seeded production model {args.model_id} @ {version}")
    print(f"  encoder: {encoder}")
    print(f"  artifacts: s3://{bucket}/{artifact_prefix}/")
    print(f"  global_f1: {metrics.get('global_f1', 0):.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
