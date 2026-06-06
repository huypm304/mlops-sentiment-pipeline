#!/usr/bin/env python3
"""Export model artifacts to final_artifacts/model/ for deployment and packaging.

Generates: model_card.json, label_mapping.json, tokenizer_info.json,
postprocess_config.json, checksum.txt, requirements.txt, README.md.

Usage:
    python scripts/export_model_artifacts.py \\
        --model-path model/best_model.pt \\
        --run-config model/run_config.json \\
        --eval-report final_artifacts/evaluation/eval_report.json \\
        --train-log model/train_log.csv \\
        --output-dir final_artifacts/model \\
        --model-version absa-v2b
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.absa.labels import ASPECTS, N_BIO, N_SENT, SENT_ID2LABEL, SENT_LABEL2ID, BIO_LABELS
from src.absa.postprocess import PostprocessConfig


def _md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_json_safe(path: Path | None) -> dict:
    if path and path.is_file():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _best_metrics(train_log: Path | None, eval_report: dict) -> dict:
    metrics: dict = {}

    # Prefer eval report (fresh run)
    if eval_report:
        metrics = {
            "tas_strict_f1":   round(eval_report.get("tas_strict", {}).get("f1", 0.0), 4),
            "tas_relaxed_f1":  round(eval_report.get("tas_relaxed", {}).get("f1", 0.0), 4),
            "span_f1":         round(eval_report.get("span", {}).get("f1", 0.0), 4),
            "sent_matched_f1": round(eval_report.get("sent_matched", {}).get("f1", 0.0), 4),
            "global_f1":       round(eval_report.get("global", {}).get("f1", 0.0), 4),
        }
        return metrics

    # Fallback to train_log best epoch
    if train_log and train_log.is_file():
        with open(train_log, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("is_best") == "best":
                    metrics = {
                        "tas_strict_f1":   float(row.get("tas_strict_f1", 0.0)),
                        "tas_relaxed_f1":  float(row.get("tas_relaxed_f1", 0.0)),
                        "span_f1":         float(row.get("span_f1", 0.0)),
                        "sent_matched_f1": float(row.get("sent_matched_f1", 0.0)),
                        "global_f1":       float(row.get("global_f1", 0.0)),
                    }
    return metrics


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export model artifacts for deployment")
    p.add_argument("--model-path",    type=Path, default=Path("model/best_model.pt"))
    p.add_argument("--run-config",    type=Path, default=Path("model/run_config.json"))
    p.add_argument("--eval-report",   type=Path, default=None,
                   help="eval_report.json from eval_model.py (optional)")
    p.add_argument("--train-log",     type=Path, default=Path("model/train_log.csv"))
    p.add_argument("--output-dir",    type=Path, default=Path("final_artifacts/model"))
    p.add_argument("--model-version", default="absa-v2b")
    p.add_argument("--copy-checkpoint", action="store_true",
                   help="Copy best_model.pt to output-dir (default: write pointer.txt only)")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    run_config = _load_json_safe(args.run_config)
    eval_report = _load_json_safe(args.eval_report)
    metrics = _best_metrics(args.train_log, eval_report)

    model_name = run_config.get("model_name", "Fsoft-AIC/videberta-base")
    max_len    = int(run_config.get("max_len", 192))
    max_ops    = int(run_config.get("max_ops", 6))

    # -----------------------------------------------------------------------
    # Checkpoint: copy or pointer
    # -----------------------------------------------------------------------
    if args.model_path.is_file():
        ckpt_md5 = _md5(args.model_path)
        if args.copy_checkpoint:
            dest = out / "best_model.pt"
            shutil.copy2(args.model_path, dest)
            print(f"Copied checkpoint → {dest}")
        else:
            (out / "pointer.txt").write_text(
                f"# Checkpoint pointer\n"
                f"path={args.model_path.resolve()}\n"
                f"md5={ckpt_md5}\n",
                encoding="utf-8",
            )
            print(f"Wrote pointer.txt (checkpoint at {args.model_path})")
    else:
        ckpt_md5 = "unavailable"
        print(f"WARNING: checkpoint not found: {args.model_path}")

    # -----------------------------------------------------------------------
    # run_config.json
    # -----------------------------------------------------------------------
    out_cfg = out / "run_config.json"
    with open(out_cfg, "w", encoding="utf-8") as f:
        json.dump(run_config, f, ensure_ascii=False, indent=2)
    print(f"Wrote run_config.json")

    # -----------------------------------------------------------------------
    # label_mapping.json
    # -----------------------------------------------------------------------
    label_mapping = {
        "aspects": ASPECTS,
        "n_aspects": len(ASPECTS),
        "aspect_padding_idx": len(ASPECTS),
        "sentiment_id2label": SENT_ID2LABEL,
        "sentiment_label2id": SENT_LABEL2ID,
        "n_sentiment": N_SENT,
        "bio_labels": BIO_LABELS,
        "n_bio": N_BIO,
    }
    with open(out / "label_mapping.json", "w", encoding="utf-8") as f:
        json.dump(label_mapping, f, ensure_ascii=False, indent=2)
    print("Wrote label_mapping.json")

    # -----------------------------------------------------------------------
    # tokenizer_info.json
    # -----------------------------------------------------------------------
    tokenizer_info = {
        "model_name": model_name,
        "max_len": max_len,
        "return_offsets_mapping": True,
        "return_special_tokens_mask": True,
        "padding": "max_length",
        "truncation": True,
        "notes": "Uses AutoTokenizer.from_pretrained(model_name)",
    }
    with open(out / "tokenizer_info.json", "w", encoding="utf-8") as f:
        json.dump(tokenizer_info, f, ensure_ascii=False, indent=2)
    print("Wrote tokenizer_info.json")

    # -----------------------------------------------------------------------
    # postprocess_config.json
    # -----------------------------------------------------------------------
    pp_cfg = PostprocessConfig()
    with open(out / "postprocess_config.json", "w", encoding="utf-8") as f:
        json.dump(pp_cfg.to_dict(), f, ensure_ascii=False, indent=2)
    print("Wrote postprocess_config.json")

    # -----------------------------------------------------------------------
    # model_card.json
    # -----------------------------------------------------------------------
    model_card = {
        "model_version": args.model_version,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "task": "Vietnamese Aspect-Based Sentiment Analysis (ABSA)",
        "backbone": model_name,
        "architecture": {
            "heads": ["BIO tagging (CRF)", "span-level sentiment", "global sentiment"],
            "components": [
                "ViDeBERTa encoder", "BiLSTM BIO tagger", "CRF decoder",
                "attention-weighted span pooling", "cross-attention (seq→span)",
                "span self-attention", "aspect embedding", "clause position embedding",
                "polarity-aware global head",
            ],
            "max_ops": max_ops,
            "max_len": max_len,
        },
        "aspects": ASPECTS,
        "sentiment_labels": SENT_ID2LABEL,
        "dataset_version": run_config.get("train_file", "absa-datav3 (Kaggle)"),
        "training_args": {
            "seed": run_config.get("seed", 42),
            "epochs": run_config.get("epochs"),
            "batch_size": run_config.get("batch_size"),
            "lr_backbone": run_config.get("lr_backbone"),
            "lr_heads": run_config.get("lr_heads"),
            "max_ops": max_ops,
            "max_len": max_len,
        },
        "main_metrics": metrics,
        "hard_stress_metrics": {},
        "intended_use": [
            "Aspect-level sentiment analysis on Vietnamese e-commerce/review text",
            "Demo and portfolio purposes",
            "MLOps pipeline endpoint on SageMaker",
        ],
        "not_intended_use": [
            "High-stakes decision-making without human review",
            "Non-Vietnamese text without re-training",
            "Real-time production without confidence threshold + review queue",
        ],
        "known_limitations": [
            "Weak on implicit opinions and sarcasm",
            "May fail on clean-short multi-aspect stress cases",
            "Boundary errors may occur on short (1-token) targets",
            "Confidence threshold and review queue are strongly recommended in production",
            "Training data may not cover all product domains equally",
        ],
        "status": "production_candidate",
        "checkpoint_md5": ckpt_md5,
    }
    with open(out / "model_card.json", "w", encoding="utf-8") as f:
        json.dump(model_card, f, ensure_ascii=False, indent=2)
    print("Wrote model_card.json")

    # -----------------------------------------------------------------------
    # requirements.txt
    # -----------------------------------------------------------------------
    reqs = [
        "torch>=2.0.0",
        "transformers>=4.36.0",
        "pytorch-crf>=0.7.2",
        "scikit-learn>=1.3.0",
        "numpy>=1.24.0",
        "fastapi>=0.110.0",
        "uvicorn>=0.29.0",
        "pydantic>=2.6.0",
    ]
    (out / "requirements.txt").write_text("\n".join(reqs) + "\n", encoding="utf-8")
    print("Wrote requirements.txt")

    # -----------------------------------------------------------------------
    # checksum.txt
    # -----------------------------------------------------------------------
    checksums = []
    for fpath in sorted(out.iterdir()):
        if fpath.is_file() and fpath.name != "checksum.txt":
            checksums.append(f"{_md5(fpath)}  {fpath.name}")
    (out / "checksum.txt").write_text("\n".join(checksums) + "\n", encoding="utf-8")
    print("Wrote checksum.txt")

    # -----------------------------------------------------------------------
    # README.md
    # -----------------------------------------------------------------------
    readme = f"""# ABSA Model Artifacts

