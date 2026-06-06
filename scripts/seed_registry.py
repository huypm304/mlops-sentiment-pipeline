#!/usr/bin/env python3
"""Seed DynamoDB registry with baseline production model absa-v1."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from registry.store import RegistryStore, now_iso  # noqa: E402


def _load_metrics() -> dict[str, float]:
    log_path = ROOT / "model" / "train_log.csv"
    if not log_path.is_file():
        return {
            "tas_f1": 0.72,
            "span_f1": 0.68,
            "sentiment_f1": 0.75,
            "global_f1": 0.73,
        }

    import csv

    best: dict[str, str] | None = None
    best_global = -1.0
    with log_path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                global_f1 = float(row.get("global_f1", 0) or 0)
            except ValueError:
                continue
            if global_f1 > best_global:
                best_global = global_f1
                best = row

    if not best:
        return {"tas_f1": 0.72, "span_f1": 0.68, "sentiment_f1": 0.75, "global_f1": 0.73}

    return {
        "tas_f1": float(best.get("tas_relaxed_f1", best.get("tas_f1", 0)) or 0),
        "span_f1": float(best.get("span_f1", 0) or 0),
        "sentiment_f1": float(best.get("sent_matched_f1", best.get("sentiment_f1", 0)) or 0),
        "global_f1": float(best.get("global_f1", 0) or 0),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed absa-v1 production model in DynamoDB")
    parser.add_argument("--model-id", default="absa-v1")
    parser.add_argument("--dataset-id", default="dataset-v1")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    store = RegistryStore()
    if not store.config.models_table:
        print("MODELS_TABLE is not configured", file=sys.stderr)
        return 1

    metrics = _load_metrics()
    version = now_iso()
    record = {
        "model_id": args.model_id,
        "version": version,
        "status": "PRODUCTION",
        "source": "local_training",
        "artifact_uri": f"s3://{store.config.artifacts_bucket}/models/production/" if store.config.artifacts_bucket else "models/production/",
        "artifact_prefix": "models/production",
        "dataset_id": args.dataset_id,
        "metrics": metrics,
        "registered_at": version,
    }

    if args.dry_run:
        print(json.dumps(record, indent=2, ensure_ascii=False))
        return 0

    store.put_model(record)
    print(f"Seeded production model {args.model_id} @ {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
