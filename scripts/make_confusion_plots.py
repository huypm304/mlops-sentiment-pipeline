#!/usr/bin/env python3
"""Generate confusion matrix plots from confusion JSON files.

Reads either best_confusion_matrices.json or confusion_matrices.jsonl
(takes the last is_best=true row from JSONL).

Usage:
    python scripts/make_confusion_plots.py \\
        --confusion-file model/best_confusion_matrices.json \\
        --output-dir final_artifacts/figures
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    print("ERROR: matplotlib + numpy required. pip install matplotlib numpy")
    sys.exit(1)

SENTIMENT_LABELS = ["NEG", "POS", "NEU"]


def _load_matrices(path: Path) -> dict:
    """Load confusion matrices from JSON or JSONL (returns last best entry)."""
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()

    if suffix == ".jsonl":
        best = None
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if entry.get("is_best") or entry.get("phase"):
                best = entry
        if best is None:
            raise ValueError("No entries found in JSONL")
        return best.get("matrices", best)

    data = json.loads(text)
    # Handle {epoch, matrices: {...}} vs flat dict
    return data.get("matrices", data)


def _plot_matrix(
    matrix: list[list],
    labels: list[str],
    title: str,
    out_path: Path,
    normalized: bool = False,
) -> None:
    arr = np.array(matrix, dtype=float)
    if arr.size == 0:
        print(f"  WARNING: empty matrix for {title}, skipping")
        return

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(arr, interpolation="nearest", cmap="Blues" if not normalized else "YlOrRd")
    fig.colorbar(im, ax=ax)

    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_yticklabels(labels, fontsize=11)
    ax.set_xlabel("Predicted", fontsize=12)
    ax.set_ylabel("True", fontsize=12)
    ax.set_title(title, fontsize=13)

    thresh = arr.max() / 2.0
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            val = arr[i, j]
            text = f"{val:.2f}" if normalized else str(int(val))
            ax.text(j, i, text, ha="center", va="center",
                    color="white" if val > thresh else "black", fontsize=11)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Saved: {out_path}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate confusion matrix plots")
    p.add_argument("--confusion-file", type=Path, required=True,
                   help="Path to best_confusion_matrices.json or confusion_matrices.jsonl")
    p.add_argument("--output-dir", type=Path, default=Path("final_artifacts/figures"))
    p.add_argument("--normalized", action="store_true",
                   help="Plot normalized instead of raw counts")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    if not args.confusion_file.is_file():
        print(f"ERROR: confusion file not found: {args.confusion_file}")
        sys.exit(1)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    matrices = _load_matrices(args.confusion_file)

    plots = [
        ("sentiment",       "Sentiment Confusion Matrix",           "sentiment_confusion_matrix.png"),
        ("sentiment_goldspan", "Sentiment@GoldSpan Confusion Matrix", "sentiment_goldspan_confusion_matrix.png"),
        ("global",          "Global Sentiment Confusion Matrix",    "global_confusion_matrix.png"),
        ("bio",             "BIO Tag Confusion Matrix",             "bio_confusion_matrix.png"),
    ]

    for key, title, filename in plots:
        if key not in matrices:
            print(f"  WARNING: '{key}' matrix not found, skipping {filename}")
            continue

        m_data = matrices[key]
        labels = m_data.get("labels", SENTIMENT_LABELS)
        matrix_key = "normalized" if (args.normalized and m_data.get("normalized")) else "raw"
        matrix = m_data.get(matrix_key, [])

        if not matrix:
            print(f"  WARNING: empty '{matrix_key}' matrix for {key}, skipping")
            continue

        if key == "bio" and len(labels) > 10:
            print(f"  INFO: BIO matrix is {len(labels)}x{len(labels)}, skipping (too large)")
            continue

        _plot_matrix(
            matrix,
            labels,
            title + (" (normalized)" if args.normalized and matrix_key == "normalized" else ""),
            args.output_dir / filename,
            normalized=(matrix_key == "normalized"),
        )

    print(f"\nDone. Output: {args.output_dir}")


if __name__ == "__main__":
    main()
