"""Run train+dev data benchmark audit and build JSON report."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


def _benchmark_candidates() -> list[Path]:
    """Resolve data_benchmark root in Lambda bundle or monorepo checkout."""
    here = Path(__file__).resolve()
    candidates: list[Path] = []

    # Lambda bundle: /var/task/data_benchmark (sibling of dataset_audit/)
    task_root = here.parents[1]
    candidates.append(task_root / "data_benchmark")

    # Monorepo: ml/data_processing (walk up — do not assume fixed parent depth)
    for parent in here.parents:
        ml_path = parent / "ml" / "data_processing"
        if (ml_path / "engine.py").is_file():
            candidates.append(ml_path)
            break

    # De-dupe while preserving order
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in candidates:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(resolved)
    return unique


def _ensure_benchmark_path() -> Path:
    for candidate in _benchmark_candidates():
        if (candidate / "engine.py").is_file():
            root = str(candidate)
            if root not in sys.path:
                sys.path.insert(0, root)
            return candidate
    raise FileNotFoundError(
        "data_benchmark package not found — run scripts/build_audit_lambda.sh before deploy"
    )


def run_dataset_audit(
    train_source: str | Path,
    dev_source: str | Path | None = None,
    *,
    test_source: str | Path | None = None,
    dataset_id: str = "",
    dataset_key: str = "",
    source_label: str = "",
    skip_integrity: bool = True,
) -> dict[str, Any]:
    """Audit a train+dev bundle using the data_benchmark suite."""
    _ensure_benchmark_path()
    from engine import run_data_benchmark  # noqa: E402

    train_path = Path(train_source)
    if dev_source is None:
        raise ValueError("dev_source is required — data benchmark audits train and dev together")

    dev_path = Path(dev_source)
    test_path = Path(test_source) if test_source else None

    return run_data_benchmark(
        train_path,
        dev_path,
        test_path=test_path,
        skip_integrity=skip_integrity,
        dataset_id=dataset_id,
        dataset_key=dataset_key,
        source_label=source_label,
    )
