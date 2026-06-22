"""Local dataset registry: upload train/dev/test splits and track audit status."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.config.settings import REPO_ROOT
from backend.app.services import registry_db

DATASETS_DIR = REPO_ROOT / "datasets" / "local"
SPLITS = ("train", "dev", "test")
REQUIRED_SPLITS = ("train", "dev")
BUNDLE_SPLIT = "bundle"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug[:48] or "dataset"


def _dataset_dir(dataset_id: str) -> Path:
    return DATASETS_DIR / dataset_id


def _manifest_path(dataset_id: str) -> Path:
    return _dataset_dir(dataset_id) / "manifest.json"


def _count_jsonl_rows(path: Path) -> int:
    count = 0
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def audit_score_from_report(report: dict[str, Any]) -> float:
    return _audit_score_from_report(report)


def _audit_score_from_report(report: dict[str, Any]) -> float:
    benchmarks = report.get("benchmarks") or []
    if not benchmarks:
        return 0.0
    passed = sum(1 for row in benchmarks if row.get("status") == "pass")
    return round(passed / len(benchmarks), 4)


def _load_manifest_raw(dataset_id: str) -> dict[str, Any]:
    path = _manifest_path(dataset_id)
    if not path.is_file():
        raise FileNotFoundError(f"Dataset '{dataset_id}' not found")
    return json.loads(path.read_text(encoding="utf-8"))


def _sync_dataset_registry(manifest: dict[str, Any]) -> None:
    store = registry_db.get_store()
    if store is None or not store.config.datasets_table:
        return
    record = store.dataset_record_from_manifest(manifest)
    audits = manifest.get("audits") or {}
    if audits:
        scores = [float(a.get("audit_score", 0)) for a in audits.values()]
        if scores:
            record["audit_score"] = round(sum(scores) / len(scores), 4)
        bundle = audits.get("bundle") or {}
        if bundle.get("report_id"):
            record["audit_report_uri"] = (
                f"s3://{store.config.artifacts_bucket}/reports/audit/{bundle['report_id']}.json"
                if store.config.artifacts_bucket
                else f"reports/audit/{bundle['report_id']}.json"
            )
    existing = store.get_dataset(manifest["dataset_id"])
    if existing:
        store.update_dataset(
            manifest["dataset_id"],
            str(existing["created_at"]),
            {k: v for k, v in record.items() if k not in {"dataset_id", "created_at"}},
        )
    else:
        store.put_dataset(record)


def save_manifest(manifest: dict[str, Any]) -> None:
    dataset_id = manifest["dataset_id"]
    path = _manifest_path(dataset_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    _sync_dataset_registry(manifest)


def resolve_split_path(dataset_id: str, split: str) -> Path:
    manifest = _load_manifest_raw(dataset_id)
    split_info = manifest.get("splits", {}).get(split)
    if not split_info:
        raise FileNotFoundError(f"Split '{split}' not uploaded for dataset '{dataset_id}'")
    path = _dataset_dir(dataset_id) / split_info["filename"]
    if not path.is_file():
        raise FileNotFoundError(f"Split file missing: {path}")
    return path


def create_dataset(
    *,
    name: str,
    files: dict[str, tuple[str, bytes]],
) -> dict[str, Any]:
    if not files:
        raise ValueError("At least one split file is required")
    missing = [split for split in REQUIRED_SPLITS if split not in files]
    if missing:
        raise ValueError(f"Required splits missing: {', '.join(missing)}")

    dataset_id = f"{_slugify(name)}-{uuid.uuid4().hex[:8]}"
    dataset_path = _dataset_dir(dataset_id)
    dataset_path.mkdir(parents=True, exist_ok=True)

    now = _now_iso()
    splits: dict[str, dict[str, Any]] = {}
    for split, (original_name, content) in files.items():
        if split not in SPLITS:
            raise ValueError(f"Invalid split '{split}'")
        suffix = Path(original_name).suffix or ".jsonl"
        filename = f"{split}{suffix}"
        target = dataset_path / filename
        target.write_bytes(content)
        splits[split] = {
            "filename": filename,
            "rows": _count_jsonl_rows(target),
            "size_bytes": target.stat().st_size,
        }

    manifest = {
        "dataset_id": dataset_id,
        "name": name.strip() or dataset_id,
        "status": "pending",
        "created_at": now,
        "updated_at": now,
        "splits": splits,
        "audits": {},
        "audit_passed": False,
    }
    save_manifest(manifest)
    return manifest


def get_dataset(dataset_id: str) -> dict[str, Any]:
    return _load_manifest_raw(dataset_id)


def _audit_status(manifest: dict[str, Any]) -> str:
    if manifest.get("audit_passed"):
        return "pass"
    audits = manifest.get("audits") or {}
    if audits:
        return "running"
    return "pending"


def list_datasets() -> list[dict[str, Any]]:
    store = registry_db.get_store()
    if store is not None and store.config.datasets_table:
        return [registry_db.map_dataset_list_item(row) for row in store.list_datasets()]

    if not DATASETS_DIR.exists():
        return []

    items: list[dict[str, Any]] = []
    for manifest_path in sorted(DATASETS_DIR.glob("*/manifest.json"), reverse=True):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        splits = manifest.get("splits") or {}
        audits = manifest.get("audits") or {}
        scores = [float(a.get("audit_score", 0)) for a in audits.values()]
        items.append(
            {
                "dataset_id": manifest.get("dataset_id", manifest_path.parent.name),
                "name": manifest.get("name", manifest_path.parent.name),
                "status": manifest.get("status", "pending"),
                "created_at": manifest.get("created_at", ""),
                "splits": list(splits.keys()),
                "audit_passed": bool(manifest.get("audit_passed")),
                "audit_status": _audit_status(manifest),
                "audit_score": round(sum(scores) / len(scores), 4) if scores else None,
                "total_rows": sum(int(s.get("rows", 0)) for s in splits.values()),
            }
        )
    return items


def record_audit_result(dataset_id: str, split: str, report: dict[str, Any]) -> dict[str, Any]:
    manifest = _load_manifest_raw(dataset_id)
    splits = manifest.get("splits", {})

    if split == BUNDLE_SPLIT:
        missing = [name for name in REQUIRED_SPLITS if name not in splits]
        if missing:
            raise FileNotFoundError(
                f"Required splits missing for bundle audit in '{dataset_id}': {', '.join(missing)}"
            )
    elif split not in splits:
        raise FileNotFoundError(f"Split '{split}' not found in dataset '{dataset_id}'")

    audits = manifest.setdefault("audits", {})
    audits[split] = {
        "report_id": report["report_id"],
        "passed": bool(report.get("passed")),
        "audit_score": _audit_score_from_report(report),
        "error_count": int((report.get("summary") or {}).get("error_count", 0)),
        "generated_at": report.get("generated_at", _now_iso()),
    }

    manifest["audit_passed"] = bool(audits.get("bundle", {}).get("passed"))
    manifest["status"] = "audited" if audits else "pending"
    if manifest["audit_passed"]:
        manifest["status"] = "audited"
    manifest["updated_at"] = _now_iso()
    save_manifest(manifest)
    return manifest
