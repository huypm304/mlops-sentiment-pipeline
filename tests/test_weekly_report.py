"""Tests for weekly business insights report aggregation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "backend" / "lambda" / "metrics"))

from insights import (  # noqa: E402
    aggregate_weekly_stats,
    build_insights,
    extract_keywords,
    render_markdown,
    tokenize_vi,
)


def _sample_predictions() -> list[dict]:
    return [
        {
            "text_preview": "giao hàng trễ quá, ship chậm",
            "global_sentiment": "negative",
            "confidence": 0.85,
            "aspects": ["Ship"],
        },
        {
            "text_preview": "giá rẻ, chất lượng tốt",
            "global_sentiment": "positive",
            "confidence": 0.9,
            "aspects": ["Price", "General"],
        },
        {
            "text_preview": "dịch vụ ok",
            "global_sentiment": "neutral",
            "confidence": 0.2,
            "aspects": [],
        },
    ]


def test_tokenize_vi_filters_stopwords():
    tokens = tokenize_vi("Giá rẻ và chất lượng tốt")
    assert "gia" in tokens or "re" in tokens
    assert "va" not in tokens


def test_extract_keywords_negative_only():
    keywords = extract_keywords(_sample_predictions(), sentiment="negative", top_n=5)
    assert keywords
    assert all(isinstance(item["keyword"], str) for item in keywords)


def test_aggregate_weekly_stats_schema():
    stats = aggregate_weekly_stats(_sample_predictions())
    assert stats["total_reviews"] == 3
    assert stats["sentiment_counts"]["negative"] == 1
    assert stats["aspect_counts"]["Ship"] == 1
    assert stats["aspect_sentiment"]["Ship"]["negative"] == 1
    assert stats["low_confidence_rate"] > 0
    json.dumps(stats)


def test_build_insights_vietnamese_messages():
    stats = aggregate_weekly_stats(_sample_predictions())
    insights = build_insights(stats)
    assert insights
    assert any("review" in item["message"].lower() for item in insights)


def test_build_insights_week_over_week_delta():
    current = aggregate_weekly_stats(_sample_predictions())
    previous = aggregate_weekly_stats(
        [
            {
                "text_preview": "ship ổn",
                "global_sentiment": "positive",
                "confidence": 0.9,
                "aspects": ["Ship"],
            }
        ]
    )
    insights = build_insights(current, previous_stats=previous)
    assert any(item["type"] in {"warning", "positive", "summary"} for item in insights)


def test_render_markdown_contains_sections():
    stats = aggregate_weekly_stats(_sample_predictions())
    report = {
        "report_id": "weekly-test",
        "name": "Báo cáo test",
        "model_id": "absa-v2b",
        "period_start": "2026-06-22T00:00:00Z",
        "period_end": "2026-06-29T00:00:00Z",
        "stats": stats,
        "insights": build_insights(stats),
    }
    md = render_markdown(report)
    assert "# Báo cáo review tuần" in md
    assert "## Nhận định" in md
