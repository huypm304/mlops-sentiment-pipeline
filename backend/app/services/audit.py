"""Dataset audit — uses shared engine under lambda/audit/dataset_audit."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[3]
_AUDIT_PKG = _REPO / "lambda" / "audit"
if str(_AUDIT_PKG) not in sys.path:
    sys.path.insert(0, str(_AUDIT_PKG))

from dataset_audit import run_dataset_audit  # noqa: E402

REPORTS_DIR = _REPO / "reports" / "audit"
DEFAULT_DATASET = _REPO / "model" / "data_train.jsonl"
DEMO_DATASET = _REPO / "model" / "demo_10.jsonl"


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
                    "dataset_key": data.get("dataset_key"),
                    "source_label": data.get("source_label"),
                    "passed": data.get("passed"),
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


def run_audit_on_path(
    dataset_path: Path,
    *,
    dataset_key: str = "",
) -> dict[str, Any]:
    if not dataset_path.is_file():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    report = run_dataset_audit(
        dataset_path,
        dataset_key=dataset_key or str(dataset_path.relative_to(_REPO)),
        source_label=str(dataset_path),
    )
    save_report(report)
    return report
