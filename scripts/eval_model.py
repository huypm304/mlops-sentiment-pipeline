#!/usr/bin/env python3
"""Standalone evaluation script for the ABSA model.

Loads a checkpoint with strict=True, runs evaluate() on a dev/test file,
saves reports to output_dir, and optionally compares against baseline metrics
from train_log.csv.

Usage:
    python scripts/eval_model.py \\
        --model-path final_artifacts/model/best_model.pt \\
        --model-name Fsoft-AIC/videberta-base \\
        --eval-file /path/to/dev_clean.jsonl \\
        --output-dir final_artifacts/evaluation \\
        --max-len 192 --max-ops 6 --max-context-window 25 \\
        --span-match-iou 0.5 --strict-load true
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from transformers import AutoTokenizer

# Ensure repo root on path
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.absa.dataset import ABSADataset
from src.absa.evaluation import evaluate, print_eval_metrics_line, save_eval_report
from src.absa.model import ABSAModel
from src.absa.utils import ensure_dir, md5_file


# ---------------------------------------------------------------------------
# Baseline helpers
# ---------------------------------------------------------------------------

BASELINE_METRICS = {
    "tas_relaxed_f1": 0.5799,
    "span_f1": 0.8174,
    "sent_matched_f1": 0.6470,
    "global_f1": 0.6527,
}
WARN_THRESHOLD = 0.05  # absolute deviation triggers warning


def _read_best_baseline(train_log_csv: Path) -> dict[str, float] | None:
    """Read the best epoch row from train_log.csv."""
    if not train_log_csv.is_file():
        return None
    best: dict[str, float] = {}
    try:
        with open(train_log_csv, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("is_best") == "best":
                    best = {
                        "tas_relaxed_f1":  float(row.get("tas_relaxed_f1", 0.0)),
                        "span_f1":         float(row.get("span_f1", 0.0)),
                        "sent_matched_f1": float(row.get("sent_matched_f1", 0.0)),
                        "global_f1":       float(row.get("global_f1", 0.0)),
                    }
    except Exception as exc:
        print(f"WARNING: Could not parse train_log.csv: {exc}")
        return None
    return best if best else None


def _check_parity(eval_m: dict, baseline: dict, threshold: float = WARN_THRESHOLD) -> None:
    metric_map = {
        "tas_relaxed_f1": ("tas_relaxed", "f1"),
        "span_f1":         ("span", "f1"),
        "sent_matched_f1": ("sent_matched", "f1"),
        "global_f1":       ("global", "f1"),
    }
    deviations = []
    for key, path in metric_map.items():
        expected = baseline.get(key)
        if expected is None:
            continue
        actual = eval_m[path[0]][path[1]]
        dev = abs(actual - expected)
        if dev > threshold:
            deviations.append(f"  {key}: actual={actual:.4f}, expected={expected:.4f}, diff={dev:.4f}")

    if deviations:
        print()
        print("WARNING: Eval metric differs significantly from expected training log.")
        print("Check model class, checkpoint, dataset version, and evaluator.")
        for line in deviations:
            print(line)
        print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="ABSA model evaluation script")
    p.add_argument("--model-path",         type=Path, required=True,
                   help="Path to best_model.pt checkpoint")
    p.add_argument("--model-name",         default="Fsoft-AIC/videberta-base",
                   help="HuggingFace model name used during training")
    p.add_argument("--eval-file",          type=Path, required=True,
                   help="JSONL eval file (dev_clean.jsonl schema: text, opinions, global_sentiment)")
    p.add_argument("--output-dir",         type=Path, default=Path("final_artifacts/evaluation"),
                   help="Directory to save eval reports")
    p.add_argument("--max-len",            type=int, default=192)
    p.add_argument("--max-ops",            type=int, default=6)
    p.add_argument("--max-context-window", type=int, default=25)
    p.add_argument("--span-match-iou",     type=float, default=0.5)
    p.add_argument("--batch-size",         type=int, default=32)
    p.add_argument("--num-workers",        type=int, default=0)
    p.add_argument("--strict-load",        type=lambda x: x.lower() not in ("false", "0", "no"),
                   default=True, help="Load checkpoint with strict=True (default)")
    p.add_argument("--device",             default=None, help="cuda or cpu (auto-detect if unset)")
    p.add_argument("--train-log",          type=Path, default=Path("model/train_log.csv"),
                   help="Path to train_log.csv for baseline comparison")
    p.add_argument("--warn-threshold",     type=float, default=WARN_THRESHOLD,
                   help="F1 deviation threshold to trigger parity warning")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    device = torch.device(args.device or ("cuda" if torch.cuda.is_available() else "cpu"))
    ensure_dir(args.output_dir)

    # -----------------------------------------------------------------------
    # Print file info + checksums
    # -----------------------------------------------------------------------
    print(f"Model path : {args.model_path.resolve()}")
    if args.model_path.is_file():
        print(f"Model MD5  : {md5_file(args.model_path)}")
    else:
        print("ERROR: model checkpoint not found:", args.model_path)
        sys.exit(1)

    print(f"Eval file  : {args.eval_file.resolve()}")
    if not args.eval_file.is_file():
        print("ERROR: eval file not found:", args.eval_file)
        sys.exit(1)
    print(f"Eval MD5   : {md5_file(args.eval_file)}")
    print(f"Device     : {device}")
    print(f"Strict load: {args.strict_load}")
    print()

    # -----------------------------------------------------------------------
    # Load tokenizer + dataset
    # -----------------------------------------------------------------------
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    print("Building eval dataset...")
    eval_ds = ABSADataset(
        args.eval_file, tokenizer,
        max_len=args.max_len,
        max_ops=args.max_ops,
        max_context_window=args.max_context_window,
    )
    eval_dl = DataLoader(
        eval_ds,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
    )

    # -----------------------------------------------------------------------
    # Build + load model
    # -----------------------------------------------------------------------
    print(f"Building model ({args.model_name})...")
    model = ABSAModel(args.model_name, args.max_ops).to(device)

    print("Loading checkpoint...")
    state = torch.load(args.model_path, map_location=device)
    if isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]
    cleaned = {(k[len("module."):] if k.startswith("module.") else k): v for k, v in state.items()}

    try:
        model.load_state_dict(cleaned, strict=args.strict_load)
    except RuntimeError as exc:
        print()
        print("FATAL: Checkpoint architecture mismatch.")
        print("strict=True is required. Do not bypass with strict=False.")
        print("Ensure ABSAModel class matches saved checkpoint.")
        print(f"Detail: {exc}")
        sys.exit(1)

    # Match train/train.py: model = ABSAModel(...).to(device).float()
    model.float()
    model.eval()
    print("Checkpoint loaded successfully.\n")

    # -----------------------------------------------------------------------
    # Evaluate
    # -----------------------------------------------------------------------
    print("Running evaluation...")
    eval_m = evaluate(model, eval_dl, device, args.max_ops, args.max_context_window, args.span_match_iou)

    # -----------------------------------------------------------------------
    # Print metrics
    # -----------------------------------------------------------------------
    print()
    print_eval_metrics_line(eval_m, prefix="Results: ")

    # -----------------------------------------------------------------------
    # Save reports
    # -----------------------------------------------------------------------
    save_eval_report(eval_m, args.output_dir)
    print(f"\nReports saved to: {args.output_dir.resolve()}")
    print(f"  eval_report.json")
    print(f"  confusion_matrix.json")
    print(f"  per_aspect_report.csv")
    print(f"  per_class_report.csv")

    # -----------------------------------------------------------------------
    # Parity check vs baseline
    # -----------------------------------------------------------------------
    baseline = _read_best_baseline(args.train_log) or BASELINE_METRICS
    _check_parity(eval_m, baseline, threshold=args.warn_threshold)

    # -----------------------------------------------------------------------
    # Save a run summary
    # -----------------------------------------------------------------------
    summary = {
        "model_path": str(args.model_path.resolve()),
        "eval_file": str(args.eval_file.resolve()),
        "model_md5": md5_file(args.model_path),
        "eval_file_md5": md5_file(args.eval_file),
        "device": str(device),
        "strict_load": args.strict_load,
        "args": {
            "max_len": args.max_len,
            "max_ops": args.max_ops,
            "max_context_window": args.max_context_window,
            "span_match_iou": args.span_match_iou,
        },
        "tas_strict_f1":    round(eval_m["tas_strict"]["f1"], 4),
        "tas_relaxed_f1":   round(eval_m["tas_relaxed"]["f1"], 4),
        "span_f1":          round(eval_m["span"]["f1"], 4),
        "sent_matched_f1":  round(eval_m["sent_matched"]["f1"], 4),
        "sent_goldspan_f1": round(eval_m["sent_goldspan"]["f1"], 4),
        "global_f1":        round(eval_m["global"]["f1"], 4),
    }
    out_summary = args.output_dir / "eval_run_summary.json"
    with open(out_summary, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"  eval_run_summary.json")


if __name__ == "__main__":
    main()
