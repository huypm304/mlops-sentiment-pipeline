#!/usr/bin/env python3
"""Publish a completed training run to experiment tracking (S3 + DynamoDB).

After local training, run:

    python scripts/publish_training_run.py \\
        --model-dir model \\
        --dataset-id dataset-v1

With AWS configured (ARTIFACTS_BUCKET, TRAINING_RUNS_TABLE):

    export ARTIFACTS_BUCKET=absa-mlops-demo-artifacts
    export TRAINING_RUNS_TABLE=absa-mlops-demo-training-runs
    python scripts/publish_training_run.py --model-dir model --dataset-id dataset-v1

Local-only (no AWS — writes experiments/index.json for the UI):

    python scripts/publish_training_run.py --model-dir model --local-only
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from registry.experiment import default_run_id, publish_training_run  # noqa: E402
from registry.store import RegistryStore  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish training run artifacts to experiment tracking")
    parser.add_argument("--run-id", default=None, help="Run ID (default: run-YYYYMMDD-HHMMSS)")
    parser.add_argument("--model-dir", type=Path, default=Path("model"), help="Local training output dir")
    parser.add_argument("--dataset-id", default=None, help="Dataset used for this run")
    parser.add_argument("--local-only", action="store_true", help="Skip S3/DynamoDB; write local index only")
    parser.add_argument("--no-plots", action="store_true", help="Skip generating PNG curves/matrices")
    parser.add_argument("--dry-run", action="store_true", help="Package locally and print summary only")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_id = args.run_id or default_run_id()
    model_dir = args.model_dir.resolve()

    if not model_dir.is_dir():
        print(f"Model directory not found: {model_dir}", file=sys.stderr)
        return 1
    if not (model_dir / "train_log.csv").is_file():
        print(f"Missing train_log.csv in {model_dir}", file=sys.stderr)
        return 1

    store = None if args.local_only else RegistryStore()
    if args.dry_run:
        from registry.experiment import package_run_artifacts

        work_dir = ROOT / "experiments" / "training-runs" / run_id
        artifacts = package_run_artifacts(
            run_id=run_id,
            model_dir=model_dir,
            output_dir=work_dir,
            dataset_id=args.dataset_id,
            generate_plots=not args.no_plots,
        )
        summary = json.loads((work_dir / "summary.json").read_text(encoding="utf-8"))
        print(json.dumps({"run_id": run_id, "summary": summary, "artifacts": list(artifacts)}, indent=2))
        return 0

    result = publish_training_run(
        run_id=run_id,
        model_dir=model_dir,
        dataset_id=args.dataset_id,
        store=store,
        local_only=args.local_only,
        generate_plots=not args.no_plots,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\n✓ Published run {run_id} ({result.get('mode', 'unknown')})")
    if result.get("artifact_uri"):
        print(f"  Artifacts: {result['artifact_uri']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
