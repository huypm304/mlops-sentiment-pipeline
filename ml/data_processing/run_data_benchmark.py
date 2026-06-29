#!/usr/bin/env python3
"""
Run all ABSA data benchmark audits and produce benchmark_summary.json.

Portable — copy entire data_benchmark/ folder to main repo.

Example:
    python data_benchmark/run_data_benchmark.py \\
        --train data_stratified/train_aug500_boundary200.jsonl \\
        --dev   data_stratified/dev_clean.jsonl \\
        --test  data_stratified/test_clean.jsonl \\
        --output-dir data_benchmark/reports
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUDITS_DIR = ROOT / "audits"
DEFAULT_THRESHOLDS = ROOT / "config" / "thresholds.json"

AUDIT_MODULES = [
    ("schema_audit", "schema_audit.py"),
    ("span_offset_audit", "span_offset_audit.py"),
    ("label_consistency_audit", "label_consistency_audit.py"),
    ("distribution_audit", "distribution_audit.py"),
    ("global_sentiment_audit", "global_sentiment_audit.py"),
    ("leakage_audit", "leakage_audit.py"),
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run ABSA data benchmark suite")
    p.add_argument("--train", required=True, type=Path, help="Train JSONL path")
    p.add_argument("--dev", required=True, type=Path, help="Dev JSONL path")
    p.add_argument("--test", default=None, type=Path, help="Optional test JSONL")
    p.add_argument(
        "--output-dir",
        default=ROOT / "reports",
        type=Path,
        help="Directory for per-module JSON reports + benchmark_summary.json",
    )
    p.add_argument(
        "--thresholds",
        default=DEFAULT_THRESHOLDS,
        type=Path,
        help="Threshold config JSON (for summary only)",
    )
    p.add_argument(
        "--skip-integrity",
        action="store_true",
        help="Skip optional data_integrity style analysis (needs numpy)",
    )
    p.add_argument(
        "--near-threshold",
        type=float,
        default=0.9,
        help="Jaccard threshold for leakage near-duplicate detection",
    )
    return p.parse_args()


def run_audit(
    script: Path,
    *,
    train: Path,
    dev: Path,
    output: Path,
    extra_args: list[str] | None = None,
) -> None:
    cmd = [
        sys.executable,
        str(script),
        "--train", str(train),
        "--dev", str(dev),
        "--output", str(output),
    ]
    if extra_args:
        cmd.extend(extra_args)
    print(f"  → {script.name} ...", flush=True)
    subprocess.run(cmd, check=True)


def main() -> None:
    args = parse_args()

    for path, label in [(args.train, "train"), (args.dev, "dev")]:
        if not path.exists():
            sys.exit(f"ERROR: {label} file not found: {path}")
    if args.test and not args.test.exists():
        sys.exit(f"ERROR: test file not found: {args.test}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    print("=" * 60)
    print("ABSA Data Benchmark")
    print(f"  train : {args.train}")
    print(f"  dev   : {args.dev}")
    if args.test:
        print(f"  test  : {args.test}")
    print(f"  out   : {args.output_dir}")
    print("=" * 60)

    print("\n[1/2] Running audit modules ...")
    for name, filename in AUDIT_MODULES:
        out_path = args.output_dir / f"{name}.json"
        extra = None
        if name == "leakage_audit":
            extra = ["--near-threshold", str(args.near_threshold)]
        run_audit(
            AUDITS_DIR / filename,
            train=args.train,
            dev=args.dev,
            output=out_path,
            extra_args=extra,
        )

    if not args.skip_integrity:
        integrity_out = args.output_dir / "data_integrity_style_analysis.json"
        print("\n[optional] data_integrity style analysis ...", flush=True)
        cmd = [
            sys.executable,
            str(AUDITS_DIR / "data_integrity.py"),
            "--train", str(args.train),
            "--dev", str(args.dev),
            "--output", str(integrity_out),
        ]
        if args.test:
            cmd.extend(["--test", str(args.test)])
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as exc:
            print(f"  WARN: data_integrity failed (exit {exc.returncode}), continuing")

    print("\n[2/2] Building benchmark_summary.json ...")
    sys.path.insert(0, str(ROOT))
    from summarize import build_benchmark_summary  # noqa: E402

    summary = build_benchmark_summary(
        args.output_dir,
        args.train,
        thresholds_path=args.thresholds if args.thresholds.exists() else None,
    )
    summary_path = args.output_dir / "benchmark_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - t0
    status = summary.get("overall", {}).get("data_level_status", "unknown")
    print("\n" + "=" * 60)
    print(f"Done in {elapsed:.1f}s")
    print(f"  Summary : {summary_path}")
    print(f"  Status  : {status}")
    print("  Modules :")
    for mod, st in summary.get("overall", {}).get("module_statuses", {}).items():
        print(f"    {mod}: {st}")
    print("=" * 60)

    if status == "fail":
        sys.exit(1)


if __name__ == "__main__":
    main()
