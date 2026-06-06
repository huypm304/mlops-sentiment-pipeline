"""Run train+dev data benchmark audit and build JSON report."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[3]
_BENCHMARK_CANDIDATES = [
    Path(__file__).resolve().parents[1] / "data_benchmark",
    _REPO / "data_benchmark",
]


def _ensure_benchmark_path() -> Path:
    for candidate in _BENCHMARK_CANDIDATES:
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
