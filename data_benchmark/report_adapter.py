"""Map data_benchmark outputs to the platform audit report schema."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ASPECT_ORDER = [
    "Fashion",
    "Electronics",
    "General",
    "Service",
    "Ship",
    "Price",
    "App",
]

SENTIMENT_LABELS = {0: "NEG", 1: "POS", 2: "NEU"}

MODULE_BENCHMARKS: list[dict[str, Any]] = [
    {
        "id": "schema_audit",
        "name": "Schema audit",
        "description": "Required fields, valid aspect/sentiment labels (train + dev)",
        "metric_key": "critical_error_pct_combined",
        "threshold_key": "critical_schema_error_target_pct",
        "threshold_default": 0.0,
        "unit": "percent",
        "higher_is_better": False,
    },
    {
        "id": "span_offset_audit",
        "name": "Span offset audit",
        "description": "Opinion span offsets match text on train split",
        "metric_key": "train_exact_pct",
        "threshold_key": "exact_offset_match_target_pct",
        "threshold_default": 99.5,
        "unit": "percent",
        "higher_is_better": True,
    },
    {
        "id": "label_consistency_audit",
        "name": "Label consistency",
        "description": "Suspicious aspect/sentiment annotation patterns",
        "metric_key": "aspect_suspicious_pct",
        "threshold_key": "aspect_suspicious_good_lt_pct",
        "threshold_default": 3.0,
        "unit": "percent",
        "higher_is_better": False,
    },
    {
        "id": "distribution_audit",
        "name": "Distribution audit",
        "description": "Per-aspect and aspect×sentiment cell coverage",
        "metric_key": "train_per_aspect_ge_300",
        "threshold_key": "train_per_aspect_min_opinions",
        "threshold_default": 300,
        "unit": "boolean",
        "higher_is_better": True,
    },
    {
        "id": "global_sentiment_audit",
        "name": "Global sentiment consistency",
        "description": "global_sentiment matches opinion polarity rule",
        "metric_key": "train_consistency_pct",
        "threshold_key": "consistency_good_ge_pct",
        "threshold_default": 95.0,
        "unit": "percent",
        "higher_is_better": True,
    },
    {
        "id": "leakage_audit",
        "name": "Train/dev leakage",
        "description": "Exact/near duplicate rows and conflicting labels",
        "metric_key": "exact_leakage_pct",
        "threshold_key": "exact_leakage_target_pct",
        "threshold_default": 0.0,
        "unit": "percent",
        "higher_is_better": False,
    },
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _module_status(summary: dict[str, Any], module_id: str) -> str:
    module = summary.get(module_id) or {}
    return str(module.get("status") or "unknown")


def _benchmark_status(module_status: str) -> str:
    if module_status == "fail":
        return "fail"
    if module_status == "warn":
        return "warn"
    return "pass"


def _display_value(value: Any, unit: str) -> str:
    if unit == "boolean":
        return "yes" if value else "no"
    if unit == "percent":
        if isinstance(value, bool):
            return "yes" if value else "no"
        return f"{float(value):.2f}%"
    return str(value)


def _display_threshold(threshold: Any, unit: str, *, higher_is_better: bool) -> str:
    if unit == "boolean":
        return "all checks true"
    if unit == "percent":
        if higher_is_better:
            return f"≥ {float(threshold):.1f}%"
        return f"≤ {float(threshold):.1f}%"
    return str(threshold)


def _metric_value(summary: dict[str, Any], module_id: str, metric_key: str) -> Any:
    module = summary.get(module_id) or {}
    return module.get(metric_key, 0)


def build_benchmark_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in MODULE_BENCHMARKS:
        module_id = spec["id"]
        module_status = _module_status(summary, module_id)
        value = _metric_value(summary, module_id, spec["metric_key"])
        threshold = spec["threshold_default"]
        status = _benchmark_status(module_status)
        rows.append(
            {
                "id": module_id,
                "name": spec["name"],
                "description": spec["description"],
                "value": value if not isinstance(value, bool) else (1.0 if value else 0.0),
                "threshold": threshold,
                "unit": spec["unit"],
                "higher_is_better": spec["higher_is_better"],
                "status": status,
                "display_value": _display_value(value, spec["unit"]),
                "display_threshold": _display_threshold(
                    threshold,
                    spec["unit"],
                    higher_is_better=spec["higher_is_better"],
                ),
                "module_status": module_status,
            }
        )
    return rows


def _extract_distributions(module_reports: dict[str, dict[str, Any]], train_path: Path) -> dict[str, dict[str, int]]:
    dist = module_reports.get("distribution_audit") or {}
    train = dist.get("train") or {}
    aspects: dict[str, int] = {name: 0 for name in ASPECT_ORDER}
    sentiments: dict[str, int] = {"NEG": 0, "POS": 0, "NEU": 0}

    for row in train.get("aspect_distribution") or []:
        aspect = row.get("aspect")
        if aspect in aspects:
            aspects[aspect] = int(row.get("opinions") or 0)

    for row in train.get("aspect_sentiment_matrix") or []:
        sentiments["NEG"] += int(row.get("NEG") or 0)
        sentiments["POS"] += int(row.get("POS") or 0)
        sentiments["NEU"] += int(row.get("NEU") or 0)

    global_sentiments = _count_global_sentiments(train_path)

    return {
        "aspects": aspects,
        "opinion_sentiments": sentiments,
        "global_sentiments": global_sentiments,
    }


def _count_global_sentiments(train_path: Path) -> dict[str, int]:
    counts = {"NEG": 0, "POS": 0, "NEU": 0}
    labels = {0: "NEG", 1: "POS", 2: "NEU"}
    with train_path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            value = json.loads(line).get("global_sentiment")
            if value in labels:
                counts[labels[value]] += 1
    return counts


def _collect_issues(module_reports: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []

    schema = module_reports.get("schema_audit") or {}
    for split in ("train", "dev"):
        split_data = schema.get(split) or {}
        for item in split_data.get("parse_errors") or []:
            issues.append(
                {
                    "line": item.get("line", 0),
                    "code": "JSON_PARSE",
                    "severity": "error",
                    "message": f"[{split}] {item.get('error', 'parse error')}",
                }
            )
        for item in split_data.get("schema_errors") or []:
            issues.append(
                {
                    "line": item.get("line", 0),
                    "code": item.get("code", "SCHEMA"),
                    "severity": "error",
                    "message": f"[{split}] {item.get('message', 'schema error')}",
                }
            )

    leakage = module_reports.get("leakage_audit") or {}
    same_diff = int((leakage.get("metrics") or {}).get("same_text_different_labels_count") or 0)
    if same_diff:
        issues.append(
            {
                "line": 0,
                "code": "LEAKAGE_LABEL_CONFLICT",
                "severity": "error",
                "message": f"{same_diff} train/dev pairs share text but disagree on labels",
            }
        )

    return issues[:500]


def build_audit_report(
    *,
    summary: dict[str, Any],
    module_reports: dict[str, dict[str, Any]],
    train_path: Path,
    dev_path: Path,
    dataset_id: str = "",
    dataset_key: str = "",
    source_label: str = "",
) -> dict[str, Any]:
    overall = summary.get("overall") or {}
    data_level_status = str(overall.get("data_level_status") or "unknown")
    passed = data_level_status != "fail"

    dataset_summary = summary.get("dataset_summary") or {}
    train_rows = int(dataset_summary.get("train_rows") or 0)
    train_opinions = int(dataset_summary.get("train_opinions") or 0)
    issues = _collect_issues(module_reports)
    error_count = sum(1 for item in issues if item["severity"] == "error")
    warning_count = sum(1 for item in issues if item["severity"] == "warning")
    for module_id, status in (overall.get("module_statuses") or {}).items():
        if status == "warn":
            warning_count += 1
        elif status == "fail":
            error_count += 1

    now = datetime.now(timezone.utc)
    report_id = now.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    label = source_label or f"{train_path.name} + {dev_path.name}"
    key = dataset_key or f"datasets/local/{dataset_id or train_path.stem}"

    return {
        "report_id": report_id,
        "generated_at": now.isoformat(),
        "dataset_id": dataset_id,
        "dataset_key": key,
        "source_label": label,
        "schema": "absa-data-benchmark-v1",
        "passed": passed,
        "data_level_status": data_level_status,
        "summary": {
            "total_lines": train_rows,
            "parsed_records": train_rows,
            "parse_errors": 0,
            "error_count": error_count,
            "warning_count": warning_count,
            "records_with_opinions": train_rows,
            "total_opinions": train_opinions,
            "avg_opinions_per_record": round(train_opinions / train_rows, 3) if train_rows else 0.0,
            "train_rows": train_rows,
            "dev_rows": _count_rows(dev_path),
        },
        "benchmarks": build_benchmark_rows(summary),
        "modules": summary,
        "module_reports": {name: {"status": _module_status(summary, name)} for name in summary if name != "overall" and name != "dataset_summary"},
        "distributions": _extract_distributions(module_reports, train_path),
        "issues": issues,
        "issue_truncated": len(issues) >= 500,
    }


def _count_rows(path: Path) -> int:
    count = 0
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count
