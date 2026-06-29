#!/usr/bin/env python3
"""Orchestrator — generate all evaluation reports and figures.

Calls make_learning_curves, make_confusion_plots, and merges eval JSONs.

Usage:
    python scripts/generate_reports.py \\
        --train-log model/train_log.csv \\
        --confusion-file model/best_confusion_matrices.json \\
        --eval-main artifacts/evaluation/eval_report.json \\
        --output-dir artifacts
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

ASPECTS = ["Fashion", "Electronics", "General", "Service", "Ship", "Price", "App"]


def _run(cmd: list[str]) -> None:
    print(f"  Running: {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"  WARNING: command exited with code {result.returncode}")


def _load_json_safe(path: Path) -> dict | None:
    if not path.is_file():
        print(f"  WARNING: {path} not found, skipping")
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  WARNING: could not read {path}: {e}")
        return None


def _build_summary_metrics(eval_main: dict | None, eval_hard: dict | None, train_log: Path | None) -> dict:
    summary: dict = {"source": "generate_reports.py"}

    if eval_main:
        summary["main_eval"] = {
            "tas_strict_f1":    round(eval_main.get("tas_strict", {}).get("f1", 0.0), 4),
            "tas_relaxed_f1":   round(eval_main.get("tas_relaxed", {}).get("f1", 0.0), 4),
            "span_f1":          round(eval_main.get("span", {}).get("f1", 0.0), 4),
            "sent_matched_f1":  round(eval_main.get("sent_matched", {}).get("f1", 0.0), 4),
            "sent_goldspan_f1": round(eval_main.get("sent_goldspan", {}).get("f1", 0.0), 4),
            "global_f1":        round(eval_main.get("global", {}).get("f1", 0.0), 4),
        }

    if eval_hard:
        summary["hard_eval"] = {
            "tas_strict_f1":   round(eval_hard.get("tas_strict", {}).get("f1", 0.0), 4),
            "tas_relaxed_f1":  round(eval_hard.get("tas_relaxed", {}).get("f1", 0.0), 4),
            "span_f1":         round(eval_hard.get("span", {}).get("f1", 0.0), 4),
            "sent_matched_f1": round(eval_hard.get("sent_matched", {}).get("f1", 0.0), 4),
            "global_f1":       round(eval_hard.get("global", {}).get("f1", 0.0), 4),
        }

    if train_log and train_log.is_file():
        best_row = _best_epoch_from_csv(train_log)
        if best_row:
            summary["best_training_epoch"] = best_row

    return summary


def _best_epoch_from_csv(path: Path) -> dict | None:
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            best = None
            for row in reader:
                if row.get("is_best") == "best":
                    best = {
                        "epoch": int(row.get("epoch", 0)),
                        "phase": row.get("phase", ""),
                        "tas_relaxed_f1":  float(row.get("tas_relaxed_f1", 0)),
                        "span_f1":         float(row.get("span_f1", 0)),
                        "sent_matched_f1": float(row.get("sent_matched_f1", 0)),
                        "global_f1":       float(row.get("global_f1", 0)),
                    }
        return best
    except Exception:
        return None


def _build_per_aspect_comparison(eval_main: dict | None, eval_hard: dict | None, out_csv: Path) -> None:
    rows = []
    for asp in ASPECTS:
        row = {"aspect": asp}
        if eval_main:
            row["main_span_f1"]  = round(float(eval_main.get("asp_span_f1", {}).get(asp, 0.0)), 4)
            row["main_sent_f1"]  = round(float(eval_main.get("asp_sent_f1", {}).get(asp, 0.0)), 4)
        if eval_hard:
            row["hard_span_f1"] = round(float(eval_hard.get("asp_span_f1", {}).get(asp, 0.0)), 4)
            row["hard_sent_f1"] = round(float(eval_hard.get("asp_sent_f1", {}).get(asp, 0.0)), 4)
        rows.append(row)

    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"  Saved: {out_csv}")


def _make_comparison_plot(eval_main: dict | None, eval_hard: dict | None, out_dir: Path) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("  WARNING: matplotlib not available, skipping comparison plot")
        return

    if not eval_main and not eval_hard:
        return

    metrics = ["tas_relaxed_f1", "span_f1", "sent_matched_f1", "global_f1"]
    labels = ["TAS Relaxed", "Span F1", "Sent@Matched", "Global F1"]

    main_vals = [eval_main.get(m.split("_f1")[0], {}).get("f1", 0.0) if eval_main else 0.0
                 for m in metrics]
    hard_vals = [eval_hard.get(m.split("_f1")[0], {}).get("f1", 0.0) if eval_hard else 0.0
                 for m in metrics]

    x = np.arange(len(metrics))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    if eval_main:
        ax.bar(x - width/2, main_vals, width, label="Main Dev", color="steelblue")
    if eval_hard:
        ax.bar(x + width/2, hard_vals, width, label="Hard/Stress Dev", color="salmon")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel("F1")
    ax.set_title("Main vs Hard Evaluation Comparison")
    ax.set_ylim(0, 1.0)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()

    out_path = out_dir / "main_vs_hard_comparison.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Saved: {out_path}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate all evaluation reports and figures")
    p.add_argument("--train-log",       type=Path, default=Path("model/train_log.csv"))
    p.add_argument("--confusion-file",  type=Path, default=Path("model/best_confusion_matrices.json"))
    p.add_argument("--eval-main",       type=Path, default=None,
                   help="Main eval_report.json (from eval_model.py)")
    p.add_argument("--eval-hard",       type=Path, default=None,
                   help="Hard/stress eval_report.json (optional)")
    p.add_argument("--output-dir",      type=Path, default=Path("artifacts"),
                   help="Root output directory (figures/, evaluation/ subdirs created)")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    figures_dir    = args.output_dir / "figures"
    evaluation_dir = args.output_dir / "evaluation"
    figures_dir.mkdir(parents=True, exist_ok=True)
    evaluation_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Learning curves
    if args.train_log.is_file():
        print("\n--- Generating learning curves ---")
        _run([sys.executable, str(REPO_ROOT / "scripts/make_learning_curves.py"),
              "--train-log", str(args.train_log),
              "--output-dir", str(figures_dir)])
    else:
        print(f"WARNING: train_log not found: {args.train_log}, skipping learning curves")

    # Step 2: Confusion matrix plots
    if args.confusion_file.is_file():
        print("\n--- Generating confusion matrix plots ---")
        _run([sys.executable, str(REPO_ROOT / "scripts/make_confusion_plots.py"),
              "--confusion-file", str(args.confusion_file),
              "--output-dir", str(figures_dir)])
    else:
        print(f"WARNING: confusion file not found: {args.confusion_file}, skipping")

    # Step 3: Load eval JSONs
    eval_main = _load_json_safe(args.eval_main) if args.eval_main else None
    eval_hard = _load_json_safe(args.eval_hard) if args.eval_hard else None

    # Step 4: Summary metrics
    print("\n--- Building summary metrics ---")
    summary = _build_summary_metrics(eval_main, eval_hard, args.train_log)
    out_summary = evaluation_dir / "summary_metrics.json"
    with open(out_summary, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {out_summary}")

    # Step 5: Per-aspect CSV
    if eval_main or eval_hard:
        print("\n--- Per-aspect comparison ---")
        _build_per_aspect_comparison(eval_main, eval_hard, evaluation_dir / "per_aspect_report.csv")

    # Step 6: Comparison plot
    if eval_main or eval_hard:
        print("\n--- Comparison plot ---")
        _make_comparison_plot(eval_main, eval_hard, figures_dir)

    # Step 7: Per-aspect figure bars
    if eval_main:
        _plot_per_aspect_bars(eval_main, figures_dir)

    print(f"\n✓ Reports generated under: {args.output_dir.resolve()}")


def _plot_per_aspect_bars(eval_main: dict, out_dir: Path) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return

    asp_span = eval_main.get("asp_span_f1", {})
    asp_sent = eval_main.get("asp_sent_f1", {})

    for data, title, filename in [
        (asp_span, "Per-Aspect Span F1", "per_aspect_span_f1.png"),
        (asp_sent, "Per-Aspect Sentiment F1", "per_aspect_sent_f1.png"),
    ]:
        vals = [float(data.get(a, 0.0)) for a in ASPECTS]
        fig, ax = plt.subplots(figsize=(9, 4))
        colors = ["steelblue" if v >= 0.5 else "salmon" for v in vals]
        ax.bar(ASPECTS, vals, color=colors)
        ax.set_ylim(0, 1.0)
        ax.set_ylabel("F1")
        ax.set_title(title)
        ax.grid(axis="y", alpha=0.3)
        for i, v in enumerate(vals):
            ax.text(i, v + 0.01, f"{v:.2f}", ha="center", va="bottom", fontsize=9)
        fig.tight_layout()
        out_path = out_dir / filename
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        print(f"  Saved: {out_path}")


if __name__ == "__main__":
    main()
