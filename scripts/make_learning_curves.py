#!/usr/bin/env python3
"""Generate learning curve plots from train_log.csv.

Usage:
    python scripts/make_learning_curves.py \\
        --train-log model/train_log.csv \\
        --output-dir artifacts/figures
"""

from __future__ import annotations

import argparse
import csv
import sys
import warnings
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
except ImportError:
    print("ERROR: matplotlib is required. Install with: pip install matplotlib")
    sys.exit(1)


PLOT_CONFIGS = [
    {
        "filename": "learning_curve_loss.png",
        "title": "Training Loss",
        "ylabel": "Loss",
        "metrics": [("train_loss", "Train Loss", "steelblue")],
    },
    {
        "filename": "learning_curve_metrics.png",
        "title": "Main Metrics (F1)",
        "ylabel": "F1",
        "metrics": [
            ("tas_relaxed_f1",   "TAS Relaxed F1",  "royalblue"),
            ("span_f1",          "Span F1",          "darkorange"),
            ("sent_matched_f1",  "Sent@Matched F1",  "green"),
            ("global_f1",        "Global F1",        "red"),
        ],
    },
    {
        "filename": "learning_curve_tas_relaxed.png",
        "title": "TAS Relaxed F1",
        "ylabel": "F1",
        "metrics": [
            ("tas_relaxed_f1",  "TAS Relaxed F1", "royalblue"),
            ("tas_strict_f1",   "TAS Strict F1",  "navy"),
        ],
    },
    {
        "filename": "learning_curve_span_f1.png",
        "title": "Span Extraction F1",
        "ylabel": "F1",
        "metrics": [("span_f1", "Span F1", "darkorange")],
    },
    {
        "filename": "learning_curve_sent_matched.png",
        "title": "Sentiment@Matched F1",
        "ylabel": "F1",
        "metrics": [
            ("sent_matched_f1",  "Sent@Matched F1",   "green"),
            ("sent_goldspan_f1", "Sent@GoldSpan F1",  "limegreen"),
        ],
    },
    {
        "filename": "learning_curve_global_f1.png",
        "title": "Global Sentiment F1",
        "ylabel": "F1",
        "metrics": [("global_f1", "Global F1", "red")],
    },
]


def _load_csv(path: Path) -> tuple[list[str], list[dict]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = list(reader)
    return list(headers), rows


def _safe_float(val: str) -> float | None:
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _plot(config: dict, rows: list[dict], headers: list[str], out_dir: Path) -> bool:
    epochs = []
    series: dict[str, list] = {col: [] for col, _, _ in config["metrics"]}
    best_epochs = []

    for row in rows:
        epoch = _safe_float(row.get("epoch", ""))
        if epoch is None:
            continue
        epochs.append(int(epoch))
        if row.get("is_best") == "best":
            best_epochs.append(int(epoch))
        for col, _, _ in config["metrics"]:
            if col not in headers:
                continue
            series[col].append(_safe_float(row.get(col, "")))

    if not epochs:
        print(f"  WARNING: no data rows for {config['filename']}, skipping")
        return False

    available = [(col, label, color) for col, label, color in config["metrics"] if col in headers]
    if not available:
        missing = [col for col, _, _ in config["metrics"]]
        print(f"  WARNING: columns {missing} not in CSV, skipping {config['filename']}")
        return False

    fig, ax = plt.subplots(figsize=(10, 5))
    legend_patches = []
    for col, label, color in available:
        vals = series[col]
        if all(v is None for v in vals):
            continue
        clean_x = [e for e, v in zip(epochs, vals) if v is not None]
        clean_y = [v for v in vals if v is not None]
        ax.plot(clean_x, clean_y, color=color, linewidth=1.8, label=label)
        legend_patches.append(mpatches.Patch(color=color, label=label))

    for be in best_epochs:
        ax.axvline(be, color="gold", linewidth=1.2, linestyle="--", alpha=0.8)

    if best_epochs:
        best_patch = mpatches.Patch(color="gold", label=f"Best epoch ({best_epochs[-1]})", alpha=0.8)
        legend_patches.append(best_patch)

    ax.set_title(config["title"], fontsize=14)
    ax.set_xlabel("Epoch")
    ax.set_ylabel(config["ylabel"])
    ax.legend(handles=legend_patches, loc="best", fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    out_path = out_dir / config["filename"]
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Saved: {out_path}")
    return True


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate learning curve plots from train_log.csv")
    p.add_argument("--train-log",   type=Path, required=True,  help="Path to train_log.csv")
    p.add_argument("--output-dir",  type=Path, default=Path("artifacts/figures"))
    return p.parse_args()


def main() -> None:
    args = parse_args()

    if not args.train_log.is_file():
        print(f"ERROR: train_log.csv not found: {args.train_log}")
        sys.exit(1)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    headers, rows = _load_csv(args.train_log)
    print(f"Loaded {len(rows)} epoch rows from {args.train_log}")

    ok = 0
    for cfg in PLOT_CONFIGS:
        if _plot(cfg, rows, headers, args.output_dir):
            ok += 1

    print(f"\n{ok}/{len(PLOT_CONFIGS)} plots generated in {args.output_dir}")


if __name__ == "__main__":
    main()
