"""Programmatic ABSA data benchmark runner (train + dev bundle)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from report_adapter import build_audit_report

ROOT = Path(__file__).resolve().parent
AUDITS_DIR = ROOT / "audits"
DEFAULT_THRESHOLDS = ROOT / "config" / "thresholds.json"

AUDIT_MODULES: list[tuple[str, str]] = [
    ("schema_audit", "schema_audit.py"),
    ("span_offset_audit", "span_offset_audit.py"),
    ("label_consistency_audit", "label_consistency_audit.py"),
    ("distribution_audit", "distribution_audit.py"),
    ("global_sentiment_audit", "global_sentiment_audit.py"),
    ("leakage_audit", "leakage_audit.py"),
]


def resolve_benchmark_root() -> Path:
    candidates = [
        ROOT,
        Path(__file__).resolve().parents[1] / "data_benchmark",
        Path(__file__).resolve().parents[2] / "data_benchmark",
    ]
    for candidate in candidates:
        if (candidate / "run_data_benchmark.py").is_file():
            return candidate
    raise FileNotFoundError("data_benchmark package not found")


def _run_audit_script(
    script: Path,
    *,
    train: Path,
    dev: Path,
    output: Path,
    extra_args: list[str] | None = None,
) -> None:
    cmd = [
        sys.executable,
        str(script),
        "--train",
        str(train),
        "--dev",
        str(dev),
        "--output",
        str(output),
    ]
    if extra_args:
        cmd.extend(extra_args)
    subprocess.run(cmd, check=True)


def run_data_benchmark(
    train_path: Path,
    dev_path: Path,
    *,
    test_path: Path | None = None,
    thresholds_path: Path | None = None,
    skip_integrity: bool = True,
    near_threshold: float = 0.9,
    work_dir: Path | None = None,
    dataset_id: str = "",
    dataset_key: str = "",
    source_label: str = "",
) -> dict[str, Any]:
    """Run all benchmark modules and return a normalized audit report."""
    benchmark_root = resolve_benchmark_root()
    audits_dir = benchmark_root / "audits"
    thresholds = thresholds_path or benchmark_root / "config" / "thresholds.json"

    train_path = Path(train_path)
    dev_path = Path(dev_path)
    if not train_path.is_file():
        raise FileNotFoundError(f"Train file not found: {train_path}")
    if not dev_path.is_file():
        raise FileNotFoundError(f"Dev file not found: {dev_path}")

    cleanup = work_dir is None
    if work_dir is None:
        work_dir = Path(tempfile.mkdtemp(prefix="absa-benchmark-"))
    else:
        work_dir = Path(work_dir)
        work_dir.mkdir(parents=True, exist_ok=True)

    module_reports: dict[str, dict[str, Any]] = {}

    try:
        for name, filename in AUDIT_MODULES:
            out_path = work_dir / f"{name}.json"
            extra = ["--near-threshold", str(near_threshold)] if name == "leakage_audit" else None
            _run_audit_script(
                audits_dir / filename,
                train=train_path,
                dev=dev_path,
                output=out_path,
                extra_args=extra,
            )
            module_reports[name] = json.loads(out_path.read_text(encoding="utf-8"))

        if not skip_integrity:
            integrity_out = work_dir / "data_integrity_style_analysis.json"
            cmd = [
                sys.executable,
                str(audits_dir / "data_integrity.py"),
                "--train",
                str(train_path),
                "--dev",
                str(dev_path),
                "--output",
                str(integrity_out),
            ]
            if test_path and test_path.is_file():
                cmd.extend(["--test", str(test_path)])
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError:
                pass

        sys.path.insert(0, str(benchmark_root))
        from summarize import build_benchmark_summary  # noqa: E402

        summary = build_benchmark_summary(
            work_dir,
            train_path,
            thresholds_path=thresholds if thresholds.exists() else None,
        )
        summary_path = work_dir / "benchmark_summary.json"
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

        return build_audit_report(
            summary=summary,
            module_reports=module_reports,
            train_path=train_path,
            dev_path=dev_path,
            dataset_id=dataset_id,
            dataset_key=dataset_key,
            source_label=source_label,
        )
    finally:
        if cleanup:
            for path in work_dir.glob("*"):
                path.unlink(missing_ok=True)
            work_dir.rmdir()
