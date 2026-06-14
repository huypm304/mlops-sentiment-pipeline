"""Tests for DVC publish manifest builder."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys_path_inserted = False


def _import_publish():
    import sys

    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    import publish_approved_dataset as mod  # noqa: WPS433

    return mod


@pytest.fixture()
def sample_splits(tmp_path: Path):
    processed = tmp_path / "processed"
    processed.mkdir()
    for split, lines in {
        "train": ['{"text":"a"}\n', '{"text":"b"}\n'],
        "dev": ['{"text":"c"}\n'],
        "test": ['{"text":"d"}\n'],
    }.items():
        (processed / f"{split}.jsonl").write_text("".join(lines), encoding="utf-8")
    return processed


def test_build_manifest_schema(sample_splits: Path):
    mod = _import_publish()
    paths = mod._resolve_split_paths(sample_splits, mod.SPLITS)
    manifest = mod.build_manifest(
        dataset_id="dataset-v1",
        name="ABSA Benchmark v1",
        split_paths=paths,
        processed_dir=sample_splits,
        git_commit="abc123",
        dvc_remote_url="s3://absa-mlops-demo-artifacts/dvc-store",
        mirror_pending=True,
    )

    assert manifest["dataset_id"] == "dataset-v1"
    assert manifest["source"] == "dvc"
    assert manifest["status"] == "approved"
    assert manifest["s3_approved_prefix"] == "datasets/approved/dataset-v1/"
    assert manifest["splits"]["train"]["rows"] == 2
    assert manifest["dvc"]["git_commit"] == "abc123"
    assert manifest["dvc"]["files"]["train"]["rows"] == 2

    # Must be JSON-serializable for S3 manifest upload
    json.dumps(manifest, ensure_ascii=False)
