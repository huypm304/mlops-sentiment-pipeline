#!/usr/bin/env python3
"""SageMaker training entry point — maps hyperparameters to train_kaggle.py (50-epoch GPU job).

Packaged with train_kaggle.py via scripts/build_training_package.sh.
Hyperparameters: /opt/ml/input/config/hyperparameters.json
Data channel: /opt/ml/input/data/training/{train,dev}.jsonl
Outputs: /opt/ml/model/* (train_log.csv, best_model.pt, run_config.json, …)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SM_HP_SKIP = frozenset(
    {
        "sagemaker_program",
        "sagemaker_submit_directory",
        "sagemaker_region",
        "train_s3_uri",
        "output_s3_uri",
        "training_source_s3_uri",
        "sagemaker_instance_type",
        "run_id",
    }
)

SM_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(SM_ROOT))


def _load_hyperparameters() -> dict:
    hp_path = Path("/opt/ml/input/config/hyperparameters.json")
    if hp_path.is_file():
        return json.loads(hp_path.read_text(encoding="utf-8"))
    return {}


def _resolve_channel_file(channel: str, names: tuple[str, ...]) -> Path | None:
    base = Path("/opt/ml/input/data") / channel
    if not base.is_dir():
        return None
    for name in names:
        candidate = base / name
        if candidate.is_file():
            return candidate
    return None


def _hyperparameters_to_argv(hp: dict[str, object], *, train_file: Path, val_file: Path, output_dir: Path) -> list[str]:
    argv = ["train_kaggle.py", "--train-file", str(train_file), "--val-file", str(val_file), "--output-dir", str(output_dir)]
    for key, value in hp.items():
        if key in SM_HP_SKIP or value is None or value == "":
            continue
        flag = f"--{key.replace('_', '-')}"
        if flag in {"--train-file", "--val-file", "--output-dir"}:
            continue
        argv.extend([flag, str(value)])
    return argv


def main() -> None:
    hp = _load_hyperparameters()
    model_dir = Path("/opt/ml/model")
    model_dir.mkdir(parents=True, exist_ok=True)

    train_file = _resolve_channel_file("training", ("train.jsonl",))
    val_file = _resolve_channel_file("training", ("dev.jsonl", "val.jsonl"))
    if train_file is None:
        raise FileNotFoundError("Missing train.jsonl under /opt/ml/input/data/training/")
    if val_file is None:
        raise FileNotFoundError("Missing dev.jsonl or val.jsonl under /opt/ml/input/data/training/")

    argv = _hyperparameters_to_argv(hp, train_file=train_file, val_file=val_file, output_dir=model_dir)
    if "--num-workers" not in argv:
        argv.extend(["--num-workers", "0"])
    print(f"Launching train_kaggle with argv: {argv}", flush=True)
    sys.argv = argv

    import train_kaggle  # noqa: WPS433 — packaged alongside this entrypoint

    train_kaggle.main()
    print(json.dumps({"status": "Completed", "output_dir": str(model_dir)}), flush=True)


if __name__ == "__main__":
    main()
