#!/usr/bin/env python3
"""Validate and package artifacts/ for submission or S3 upload.

Checks that required files exist, generates a manifest, and optionally
creates a zip archive suitable for SageMaker model.tar.gz.

Usage:
    python scripts/package_artifacts.py \\
        --artifacts-dir artifacts \\
        --output-zip   artifacts/absa_model_package.zip
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

REQUIRED_FILES = [
    "model/model_card.json",
    "model/label_mapping.json",
    "model/run_config.json",
    "evaluation/eval_report.json",
    "evaluation/summary_metrics.json",
    "data/dataset_manifest.json",
    "figures/learning_curve_metrics.png",
    "figures/sentiment_confusion_matrix.png",
    "demo/demo_success_30.jsonl",
]

OPTIONAL_FILES = [
    "model/best_model.pt",
    "model/pointer.txt",
    "model/checksum.txt",
    "model/requirements.txt",
    "model/postprocess_config.json",
    "evaluation/confusion_matrix.json",
    "evaluation/per_aspect_report.csv",
    "evaluation/per_class_report.csv",
    "figures/learning_curve_loss.png",
    "figures/global_confusion_matrix.png",
    "figures/per_aspect_span_f1.png",
    "figures/per_aspect_sent_f1.png",
]


def _md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _validate(artifacts_dir: Path) -> tuple[list[str], list[str]]:
    missing = []
    present = []
    for rel in REQUIRED_FILES:
        p = artifacts_dir / rel
        if p.is_file():
            present.append(rel)
        else:
            missing.append(rel)
    return present, missing


def _collect_files(artifacts_dir: Path) -> list[Path]:
    files = []
    for rel in REQUIRED_FILES + OPTIONAL_FILES:
        p = artifacts_dir / rel
        if p.is_file():
            files.append(p)
    # Also collect any extra files in model/ that aren't listed
    for p in sorted((artifacts_dir / "model").iterdir()):
        if p.is_file() and p not in files:
            files.append(p)
    return files


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate and package artifacts/")
    p.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"))
    p.add_argument("--output-zip",    type=Path, default=None,
                   help="If provided, create a zip archive of required+optional files")
    p.add_argument("--strict",        action="store_true",
                   help="Exit with error if any required file is missing")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    if not args.artifacts_dir.is_dir():
        print(f"ERROR: artifacts directory not found: {args.artifacts_dir}")
        sys.exit(1)

    present, missing = _validate(args.artifacts_dir)

    print(f"Required files: {len(REQUIRED_FILES)} total")
    print(f"  Present : {len(present)}")
    print(f"  Missing : {len(missing)}")
    if missing:
        print("\nMissing required files:")
        for f in missing:
            print(f"  [MISSING] {f}")
        if args.strict:
            print("\nERROR: --strict mode: failing on missing required files")
            sys.exit(1)
    else:
        print("\nAll required files present.")

    # Build manifest
    manifest_entries = []
    files = _collect_files(args.artifacts_dir)
    for fpath in files:
        rel = str(fpath.relative_to(args.artifacts_dir))
        entry = {
            "path": rel,
            "md5": _md5(fpath),
            "size_bytes": fpath.stat().st_size,
            "required": rel in REQUIRED_FILES,
        }
        manifest_entries.append(entry)

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "artifacts_dir": str(args.artifacts_dir.resolve()),
        "required_files_present": len(present),
        "required_files_missing": len(missing),
        "missing": missing,
        "files": manifest_entries,
    }

    manifest_path = args.artifacts_dir / "artifacts_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"\nManifest written: {manifest_path}")

    # Optional zip
    if args.output_zip:
        args.output_zip.parent.mkdir(parents=True, exist_ok=True)
        print(f"\nCreating zip: {args.output_zip}")
        with zipfile.ZipFile(args.output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for fpath in files:
                arcname = str(fpath.relative_to(args.artifacts_dir))
                zf.write(fpath, arcname)
                print(f"  + {arcname}")
        size_mb = args.output_zip.stat().st_size / (1024 * 1024)
        print(f"\nZip created: {args.output_zip} ({size_mb:.1f} MB)")

    print(f"\nDone. Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
