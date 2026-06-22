"""
Build benchmark_summary.json from individual audit module outputs.

Portable — no dependency on training code or src/absa.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def compute_dataset_summary(train_path: Path) -> dict:
    rows = 0
    opinions = 0
    mams_rows = 0
    neu_ops = 0
    glob_neu = 0

    with open(train_path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rows += 1
            obj = json.loads(line)
            ops = obj.get("opinions", [])
            opinions += len(ops)
            sents = {op.get("sentiment") for op in ops if op.get("sentiment") in (0, 1, 2)}
            if len(sents) >= 2:
                mams_rows += 1
            neu_ops += sum(1 for op in ops if op.get("sentiment") == 2)
            if obj.get("global_sentiment") == 2:
                glob_neu += 1

    def pct(n, d):
        return round(n * 100.0 / d, 4) if d else 0.0

    return {
        "train_file": str(train_path),
        "train_rows": rows,
        "train_opinions": opinions,
        "avg_opinions_per_sentence": round(opinions / max(rows, 1), 4),
        "mams_pct": pct(mams_rows, rows),
        "neu_opinion_pct": pct(neu_ops, opinions),
        "global_neu_pct": pct(glob_neu, rows),
    }


def summarize_schema(data: dict) -> dict:
    combined = data.get("combined", {})
    crit_pct = combined.get("critical_schema_error_pct", 100.0)
    train_ok = data.get("train", {}).get("thresholds", {}).get("critical_schema_pass", False)
    dev_ok = data.get("dev", {}).get("thresholds", {}).get("critical_schema_pass", False)
    status = "pass" if crit_pct == 0.0 and train_ok and dev_ok else ("fail" if crit_pct > 0.5 else "warn")
    return {
        "critical_error_pct_combined": crit_pct,
        "train_all_100pct": train_ok,
        "dev_all_100pct": dev_ok,
        "status": status,
    }


def summarize_span(data: dict) -> dict:
    train = data.get("train", {}).get("metrics", {})
    th = data.get("train", {}).get("thresholds", {})
    all_pass = all(
        th.get(k, False)
        for k in (
            "pass_exact_offset", "pass_trimmed_offset", "pass_empty_span",
            "pass_out_of_bound", "pass_span_too_wide", "pass_duplicate_exact_opinion",
        )
    )
    return {
        "train_exact_pct": train.get("exact_offset_match_pct", 0.0),
        "train_trimmed_pct": train.get("trimmed_offset_match_pct", 0.0),
        "train_empty_pct": train.get("empty_span_pct", 0.0),
        "train_oob_pct": train.get("out_of_bound_pct", 0.0),
        "train_duplicate_exact_pct": train.get("duplicate_exact_opinion_pct", 0.0),
        "train_duplicate_same_aspect_rows_pct": train.get("duplicate_same_aspect_rows_pct", 0.0),
        "status": "pass" if all_pass else "warn",
    }


def summarize_label(data: dict) -> dict:
    train_m = data.get("train", {}).get("metrics", {})
    train_t = data.get("train", {}).get("thresholds", {})
    aspect_band = train_t.get("aspect_quality_band", "unknown")
    sent_band = train_t.get("sentiment_quality_band", "unknown")
    status = "pass"
    if aspect_band in ("review", "high-risk") or sent_band in ("review", "high-risk"):
        status = "warn"
    return {
        "aspect_suspicious_pct": train_m.get("aspect_suspicious_rate_pct", 0.0),
        "sentiment_suspicious_pct": train_m.get("sentiment_suspicious_rate_pct", 0.0),
        "general_overuse_pct": train_m.get("general_overuse_rate_pct", 0.0),
        "service_ship_confusion_pct": train_m.get("service_ship_confusion_rate_pct", 0.0),
        "aspect_band": aspect_band,
        "sentiment_band": sent_band,
        "status": status,
    }


def summarize_distribution(data: dict) -> dict:
    th = data.get("comparison", {}).get("thresholds", {})
    all_ok = all(th.values()) if th else False
    return {
        "train_per_aspect_ge_300": th.get("train_per_aspect_ge_300", False),
        "dev_per_aspect_ge_50": th.get("dev_per_aspect_ge_50", False),
        "cell_train_ge_30": th.get("cell_train_ge_30", False),
        "cell_train_ge_50": th.get("cell_train_ge_50", False),
        "cell_train_ge_100": th.get("cell_train_ge_100", False),
        "status": "pass" if all_ok else "warn",
    }


def summarize_global(data: dict) -> dict:
    train_pct = data.get("train", {}).get("global_rule_consistency_pct", 0.0)
    dev_pct = data.get("dev", {}).get("global_rule_consistency_pct", 0.0)
    status = "pass"
    if train_pct < 90.0 or dev_pct < 90.0:
        status = "fail"
    elif train_pct < 95.0 or dev_pct < 95.0:
        status = "warn"
    return {
        "train_consistency_pct": train_pct,
        "dev_consistency_pct": dev_pct,
        "status": status,
    }


def summarize_leakage(data: dict) -> dict:
    metrics = data.get("metrics", {})
    th = data.get("thresholds", {})
    exact_pct = metrics.get("exact_duplicate_train_dev_ratio_over_dev_pct", 0.0)
    near_pct = metrics.get("near_duplicate_dev_rows_ratio_pct", 0.0)
    same_diff = metrics.get("same_text_different_labels_count", 0)
    status = "pass"
    if not th.get("pass_exact_leakage", True) or same_diff > 0:
        status = "fail"
    elif not th.get("pass_near_duplicate", True) or th.get("warn_exact_leakage", False):
        status = "warn"
    return {
        "exact_leakage_pct": exact_pct,
        "near_duplicate_pct": near_pct,
        "same_text_diff_label_pairs": same_diff,
        "status": status,
    }


def overall_status(modules: dict[str, dict], fail_on: list[str]) -> str:
    if any(modules.get(k, {}).get("status") == "fail" for k in fail_on):
        return "fail"
    statuses = [v["status"] for v in modules.values()]
    if "warn" in statuses or "fail" in statuses:
        return "pass-with-warnings"
    return "pass"


def build_benchmark_summary(
    reports_dir: Path,
    train_path: Path,
    *,
    thresholds_path: Path | None = None,
) -> dict:
    reports_dir = Path(reports_dir)
    thresholds = {}
    if thresholds_path and thresholds_path.exists():
        thresholds = _load(thresholds_path)
    fail_on = thresholds.get("overall", {}).get(
        "fail_on_modules",
        ["schema_audit", "leakage_audit", "span_offset_audit"],
    )

    schema_data = _load(reports_dir / "schema_audit.json")
    span_data = _load(reports_dir / "span_offset_audit.json")
    label_data = _load(reports_dir / "label_consistency_audit.json")
    dist_data = _load(reports_dir / "distribution_audit.json")
    global_data = _load(reports_dir / "global_sentiment_audit.json")
    leak_data = _load(reports_dir / "leakage_audit.json")

    modules = {
        "schema_audit": summarize_schema(schema_data),
        "span_offset_audit": summarize_span(span_data),
        "label_consistency_audit": summarize_label(label_data),
        "distribution_audit": summarize_distribution(dist_data),
        "global_sentiment_audit": summarize_global(global_data),
        "leakage_audit": summarize_leakage(leak_data),
    }

    summary = {
        "dataset_summary": compute_dataset_summary(train_path),
        **modules,
        "overall": {
            "data_level_status": overall_status(modules, fail_on),
            "module_statuses": {k: v["status"] for k, v in modules.items()},
        },
    }
    return summary


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Build benchmark_summary.json from audit reports")
    p.add_argument("--reports-dir", type=Path, required=True)
    p.add_argument("--train", type=Path, required=True)
    p.add_argument("--thresholds", type=Path, default=None)
    p.add_argument("--output", type=Path, default=None)
    args = p.parse_args()

    out = args.output or (args.reports_dir / "benchmark_summary.json")
    summary = build_benchmark_summary(
        args.reports_dir,
        args.train,
        thresholds_path=args.thresholds,
    )
    with open(out, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"Wrote {out} — status: {summary['overall']['data_level_status']}")
