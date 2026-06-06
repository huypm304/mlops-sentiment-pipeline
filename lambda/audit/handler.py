"""Audit Lambda — VLSP-style dataset quality checks + S3 report."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import boto3

from dataset_audit import run_dataset_audit

_BUCKET = os.getenv("ARTIFACTS_BUCKET", "")
_s3 = boto3.client("s3")


def _response(status: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def _parse_body(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("body") or "{}"
    return json.loads(raw) if isinstance(raw, str) else raw


def _upload_report(report: dict[str, Any], dataset_key: str) -> str:
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


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    if "body" in event:
        try:
            payload = _parse_body(event)
        except json.JSONDecodeError:
            return _response(400, {"detail": "invalid JSON body"})
    else:
        payload = event.get("Payload") or event

    dataset_key = payload.get("dataset_key") or payload.get("s3_key") or "datasets/raw/latest.jsonl"

    try:
        if _BUCKET:
            local_path = _download_dataset(dataset_key)
            try:
                report = run_dataset_audit(
                    local_path,
                    dataset_key=dataset_key,
                    source_label=f"s3://{_BUCKET}/{dataset_key}",
                )
            finally:
                local_path.unlink(missing_ok=True)
            report_key = _upload_report(report, dataset_key)
            report["report_key"] = report_key
        else:
            return _response(503, {"detail": "ARTIFACTS_BUCKET is not configured"})
    except Exception as exc:  # noqa: BLE001
        return _response(500, {"detail": str(exc)})

    if payload.get("action") == "audit":
        return report

    return _response(
        200,
        {
            "passed": report["passed"],
            "report_id": report["report_id"],
            "report_key": report.get("report_key"),
            "summary": report["summary"],
            "benchmarks": report["benchmarks"],
        },
    )