Version: **{args.model_version}**

## Contents

| File | Description |
|------|-------------|
| `best_model.pt` / `pointer.txt` | Checkpoint or path pointer |
| `run_config.json` | Hyperparameters used during training |
| `label_mapping.json` | ASPECTS, BIO labels, sentiment mapping |
| `tokenizer_info.json` | Tokenizer configuration |
| `postprocess_config.json` | Inference post-processing thresholds |
| `model_card.json` | Full model card (architecture, metrics, limitations) |
| `requirements.txt` | Python dependencies |
| `checksum.txt` | MD5 checksums for all files |

## Quick inference

```python
import sys; sys.path.insert(0, ".")
from src.absa.inference import load_model, predict_one

bundle = load_model("final_artifacts/model")
result = predict_one("Giá mềm nhưng giao hàng chậm", bundle)
print(result)
```

## Metrics (best epoch)

{json.dumps(metrics, indent=2, ensure_ascii=False)}

## Known limitations

- Weak on implicit/sarcastic opinions
- Boundary errors on very short targets
- Confidence threshold + review queue recommended for production
"""
    (out / "README.md").write_text(readme, encoding="utf-8")
    print("Wrote README.md")

    print(f"\nAll artifacts exported to: {out.resolve()}")


if __name__ == "__main__":
    main()
