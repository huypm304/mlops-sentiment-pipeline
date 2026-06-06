"""Dataset audit — uses data_benchmark suite (train + dev bundle)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from backend.app.config.settings import REPO_ROOT

_AUDIT_PKG = REPO_ROOT / "lambda" / "audit"
if str(_AUDIT_PKG) not in sys.path:
    sys.path.insert(0, str(_AUDIT_PKG))

from dataset_audit import run_dataset_audit  # noqa: E402

from backend.app.services.datasets import BUNDLE_SPLIT

REPORTS_DIR = REPO_ROOT / "reports" / "audit"


def reports_dir() -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return REPORTS_DIR


def save_report(report: dict[str, Any]) -> Path:
    path = reports_dir() / f"{report['report_id']}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def list_reports(limit: int = 20) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in sorted(reports_dir().glob("*.json"), reverse=True)[:limit]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            items.append(
                {
                    "report_id": data.get("report_id", path.stem),
                    "generated_at": data.get("generated_at"),
                    "dataset_id": data.get("dataset_id"),
                    "dataset_key": data.get("dataset_key"),
                    "source_label": data.get("source_label"),
                    "passed": data.get("passed"),
                    "data_level_status": data.get("data_level_status"),
                    "summary": data.get("summary"),
                }
            )
        except (json.JSONDecodeError, OSError):
            continue
    return items


def load_report(report_id: str) -> dict[str, Any] | None:
    path = reports_dir() / f"{report_id}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def audit_score_from_report(report: dict[str, Any]) -> float:
    modules = report.get("modules") or {}
    module_statuses = (modules.get("overall") or {}).get("module_statuses")
    if module_statuses:
        passed = sum(1 for status in module_statuses.values() if status == "pass")
        return round(passed / len(module_statuses), 4)

    benchmarks = report.get("benchmarks") or []
    if not benchmarks:
        return 0.0
    passed = sum(1 for row in benchmarks if row.get("status") == "pass")
    return round(passed / len(benchmarks), 4)


def run_bundle_audit(
    *,
    train_path: Path,
    dev_path: Path,
    test_path: Path | None = None,
    dataset_id: str = "",
    dataset_key: str = "",
    source_label: str = "",
) -> dict[str, Any]:
    if not train_path.is_file():
        raise FileNotFoundError(f"Train split not found: {train_path}")
    if not dev_path.is_file():
        raise FileNotFoundError(f"Dev split not found: {dev_path}")

    report = run_dataset_audit(
        train_path,
        dev_path,
        test_source=test_path,
        dataset_id=dataset_id,
        dataset_key=dataset_key or f"datasets/local/{dataset_id or train_path.parent.name}",
        source_label=source_label,
    )
    save_report(report)
    return report
