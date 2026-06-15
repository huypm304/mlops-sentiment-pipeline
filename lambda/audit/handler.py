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

    train_key, dev_key = _split_keys(dataset_key)
    train_path = _download_dataset(train_key)
    dev_path = _download_dataset(dev_key)
    dataset_id = str(payload.get("dataset_id") or Path(train_key).parent.name)

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
    store = _get_store()
    if store.config.datasets_table:
        existing = store.get_dataset(dataset_id)
        record = {
            "dataset_id": dataset_id,
            "created_at": existing["created_at"] if existing else now_iso(),
            "name": payload.get("name") or dataset_id,
            "status": status,
            "s3_uri": f"s3://{_BUCKET}/{Path(train_key).parent}/",
            "s3_prefix": str(Path(train_key).parent),
            "audit_report_uri": f"s3://{_BUCKET}/{report_key}",
            "audit_passed": bool(report["passed"]),
            "audit_score": score,
            "updated_at": now_iso(),
        }
        if existing:
            store.update_dataset(dataset_id, str(existing["created_at"]), record)
        else:
            store.put_dataset(record)

    return {
        "passed": bool(report["passed"]),
        "report_id": report["report_id"],
        "report_key": report_key,
        "data_level_status": report.get("data_level_status"),
        "summary": report.get("summary") or {},
        "benchmarks": report.get("benchmarks") or [],
        "modules": report.get("modules") or {},
        "dataset_id": dataset_id,
        "dataset_key": train_key,
        "audit_score": score,
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
        status = str(row.get("status", "pending")).lower()
        if status == "audit_passed":
            status = "audited"
        datasets.append(
            {
                "dataset_id": row.get("dataset_id"),
                "name": row.get("name", row.get("dataset_id")),
                "status": status,
                "created_at": row.get("created_at"),
                "splits": row.get("splits") or ["train", "dev"],
                "audit_passed": bool(row.get("audit_passed")),
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
        return _response(
            200,
            {
                "dataset_id": record.get("dataset_id", dataset_id),
                "name": record.get("name", dataset_id),
                "status": str(record.get("status", "pending")).lower(),
                "created_at": record.get("created_at", ""),
                "updated_at": record.get("updated_at", record.get("created_at", "")),
                "splits": {split: {"filename": f"{split}.jsonl", "rows": 0, "size_bytes": 0} for split in (record.get("splits") or ["train", "dev"])},
                "audits": {},
                "audit_passed": bool(record.get("audit_passed")),
            },
        )

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
