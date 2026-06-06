"""Run dataset audit and build JSON report."""

from __future__ import annotations

import json
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO, TextIO

from .benchmarks import build_benchmarks
from .constants import ASPECT_ORDER, SENTIMENT_LABELS, VALID_ASPECTS
from .validators import validate_record


def _iter_jsonl(source: str | Path | TextIO | BinaryIO) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    parse_errors: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []

    if isinstance(source, (str, Path)):
        path = Path(source)
        handle: TextIO = path.open(encoding="utf-8")
        close = True
    else:
        handle = source  # type: ignore[assignment]
        close = False

    try:
        for line_no, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                parse_errors.append(
                    {
                        "line": line_no,
                        "code": "JSON_PARSE",
                        "severity": "error",
                        "message": str(exc),
                    }
                )
    finally:
        if close:
            handle.close()

    return records, parse_errors


def run_dataset_audit(
    source: str | Path | TextIO | BinaryIO,
    *,
    dataset_key: str = "",
    source_label: str = "",
) -> dict[str, Any]:
    """Audit a JSONL ABSA dataset; return a serializable report."""
    records, parse_errors = _iter_jsonl(source)
    total_lines = len(records) + len(parse_errors)

    issues: list[dict[str, Any]] = list(parse_errors)
    line_results: list[dict[str, Any]] = []

    aspect_counter: Counter[str] = Counter()
    sentiment_counter: Counter[str] = Counter()
    global_sentiment_counter: Counter[str] = Counter()

    stats = {
        "total_records": len(records),
        "total_opinions": 0,
        "span_checked": 0,
        "span_mismatch": 0,
        "duplicate_opinions": 0,
        "empty_targets": 0,
        "invalid_aspect": 0,
        "invalid_sentiment": 0,
        "global_inconsistent": 0,
        "overlapping_spans": 0,
        "records_with_opinions": 0,
    }

    for line_no, record in enumerate(records, start=1):
        result = validate_record(record, line_no)
        line_results.append(result)
        issues.extend(result["issues"])

        for op in record.get("opinions") or []:
            stats["total_opinions"] += 1
            asp = op.get("aspect")
            if asp in VALID_ASPECTS:
                aspect_counter[str(asp)] += 1
            sent = op.get("sentiment")
            if sent in SENTIMENT_LABELS:
                sentiment_counter[SENTIMENT_LABELS[int(sent)]] += 1

        gs = record.get("global_sentiment")
        if gs in SENTIMENT_LABELS:
            global_sentiment_counter[SENTIMENT_LABELS[int(gs)]] += 1

        stats["span_checked"] += result["metrics"]["span_checked"]
        stats["span_mismatch"] += result["metrics"]["span_mismatch"]
        stats["duplicate_opinions"] += result["metrics"]["duplicate_opinions"]
        stats["empty_targets"] += result["metrics"]["empty_targets"]
        stats["invalid_aspect"] += result["metrics"]["invalid_aspect"]
        stats["invalid_sentiment"] += result["metrics"]["invalid_sentiment"]
        stats["global_inconsistent"] += result["metrics"]["global_inconsistent"]
        stats["overlapping_spans"] += result["metrics"]["overlapping_spans"]
        if result["metrics"]["opinion_count"] > 0:
            stats["records_with_opinions"] += 1

    benchmarks = build_benchmarks(stats, total_lines, len(parse_errors))
    error_count = sum(1 for i in issues if i["severity"] == "error")
    warning_count = sum(1 for i in issues if i["severity"] == "warning")
    passed = error_count == 0 and all(b["status"] == "pass" for b in benchmarks)

    now = datetime.now(timezone.utc)
    report_id = now.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]

    return {
        "report_id": report_id,
        "generated_at": now.isoformat(),
        "dataset_key": dataset_key,
        "source_label": source_label or str(source),
        "schema": "absa-vlsp-audit-v1",
        "passed": passed,
        "summary": {
            "total_lines": total_lines,
            "parsed_records": len(records),
            "parse_errors": len(parse_errors),
            "error_count": error_count,
            "warning_count": warning_count,
            "records_with_opinions": stats["records_with_opinions"],
            "total_opinions": stats["total_opinions"],
            "avg_opinions_per_record": round(
                stats["total_opinions"] / len(records), 3
            )
            if records
            else 0.0,
        },
        "benchmarks": benchmarks,
        "distributions": {
            "aspects": {name: aspect_counter.get(name, 0) for name in ASPECT_ORDER},
            "opinion_sentiments": dict(sentiment_counter),
            "global_sentiments": dict(global_sentiment_counter),
        },
        "issues": issues[:500],
        "issue_truncated": len(issues) > 500,
    }
