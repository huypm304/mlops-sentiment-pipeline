"""Tests for Step Functions stage progress helpers."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "backend" / "lambda" / "pipeline"))
sys.path.insert(0, str(ROOT / "apps" / "backend"))

from sfn_progress import build_sfn_steps, cancel_training_run, initial_sfn_steps  # noqa: E402


def test_initial_sfn_steps_starts_at_train():
    steps = initial_sfn_steps()
    assert steps[0]["name"] == "Train"
    assert steps[0]["status"] == "running"
    assert steps[1]["status"] == "pending"


def test_build_sfn_steps_marks_completed_before_current():
    steps = build_sfn_steps(
        completed_states={"StartTraining"},
        current_state="EvaluateCandidate",
        sfn_status="RUNNING",
    )
    assert steps[0]["status"] == "completed"
    assert steps[1]["status"] == "running"
    assert steps[2]["status"] == "pending"


def test_cancel_marks_stale_run_without_arn(monkeypatch):
    updates: list[dict] = []

    def fake_update(run_id, created_at, payload):
        updates.append({"run_id": run_id, "created_at": created_at, **payload})

    monkeypatch.setattr("sfn_progress.update_training_run", fake_update)
    monkeypatch.setattr("sfn_progress._resolve_execution_arn", lambda _row: "")

    result = cancel_training_run(
        {"run_id": "run-stale", "created_at": "2026-01-01T00:00:00Z", "status": "TRAINING"},
        cancelled_by="test",
    )
    assert result["status"] == "CANCELLED"
    assert updates and updates[0]["status"] == "CANCELLED"


def test_build_sfn_steps_all_completed_on_success():
    steps = build_sfn_steps(
        completed_states=set(),
        current_state=None,
        sfn_status="SUCCEEDED",
    )
    assert all(step["status"] == "completed" for step in steps)
