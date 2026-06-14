#!/usr/bin/env python3
"""Publish DVC-tracked benchmark splits to S3 approved + manifest + DynamoDB.

Local workflow (after ``dvc pull``):

    python scripts/publish_approved_dataset.py \\
        --dataset-id dataset-v1 \\
        --name "ABSA Benchmark v1"

Upload targets (same artifacts bucket as Terraform core):
  - s3://<bucket>/datasets/approved/<dataset_id>/{train,dev,test}.jsonl
  - s3://<bucket>/datasets/pending/<dataset_id>/   (mirror for audit Lambda)
  - s3://<bucket>/datasets/manifests/<dataset_id>.json

Cloud training reads ``datasets/approved/`` + manifest — not the DVC store.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DEFAULT_PROCESSED_DIR = ROOT / "datasets" / "processed"
SPLITS = ("train", "dev", "test")
REQUIRED_SPLITS = ("train", "dev")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _count_jsonl_rows(path: Path) -> int:
    count = 0
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def _git_commit() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def _parse_dvc_out(path: Path) -> dict[str, Any]:
    """Extract md5/size from a .dvc sidecar (supports md5 and hash fields)."""
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    info: dict[str, Any] = {}
    for key in ("md5", "hash", "size", "nfiles"):
        match = re.search(rf"^\s*{key}:\s*(\S+)\s*$", text, re.MULTILINE)
        if match:
            value: Any = match.group(1).strip("'\"")
            if key in {"size", "nfiles"}:
                try:
                    value = int(value)
                except ValueError:
                    pass
            info[key] = value
    return info


def _load_dvc_remote_url() -> str:
    config_path = ROOT / ".dvc" / "config"
    if not config_path.is_file():
        return ""
    text = config_path.read_text(encoding="utf-8")
    match = re.search(r'url\s*=\s*(s3://[^\s]+)', text)
    return match.group(1) if match else ""


def _resolve_split_paths(processed_dir: Path, splits: tuple[str, ...]) -> dict[str, Path]:
    resolved: dict[str, Path] = {}
    missing: list[str] = []
    for split in splits:
        path = processed_dir / f"{split}.jsonl"
        if path.is_file():
            resolved[split] = path
        elif split in REQUIRED_SPLITS:
            missing.append(str(path))
    if missing:
        raise FileNotFoundError(
            "Required split files not found. Run `dvc pull` first.\n  "
            + "\n  ".join(missing)
        )
    return resolved


def build_manifest(
    *,
    dataset_id: str,
    name: str,
    split_paths: dict[str, Path],
    processed_dir: Path,
    git_commit: str,
    dvc_remote_url: str,
    mirror_pending: bool,
) -> dict[str, Any]:
    now = _now_iso()
    splits: dict[str, dict[str, Any]] = {}
    dvc_files: dict[str, Any] = {}

    for split, path in split_paths.items():
        checksum = _md5(path)
        dvc_sidecar = processed_dir / f"{path.name}.dvc"
        dvc_meta = _parse_dvc_out(dvc_sidecar)
        splits[split] = {
            "filename": path.name,
            "rows": _count_jsonl_rows(path),
            "size_bytes": path.stat().st_size,
            "checksum_md5": checksum,
            "s3_key_approved": f"datasets/approved/{dataset_id}/{path.name}",
            "s3_key_pending": f"datasets/pending/{dataset_id}/{path.name}",
        }
        dvc_files[split] = {
            "dvc_file": (
                str(dvc_sidecar.relative_to(ROOT))
                if dvc_sidecar.is_file() and ROOT in dvc_sidecar.parents
                else (str(dvc_sidecar) if dvc_sidecar.is_file() else "")
            ),
            "md5": dvc_meta.get("md5") or dvc_meta.get("hash") or checksum,
            "size": dvc_meta.get("size", path.stat().st_size),
            "rows": splits[split]["rows"],
        }

    approved_prefix = f"datasets/approved/{dataset_id}/"
    pending_prefix = f"datasets/pending/{dataset_id}/"

    return {
        "dataset_id": dataset_id,
        "name": name.strip() or dataset_id,
        "source": "dvc",
        "status": "approved",
        "created_at": now,
        "updated_at": now,
        "uploaded_by": "dvc-publish",
        "s3_approved_prefix": approved_prefix,
        "s3_pending_prefix": pending_prefix if mirror_pending else "",
        "splits": splits,
        "dvc": {
            "remote_url": dvc_remote_url,
            "git_commit": git_commit,
            "processed_dir": (
                str(processed_dir.relative_to(ROOT))
                if ROOT in processed_dir.parents
                else str(processed_dir)
            ),
            "files": dvc_files,
        },
        "audits": {},
        "audit_passed": False,
    }


def publish_to_s3(
    *,
    bucket: str,
    dataset_id: str,
    split_paths: dict[str, Path],
    manifest: dict[str, Any],
    region: str,
    mirror_pending: bool,
    dry_run: bool,
) -> dict[str, str]:
    import boto3

    client = boto3.client("s3", region_name=region)
    uploaded: dict[str, str] = {}

    targets: list[tuple[str, Path]] = []
    for split, path in split_paths.items():
        targets.append((f"datasets/approved/{dataset_id}/{path.name}", path))
        if mirror_pending:
            targets.append((f"datasets/pending/{dataset_id}/{path.name}", path))

    for key, path in targets:
        uploaded[key] = f"s3://{bucket}/{key}"
        if dry_run:
            print(f"[dry-run] upload {path} -> s3://{bucket}/{key}")
            continue
        client.upload_file(str(path), bucket, key, ExtraArgs={"ContentType": "application/x-ndjson"})

    manifest_key = f"datasets/manifests/{dataset_id}.json"
    manifest_body = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
    uploaded[manifest_key] = f"s3://{bucket}/{manifest_key}"
    if dry_run:
        print(f"[dry-run] put manifest -> s3://{bucket}/{manifest_key}")
    else:
        client.put_object(
            Bucket=bucket,
            Key=manifest_key,
            Body=manifest_body,
            ContentType="application/json",
        )

    return uploaded


def sync_dynamodb(manifest: dict[str, Any], *, dry_run: bool) -> None:
    from registry.store import RegistryStore

    store = RegistryStore()
    if not store.config.datasets_table:
        print("DynamoDB datasets table not configured — skipping registry sync.")
        return

    record = store.dataset_record_from_manifest(manifest)
    record["status"] = "APPROVED"
    record["s3_prefix"] = manifest["s3_approved_prefix"].rstrip("/")
    record["s3_uri"] = (
        f"s3://{store.config.artifacts_bucket}/{record['s3_prefix']}/"
        if store.config.artifacts_bucket
        else record.get("s3_uri", "")
    )
    record["source"] = "dvc"
    record["dvc_git_commit"] = (manifest.get("dvc") or {}).get("git_commit", "")
    record["manifest_s3_key"] = f"datasets/manifests/{manifest['dataset_id']}.json"

    if dry_run:
        print(f"[dry-run] DynamoDB put_dataset: {record['dataset_id']} status=APPROVED")
        return

    existing = store.get_dataset(manifest["dataset_id"])
    if existing:
        store.update_dataset(
            manifest["dataset_id"],
            str(existing["created_at"]),
            {k: v for k, v in record.items() if k not in {"dataset_id", "created_at"}},
        )
    else:
        store.put_dataset(record)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-id", default="dataset-v1", help="Stable dataset id (e.g. dataset-v1)")
    parser.add_argument("--name", default="ABSA Benchmark v1", help="Human-readable dataset name")
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=DEFAULT_PROCESSED_DIR,
        help="Directory containing DVC-tracked JSONL splits",
    )
    parser.add_argument(
        "--bucket",
        default="",
        help="S3 artifacts bucket (default: ARTIFACTS_BUCKET env or absa-mlops-demo-artifacts)",
    )
    parser.add_argument("--region", default="", help="AWS region (default: AWS_REGION or ap-southeast-1)")
    parser.add_argument(
        "--mirror-pending",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Also upload to datasets/pending/ for audit Lambda compatibility",
    )
    parser.add_argument("--skip-dynamodb", action="store_true", help="Do not write DynamoDB registry record")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without uploading")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    import os

    bucket = args.bucket or os.getenv("ARTIFACTS_BUCKET", "absa-mlops-demo-artifacts")
    region = args.region or os.getenv("AWS_REGION", "ap-southeast-1")
    processed_dir = args.processed_dir.resolve()

    split_paths = _resolve_split_paths(processed_dir, SPLITS)
    git_commit = _git_commit()
    dvc_remote = _load_dvc_remote_url()

    manifest = build_manifest(
        dataset_id=args.dataset_id,
        name=args.name,
        split_paths=split_paths,
        processed_dir=processed_dir,
        git_commit=git_commit,
        dvc_remote_url=dvc_remote,
        mirror_pending=args.mirror_pending,
    )

    print(f"Publishing dataset '{args.dataset_id}' to s3://{bucket}/")
    uploaded = publish_to_s3(
        bucket=bucket,
        dataset_id=args.dataset_id,
        split_paths=split_paths,
        manifest=manifest,
        region=region,
        mirror_pending=args.mirror_pending,
        dry_run=args.dry_run,
    )

    if not args.skip_dynamodb:
        sync_dynamodb(manifest, dry_run=args.dry_run)

    print("\nUpload summary:")
    for key, uri in sorted(uploaded.items()):
        print(f"  {uri}")

    print("\nNext steps:")
    if args.mirror_pending:
        print(f"  1. Run audit once: POST /datasets/{args.dataset_id}/audit")
        print(f"  2. Approve: POST /datasets/{args.dataset_id}/approve")
    print(f"  3. Trigger training with dataset_id={args.dataset_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
