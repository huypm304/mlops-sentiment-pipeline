"""Tests for training-run S3 artifact helpers."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "backend"))

from registry.run_artifacts import (
    align_mock_candidate_metrics,
    build_comparison_report,
    metrics_from_train_log_text,
    normalize_pipeline_metrics,
)

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures"


def test_metrics_from_train_log_fixture():
    text = (FIXTURES / "train_log_sample.csv").read_text(encoding="utf-8")
    metrics = metrics_from_train_log_text(text)
    assert metrics["global_f1"] > 0.8
    assert metrics["tas_relaxed_f1"] > 0.7


def test_compare_promotes_when_candidate_beats_baseline():
    baseline = normalize_pipeline_metrics({"global_f1": 0.80, "tas_f1": 0.75})
    candidate = normalize_pipeline_metrics({"global_f1": 0.83, "tas_f1": 0.77})
    report = build_comparison_report(
        baseline_model_id="absa-v2b",
        candidate_model_id="candidate-run-1",
        production_metrics=baseline,
        candidate_metrics=candidate,
    )
    assert report["promote"] is True
    assert report["metric_gate_passed"] is True


def test_compare_rejects_when_candidate_below_baseline():
    baseline = normalize_pipeline_metrics({"tas_relaxed_f1": 0.80})
    candidate = normalize_pipeline_metrics({"tas_relaxed_f1": 0.70})
    report = build_comparison_report(
        baseline_model_id="absa-v2b",
        candidate_model_id="candidate-run-2",
        production_metrics=baseline,
        candidate_metrics=candidate,
    )
    assert report["promote"] is False


def test_compare_uses_global_f1_when_tas_relaxed_missing():
    baseline = normalize_pipeline_metrics({"global_f1": 0.82})
    candidate = normalize_pipeline_metrics({"global_f1": 0.83})
    report = build_comparison_report(
        baseline_model_id="absa-v2b",
        candidate_model_id="candidate-run-3",
        production_metrics=baseline,
        candidate_metrics=candidate,
    )
    assert report["primary_metric"] == "global_f1"
    assert report["promote"] is True


def test_align_mock_candidate_metrics_from_production():
    baseline = normalize_pipeline_metrics({"tas_f1": 0.78, "global_f1": 0.80})
    candidate = normalize_pipeline_metrics({"global_f1": 0})
    aligned = align_mock_candidate_metrics(candidate, baseline)
    assert aligned["tas_relaxed_f1"] == 0.78
