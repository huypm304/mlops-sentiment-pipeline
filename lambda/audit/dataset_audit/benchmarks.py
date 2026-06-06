"""Quality benchmarks vs thesis thresholds."""

from __future__ import annotations

from typing import Any

from .constants import BENCHMARK_THRESHOLDS


def _status(value: float, threshold: float, *, higher_is_better: bool = True) -> str:
    if higher_is_better:
        return "pass" if value >= threshold else "fail"
    return "pass" if value <= threshold else "fail"


def build_benchmarks(
    stats: dict[str, int],
    total_lines: int,
    parse_errors: int,
) -> list[dict[str, Any]]:
    parsed = stats["total_records"]
    opinions = max(stats["total_opinions"], 1)
    spans = max(stats["span_checked"], 1)

    record_parse_rate = parsed / total_lines if total_lines else 0.0
    span_offset_accuracy = 1.0 - (stats["span_mismatch"] / spans)
    aspect_schema_rate = 1.0 - (stats["invalid_aspect"] / opinions)
    sentiment_schema_rate = 1.0 - (stats["invalid_sentiment"] / opinions)
    duplicate_opinion_rate = stats["duplicate_opinions"] / opinions
    empty_target_rate = stats["empty_targets"] / opinions
    global_checks = max(parsed - stats["global_inconsistent"], 1)
    global_consistency_rate = 1.0 - (stats["global_inconsistent"] / global_checks)

    rows = [
        {
            "id": "record_parse_rate",
            "name": "JSONL parse success",
            "description": "Share of non-empty lines that parse as valid JSON objects",
            "value": round(record_parse_rate, 4),
            "threshold": BENCHMARK_THRESHOLDS["record_parse_rate"],
            "unit": "ratio",
            "higher_is_better": True,
        },
        {
            "id": "span_offset_accuracy",
            "name": "Span offset accuracy (VLSP)",
            "description": "Opinion targets align with text[start:end]",
            "value": round(span_offset_accuracy, 4),
            "threshold": BENCHMARK_THRESHOLDS["span_offset_accuracy"],
            "unit": "ratio",
            "higher_is_better": True,
        },
        {
            "id": "aspect_schema_rate",
            "name": "Aspect schema compliance",
            "description": "Opinions use allowed aspect labels (Fashion, Price, …)",
            "value": round(aspect_schema_rate, 4),
            "threshold": BENCHMARK_THRESHOLDS["aspect_schema_rate"],
            "unit": "ratio",
            "higher_is_better": True,
        },
        {
            "id": "sentiment_schema_rate",
            "name": "Sentiment schema compliance",
            "description": "Polarity encoded as 0/1/2 (neg/pos/neutral)",
            "value": round(sentiment_schema_rate, 4),
            "threshold": BENCHMARK_THRESHOLDS["sentiment_schema_rate"],
            "unit": "ratio",
            "higher_is_better": True,
        },
        {
            "id": "duplicate_opinion_rate",
            "name": "Duplicate opinion rate",
            "description": "Repeated (target, aspect) within the same sentence",
            "value": round(duplicate_opinion_rate, 4),
            "threshold": BENCHMARK_THRESHOLDS["duplicate_opinion_rate_max"],
            "unit": "ratio",
            "higher_is_better": False,
        },
        {
            "id": "empty_target_rate",
            "name": "Empty target rate",
            "description": "Opinions with missing or blank targets",
            "value": round(empty_target_rate, 4),
            "threshold": BENCHMARK_THRESHOLDS["empty_target_rate_max"],
            "unit": "ratio",
            "higher_is_better": False,
        },
        {
            "id": "global_consistency_rate",
            "name": "Global sentiment consistency",
            "description": "global_sentiment matches majority opinion polarity",
            "value": round(global_consistency_rate, 4),
            "threshold": BENCHMARK_THRESHOLDS["global_consistency_rate"],
            "unit": "ratio",
            "higher_is_better": True,
        },
    ]

    for row in rows:
        row["status"] = _status(
            row["value"],
            row["threshold"],
            higher_is_better=row["higher_is_better"],
        )
        row["display_value"] = (
            f"{row['value'] * 100:.2f}%"
            if row["unit"] == "ratio"
            else str(row["value"])
        )
        row["display_threshold"] = (
            f"≥ {row['threshold'] * 100:.0f}%"
            if row["higher_is_better"]
            else f"≤ {row['threshold'] * 100:.1f}%"
        )

    if parse_errors:
        rows.insert(
            0,
            {
                "id": "parse_errors",
                "name": "Parse errors",
                "description": "Malformed JSON lines",
                "value": parse_errors,
                "threshold": 0,
                "unit": "count",
                "higher_is_better": False,
                "status": "fail",
                "display_value": str(parse_errors),
                "display_threshold": "0",
            },
        )

    return rows
