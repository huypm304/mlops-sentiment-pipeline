"""Audit Lambda — dataset registry, presign upload, and data_benchmark audit."""

from __future__ import annotations

import json
import os
import re
import tempfile
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError

from dataset_audit import run_dataset_audit
from registry.store import RegistryStore, now_iso

_BUCKET = os.getenv("ARTIFACTS_BUCKET", "")
_s3 = boto3.client("s3")
_store: RegistryStore | None = None


def _get_store() -> RegistryStore:
    global _store
    if _store is None:
        _store = RegistryStore()
    return _store


def _response(status: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def _parse_body(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        import base64

        raw = base64.b64decode(raw).decode("utf-8")
    return json.loads(raw) if isinstance(raw, str) else raw


def _route(event: dict[str, Any]) -> tuple[str, str]:
    path = event.get("rawPath") or event.get("path") or ""
    method = (
        event.get("requestContext", {}).get("http", {}).get("method")
        or event.get("httpMethod")
        or "GET"
    )
    return method.upper(), path


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug[:48] or "dataset"


def _resolve_dataset_key(payload: dict[str, Any]) -> str:
    if payload.get("dataset_key"):
        return str(payload["dataset_key"])
    if payload.get("s3_key"):
        return str(payload["s3_key"])
    uri = str(payload.get("dataset_s3_uri") or "")
    if uri.startswith("s3://"):
        parsed = urlparse(uri)
        return parsed.path.lstrip("/")
    dataset_id = str(payload.get("dataset_id") or "latest")
    return f"datasets/pending/{dataset_id}/train.jsonl"


def _split_keys(dataset_key: str) -> tuple[str, str]:
    path = Path(dataset_key)
    prefix = str(path.parent)
    train_key = dataset_key if path.name.startswith("train") else f"{prefix}/train.jsonl"
    dev_key = f"{prefix}/dev.jsonl"
    return train_key, dev_key


def _upload_report(report: dict[str, Any]) -> str:
    report_key = f"reports/audit/{report['report_id']}.json"
    _s3.put_object(
        Bucket=_BUCKET,
        Key=report_key,
        Body=json.dumps(report, ensure_ascii=False).encode("utf-8"),
        ContentType="application/json",
    )
    return report_key


def _download_dataset(dataset_key: str) -> Path:
    suffix = Path(dataset_key).suffix or ".jsonl"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.close()
    _s3.download_file(_BUCKET, dataset_key, tmp.name)
    return Path(tmp.name)


def _count_s3_lines(key: str) -> int:
    resp = _s3.get_object(Bucket=_BUCKET, Key=key)
    body = resp["Body"].read()
    return sum(1 for line in body.splitlines() if line.strip())


def _count_file_lines(path: Path) -> int:
    count = 0
    with path.open("rb") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def _split_stats_from_prefix(prefix: str, split_names: list[str]) -> dict[str, Any]:
    stats: dict[str, Any] = {}
    total_rows = 0
    for split in split_names:
        filename = f"{split}.jsonl"
        key = f"{prefix}/{filename}"
        try:
            head = _s3.head_object(Bucket=_BUCKET, Key=key)
            rows = _count_s3_lines(key)
            size_bytes = int(head.get("ContentLength") or 0)
        except ClientError:
            rows = 0
            size_bytes = 0
        stats[split] = {"filename": filename, "rows": rows, "size_bytes": size_bytes}
        total_rows += rows
    return {"split_stats": stats, "total_rows": total_rows}


def _split_stats_from_paths(
    paths: dict[str, Path],
) -> tuple[dict[str, Any], int]:
    stats: dict[str, Any] = {}
    total_rows = 0
    for split, path in paths.items():
        rows = _count_file_lines(path)
        stats[split] = {
            "filename": f"{split}.jsonl",
            "rows": rows,
            "size_bytes": path.stat().st_size,
        }
        total_rows += rows
    return stats, total_rows


def _build_splits_payload(record: dict[str, Any]) -> dict[str, Any]:
    prefix = str(record.get("s3_prefix") or f"datasets/pending/{record.get('dataset_id')}").strip("/")
    split_names = record.get("splits") or ["train", "dev"]
    if isinstance(split_names, dict):
        split_names = list(split_names.keys())

    cached = record.get("split_stats") or {}
    splits_payload: dict[str, Any] = {}
    for split in split_names:
        filename = f"{split}.jsonl"
        if split in cached:
            info = cached[split]
            splits_payload[split] = {
                "filename": info.get("filename", filename),
                "rows": int(info.get("rows", 0)),
                "size_bytes": int(info.get("size_bytes", 0)),
            }
            continue
        if _BUCKET:
            key = f"{prefix}/{filename}"
            try:
                head = _s3.head_object(Bucket=_BUCKET, Key=key)
                rows = _count_s3_lines(key)
                size_bytes = int(head.get("ContentLength") or 0)
                splits_payload[split] = {"filename": filename, "rows": rows, "size_bytes": size_bytes}
                continue
            except ClientError:
                pass
        splits_payload[split] = {"filename": filename, "rows": 0, "size_bytes": 0}
    return splits_payload


def _load_audit_report(record: dict[str, Any]) -> dict[str, Any] | None:
    uri = str(record.get("audit_report_uri") or "")
    if not uri.startswith("s3://") or not _BUCKET:
        return None
    key = urlparse(uri).path.lstrip("/")
    try:
        obj = _s3.get_object(Bucket=_BUCKET, Key=key)
        return json.loads(obj["Body"].read())
    except ClientError:
        return None


def _slim_benchmarks(benchmarks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": str(row.get("id", "")),
            "name": str(row.get("name", "")),
            "description": str(row.get("description", "")),
            "value": float(row.get("value", 0)),
            "threshold": float(row.get("threshold", 0)),
            "unit": str(row.get("unit", "")),
            "higher_is_better": bool(row.get("higher_is_better")),
            "status": str(row.get("status", "fail")),
            "display_value": str(row.get("display_value", "")),
            "display_threshold": str(row.get("display_threshold", "")),
        }
        for row in benchmarks
    ]


def _audit_bundle_payload(
    report: dict[str, Any] | None,
    *,
    report_id: str,
    passed: bool,
    audit_score: float,
    generated_at: str,
) -> dict[str, Any]:
    summary = (report or {}).get("summary") or {}
    benchmarks = (report or {}).get("benchmarks") or []
    issues = (report or {}).get("issues") or []
    distributions = (report or {}).get("distributions") or {}

    return {
        "report_id": report_id or "unknown",
        "passed": passed,
        "audit_score": audit_score,
        "error_count": int(summary.get("error_count") or 0),
        "generated_at": generated_at,
        "data_level_status": (report or {}).get("data_level_status"),
        "failed_checks": [
            str(row.get("name") or row.get("id"))
            for row in benchmarks
            if row.get("status") == "fail"
        ],
        "benchmarks": _slim_benchmarks(benchmarks),
        "distributions": distributions,
        "issues": issues[:20],
        "issue_truncated": bool((report or {}).get("issue_truncated")) or len(issues) > 20,
        "summary": {
            "train_rows": int(summary.get("train_rows") or 0),
            "dev_rows": int(summary.get("dev_rows") or 0),
            "warning_count": int(summary.get("warning_count") or 0),
            "parsed_records": int(summary.get("parsed_records") or 0),
            "total_opinions": int(summary.get("total_opinions") or 0),
            "avg_opinions_per_record": float(summary.get("avg_opinions_per_record") or 0),
        },
    }


def _build_audits_payload(record: dict[str, Any]) -> dict[str, Any]:
    if (
        not record.get("audit_report_uri")
        and not record.get("audit_report_id")
        and record.get("audit_passed") is None
        and record.get("audit_score") is None
    ):
        return {}

    report = _load_audit_report(record)
    report_id = str(record.get("audit_report_id") or "")
    if not report_id:
        report_uri = str(record.get("audit_report_uri") or "")
        if report_uri:
            report_id = Path(urlparse(report_uri).path).stem
        elif report:
            report_id = str(report.get("report_id") or "unknown")

    bundle = _audit_bundle_payload(
        report,
        report_id=report_id,
        passed=bool(record.get("audit_passed")),
        audit_score=float(record.get("audit_score") or 0),
        generated_at=str(record.get("updated_at") or record.get("created_at") or now_iso()),
    )
    return {"bundle": bundle}


def _dataset_manifest(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "dataset_id": record.get("dataset_id"),
        "name": record.get("name", record.get("dataset_id")),
        "status": _normalize_dataset_status(str(record.get("status", "pending"))),
        "created_at": record.get("created_at", ""),
        "updated_at": record.get("updated_at", record.get("created_at", "")),
        "splits": _build_splits_payload(record),
        "audits": _build_audits_payload(record),
        "audit_passed": bool(record.get("audit_passed")),
    }


def _normalize_dataset_status(raw: str) -> str:
    status = raw.strip().lower()
    if status in {"pending_upload", "pending"}:
        return "pending"
    if status == "audit_passed":
        return "audited"
    if status == "audit_failed":
        return "failed"
    return status


def _audit_status_from_row(row: dict[str, Any]) -> str:
    if row.get("audit_passed"):
        return "pass"
    status = str(row.get("status", "")).upper()
    if status == "AUDIT_FAILED":
        return "fail"
    if status == "AUDIT_PASSED":
        return "pass"
    return "pending"


def _audit_score(report: dict[str, Any]) -> float:
    benchmarks = report.get("benchmarks") or []
    if not benchmarks:
        return 0.0
    passed = sum(1 for row in benchmarks if row.get("status") == "pass")
    return round(passed / len(benchmarks), 4)


def _audit_result(payload: dict[str, Any]) -> dict[str, Any]:
    dataset_key = _resolve_dataset_key(payload)
    if not _BUCKET:
        raise RuntimeError("ARTIFACTS_BUCKET is not configured")

    dataset_id = str(payload.get("dataset_id") or Path(dataset_key).parent.name)
    store = _get_store()
    if store.config.datasets_table:
        existing = store.get_dataset(dataset_id)
        if existing and str(existing.get("status", "")).upper() == "PENDING_UPLOAD":
            _handle_complete_upload(dataset_id)

    train_key, dev_key = _split_keys(dataset_key)
    train_path = _download_dataset(train_key)
    dev_path = _download_dataset(dev_key)
    dataset_id = str(payload.get("dataset_id") or Path(train_key).parent.name)
    split_stats, total_rows = _split_stats_from_paths({"train": train_path, "dev": dev_path})

    try:
        report = run_dataset_audit(
            train_path,
            dev_path,
            dataset_id=dataset_id,
            dataset_key=train_key,
            source_label=f"s3://{_BUCKET}/{Path(train_key).parent.name}",
        )
    finally:
        train_path.unlink(missing_ok=True)
        dev_path.unlink(missing_ok=True)

    report_key = _upload_report(report)
    score = _audit_score(report)
    status = "AUDIT_PASSED" if report["passed"] else "AUDIT_FAILED"
    if store.config.datasets_table:
        existing = store.get_dataset(dataset_id)
        updates = {
            "name": (existing or {}).get("name") or payload.get("name") or dataset_id,
            "status": status,
            "s3_uri": f"s3://{_BUCKET}/{Path(train_key).parent}/",
            "s3_prefix": str(Path(train_key).parent),
            "splits": list(split_stats.keys()),
            "split_stats": split_stats,
            "num_records": total_rows,
            "audit_report_uri": f"s3://{_BUCKET}/{report_key}",
            "audit_report_id": report["report_id"],
            "audit_passed": bool(report["passed"]),
            "audit_score": score,
        }
        if existing:
            store.update_dataset(dataset_id, str(existing["created_at"]), updates)
        else:
            store.put_dataset(
                {
                    "dataset_id": dataset_id,
                    "created_at": now_iso(),
                    **updates,
                }
            )

    bundle = _audit_bundle_payload(
        report,
        report_id=str(report["report_id"]),
        passed=bool(report["passed"]),
        audit_score=score,
        generated_at=now_iso(),
    )
    return {
        **bundle,
        "report_key": report_key,
        "dataset_id": dataset_id,
        "dataset_key": train_key,
        "summary": report.get("summary") or {},
        "modules": report.get("modules") or {},
    }


def _handle_presign(payload: dict[str, Any]) -> dict[str, Any]:
    name = str(payload.get("name") or "dataset").strip()
    dataset_id = payload.get("dataset_id") or f"{_slugify(name)}-{uuid.uuid4().hex[:8]}"
    prefix = f"datasets/pending/{dataset_id}"
    store = _get_store()
    uploads = {
        "train": store.presign_upload(f"{prefix}/train.jsonl"),
        "dev": store.presign_upload(f"{prefix}/dev.jsonl"),
    }
    if payload.get("include_test"):
        uploads["test"] = store.presign_upload(f"{prefix}/test.jsonl")

    created_at = now_iso()
    if store.config.datasets_table:
        store.put_dataset(
            {
                "dataset_id": dataset_id,
                "created_at": created_at,
                "name": name,
                "status": "PENDING_UPLOAD",
                "s3_uri": f"s3://{_BUCKET}/{prefix}/",
                "s3_prefix": prefix,
                "uploaded_by": payload.get("uploaded_by", "admin-ui"),
                "updated_at": created_at,
            }
        )

    return {
        "dataset_id": dataset_id,
        "prefix": prefix,
        "upload_urls": uploads,
        "expires_in": 900,
    }


def _handle_complete_upload(dataset_id: str) -> dict[str, Any]:
    store = _get_store()
    record = store.get_dataset(dataset_id)
    if record is None:
        raise KeyError(f"Dataset '{dataset_id}' not found")
    if not _BUCKET:
        raise RuntimeError("ARTIFACTS_BUCKET is not configured")

    prefix = str(record.get("s3_prefix") or f"datasets/pending/{dataset_id}").strip("/")
    discovered = _split_stats_from_prefix(prefix, ["train", "dev", "test"])
    splits = [split for split, info in discovered["split_stats"].items() if info["rows"] > 0]
    if not splits:
        raise FileNotFoundError(f"No uploaded splits found under s3://{_BUCKET}/{prefix}/")
    total_rows = discovered["total_rows"]

    store.update_dataset(
        dataset_id,
        str(record["created_at"]),
        {
            "status": "PENDING",
            "s3_uri": f"s3://{_BUCKET}/{prefix}/",
            "s3_prefix": prefix,
            "splits": splits,
            "split_stats": {split: discovered["split_stats"][split] for split in splits},
            "num_records": total_rows,
        },
    )
    return {
        "dataset_id": dataset_id,
        "status": "pending",
        "splits": splits,
        "total_rows": total_rows,
    }


def _handle_approve(dataset_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    store = _get_store()
    record = store.get_dataset(dataset_id)
    if record is None:
        raise KeyError(f"Dataset '{dataset_id}' not found")
    decision = str(payload.get("decision", "approve")).lower()
    status = "APPROVED" if decision == "approve" else "REJECTED"
    store.update_dataset(
        dataset_id,
        str(record["created_at"]),
        {
            "status": status,
            "approved_by": payload.get("approved_by", "admin-ui"),
            "approved_at": now_iso(),
        },
    )
    return {"dataset_id": dataset_id, "status": status}


def _handle_list_datasets() -> dict[str, Any]:
    store = _get_store()
    if not store.config.datasets_table:
        return {"datasets": []}
    rows = store.list_datasets(limit=50)
    datasets = []
    for row in rows:
        status = _normalize_dataset_status(str(row.get("status", "pending")))
        datasets.append(
            {
                "dataset_id": row.get("dataset_id"),
                "name": row.get("name", row.get("dataset_id")),
                "status": status,
                "created_at": row.get("created_at"),
                "splits": row.get("splits") or ["train", "dev"],
                "audit_passed": bool(row.get("audit_passed")),
                "audit_status": _audit_status_from_row(row),
                "audit_score": row.get("audit_score"),
                "total_rows": int(row.get("num_records", 0)),
            }
        )
    return {"datasets": datasets}


def _handle_http(event: dict[str, Any]) -> dict[str, Any]:
    method, path = _route(event)

    if path.endswith("/datasets/presign-upload") and method == "POST":
        try:
            payload = _parse_body(event)
            return _response(200, _handle_presign(payload))
        except json.JSONDecodeError:
            return _response(400, {"detail": "invalid JSON body"})
        except Exception as exc:  # noqa: BLE001
            return _response(500, {"detail": str(exc)})

    if path.endswith("/datasets") and method == "GET":
        return _response(200, _handle_list_datasets())

    if "/datasets/" in path and method == "GET":
        dataset_id = path.split("/datasets/")[1].split("/")[0]
        store = _get_store()
        record = store.get_dataset(dataset_id) if store.config.datasets_table else None
        if record is None:
            return _response(404, {"detail": f"Dataset '{dataset_id}' not found"})
        return _response(200, _dataset_manifest(record))

    if "/datasets/" in path and path.endswith("/audit") and method == "POST":
        dataset_id = path.split("/datasets/")[1].split("/")[0]
        try:
            payload = _parse_body(event)
            payload.setdefault("dataset_id", dataset_id)
            return _response(200, _audit_result(payload))
        except json.JSONDecodeError:
            return _response(400, {"detail": "invalid JSON body"})
        except Exception as exc:  # noqa: BLE001
            return _response(500, {"detail": str(exc)})

    if "/datasets/" in path and path.endswith("/approve") and method == "POST":
        dataset_id = path.split("/datasets/")[1].split("/")[0]
        try:
            payload = _parse_body(event)
            return _response(200, _handle_approve(dataset_id, payload))
        except KeyError as exc:
            return _response(404, {"detail": str(exc)})
        except Exception as exc:  # noqa: BLE001
            return _response(500, {"detail": str(exc)})

    return _response(404, {"detail": f"No route for {method} {path}"})


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    if event.get("requestContext") or event.get("rawPath") or event.get("path"):
        return _handle_http(event)

    if "body" in event and not event.get("action"):
        try:
            payload = _parse_body(event)
        except json.JSONDecodeError:
            return _response(400, {"detail": "invalid JSON body"})
    else:
        payload = event.get("Payload") if isinstance(event.get("Payload"), dict) else event

    action = payload.get("action")

    try:
        result = _audit_result(payload)
    except Exception as exc:  # noqa: BLE001
        if action in {"validate", "audit"}:
            return {"passed": False, "error": str(exc), "action": action}
        return _response(500, {"detail": str(exc)})

    if action in {"validate", "audit"}:
        return result

    return _response(200, result)
