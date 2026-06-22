#!/usr/bin/env python3
"""SageMaker training entry point — reads hyperparameters and runs mock or real training.

Packaged with ml.inference modules via scripts/build_training_package.sh.
On SageMaker, hyperparameters arrive in /opt/ml/input/config/hyperparameters.json.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))


def _load_hyperparameters() -> dict:
    hp_path = Path("/opt/ml/input/config/hyperparameters.json")
    if hp_path.is_file():
        return json.loads(hp_path.read_text(encoding="utf-8"))
    return dict(os.environ)


def main() -> None:
    hp = _load_hyperparameters()
    model_dir = Path("/opt/ml/model")
    model_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "status": "Completed",
        "mode": "sagemaker-entrypoint",
        "hyperparameters": hp,
        "message": "Wire full ml.inference training loop here for GPU jobs",
    }
    (model_dir / "training_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    (model_dir / "run_config.json").write_text(
        json.dumps(hp, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(manifest))


if __name__ == "__main__":
    main()
