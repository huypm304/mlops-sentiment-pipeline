"""Weekly business insights — aggregation, keywords, and rule-based Vietnamese narratives."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

ASPECT_ORDER = ["Fashion", "Electronics", "General", "Service", "Ship", "Price", "App"]
SENTIMENT_KEYS = ["negative", "positive", "neutral"]

VI_STOPWORDS = frozenset(
    {
        "a",
        "ai",
        "ao",
        "ban",
        "bi",
        "bo",
        "cac",
        "cai",
        "can",
        "cho",
        "co",
        "con",
        "cua",
        "da",
        "de",
        "den",
        "di",
        "do",
        "duoc",
        "gap",
        "gi",
        "hay",
        "hoac",
        "khong",
        "la",
        "lam",
        "ma",
        "mot",
        "nao",
        "neu",
        "nay",
        "nhung",
        "no",
        "nhu",
        "o",
        "qua",
        "rat",
        "roi",
        "se",
        "thi",
        "toi",
        "tren",
        "trong",
        "tu",
        "va",
        "ve",
        "voi",
        "vua",
        "xin",
        "đã",
        "đang",
        "được",
        "để",
        "đó",
        "đã",
        "là",
        "có",
        "của",
        "và",
        "với",
        "cho",
        "không",
        "một",
        "này",
        "nhưng",
        "rất",
        "thì",
        "tôi",
        "trong",
        "được",
        "khi",
        "nên",
        "cũng",
        "mà",
        "về",
        "nữa",
        "thật",
        "sản",
        "phẩm",
        "hàng",
        "shop",
        "mua",
        "dùng",
        "dùng",
        "ok",
        "the",
        "is",
        "it",
        "and",
    }
)

_TOKEN_RE = re.compile(r"[a-zA-Zà-ỹÀ-Ỹ0-9]+", re.UNICODE)


def _normalize_sentiment(label: str) -> str:
    value = str(label or "neutral").strip().lower()
    if value in SENTIMENT_KEYS:
        return value
    if value in ("neg", "negative", "0"):
        return "negative"
    if value in ("pos", "positive", "1"):
        return "positive"
    return "neutral"


def _fold_vi(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def tokenize_vi(text: str) -> list[str]:
    tokens: list[str] = []
    for match in _TOKEN_RE.findall(text or ""):
        folded = _fold_vi(match)
        if len(folded) < 2 or folded in VI_STOPWORDS:
            continue
        tokens.append(folded)
    return tokens


def extract_keywords(
    predictions: list[dict[str, Any]],
    *,
    sentiment: str | None = None,
    top_n: int = 10,
) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for row in predictions:
        row_sentiment = _normalize_sentiment(str(row.get("global_sentiment", "neutral")))
        if sentiment and row_sentiment != sentiment:
            continue
        text = str(row.get("text_preview") or row.get("text") or "")
        counter.update(tokenize_vi(text))

    total = sum(counter.values()) or 1
    return [
        {
            "keyword": word,
            "count": count,
            "share_pct": round(count / total * 100, 1),
        }
        for word, count in counter.most_common(top_n)
    ]


def _dist_from_counter(counter: Counter[str], keys: list[str]) -> dict[str, float]:
    total = sum(counter.get(key, 0) for key in keys) or 1
    return {key: round(counter.get(key, 0) / total, 4) for key in keys}


def aggregate_weekly_stats(
    predictions: list[dict[str, Any]],
    *,
    aspect_order: list[str] | None = None,
) -> dict[str, Any]:
    aspects = aspect_order or ASPECT_ORDER
    sentiment_c: Counter[str] = Counter()
    aspect_c: Counter[str] = Counter()
    aspect_sentiment: dict[str, Counter[str]] = {asp: Counter() for asp in aspects}
    low_conf = 0
    no_opinion = 0

    for row in predictions:
        sentiment = _normalize_sentiment(str(row.get("global_sentiment", "neutral")))
        sentiment_c[sentiment] += 1
        confidence = float(row.get("confidence", 0) or 0)
        if confidence < 0.32:
            low_conf += 1
        row_aspects = [str(a) for a in (row.get("aspects") or []) if str(a) in aspects]
        if not row_aspects:
            no_opinion += 1
        for aspect in row_aspects:
            aspect_c[aspect] += 1
            aspect_sentiment[aspect][sentiment] += 1

    total = len(predictions)
    aspect_sentiment_matrix: dict[str, dict[str, int]] = {}
    aspect_sentiment_rates: dict[str, dict[str, float]] = {}
    for aspect in aspects:
        counts = {key: int(aspect_sentiment[aspect].get(key, 0)) for key in SENTIMENT_KEYS}
        aspect_total = sum(counts.values()) or 1
        aspect_sentiment_matrix[aspect] = counts
        aspect_sentiment_rates[aspect] = {
            key: round(counts[key] / aspect_total, 4) for key in SENTIMENT_KEYS
        }

    return {
        "total_reviews": total,
        "sentiment_mix": _dist_from_counter(sentiment_c, SENTIMENT_KEYS),
        "sentiment_counts": {key: int(sentiment_c.get(key, 0)) for key in SENTIMENT_KEYS},
        "aspect_share": _dist_from_counter(aspect_c, aspects),
        "aspect_counts": {asp: int(aspect_c.get(asp, 0)) for asp in aspects},
        "aspect_sentiment": aspect_sentiment_matrix,
        "aspect_sentiment_rates": aspect_sentiment_rates,
        "low_confidence_rate": round(low_conf / total, 4) if total else 0.0,
        "no_opinion_rate": round(no_opinion / total, 4) if total else 0.0,
        "top_keywords": {
            "overall": extract_keywords(predictions, top_n=10),
            "negative": extract_keywords(predictions, sentiment="negative", top_n=8),
            "positive": extract_keywords(predictions, sentiment="positive", top_n=8),
        },
    }


def _aspect_negative_leader(
    stats: dict[str, Any],
) -> tuple[str, float] | None:
    rates = stats.get("aspect_sentiment_rates") or {}
    best: tuple[str, float] | None = None
    for aspect, row in rates.items():
        neg_rate = float(row.get("negative", 0))
        if int((stats.get("aspect_counts") or {}).get(aspect, 0)) < 2:
            continue
        if best is None or neg_rate > best[1]:
            best = (aspect, neg_rate)
    return best


def _aspect_positive_leader(
    stats: dict[str, Any],
) -> tuple[str, float] | None:
    rates = stats.get("aspect_sentiment_rates") or {}
    best: tuple[str, float] | None = None
    for aspect, row in rates.items():
        pos_rate = float(row.get("positive", 0))
        if int((stats.get("aspect_counts") or {}).get(aspect, 0)) < 2:
            continue
        if best is None or pos_rate > best[1]:
            best = (aspect, pos_rate)
    return best


def build_insights(
    stats: dict[str, Any],
    *,
    previous_stats: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    insights: list[dict[str, str]] = []
    total = int(stats.get("total_reviews", 0))

    if total == 0:
        insights.append(
            {
                "type": "info",
                "message": "Chưa có review nào trong kỳ báo cáo — hãy chạy inference để thu thập dữ liệu.",
            }
        )
        return insights

    mix = stats.get("sentiment_mix") or {}
    neg_pct = round(float(mix.get("negative", 0)) * 100, 1)
    pos_pct = round(float(mix.get("positive", 0)) * 100, 1)
    insights.append(
        {
            "type": "summary",
            "message": (
                f"Tổng {total} review: {pos_pct}% tích cực, {neg_pct}% tiêu cực, "
                f"{round(float(mix.get('neutral', 0)) * 100, 1)}% trung tính."
            ),
        }
    )

    neg_leader = _aspect_negative_leader(stats)
    if neg_leader and neg_leader[1] >= 0.25:
        msg = (
            f"Khía cạnh **{neg_leader[0]}** có tỷ lệ tiêu cực cao nhất tuần "
            f"({round(neg_leader[1] * 100, 1)}%)."
        )
        if previous_stats:
            prev_rates = (previous_stats.get("aspect_sentiment_rates") or {}).get(neg_leader[0], {})
            prev_neg = float(prev_rates.get("negative", 0))
            delta = round((neg_leader[1] - prev_neg) * 100, 1)
            if delta > 5:
                msg += f" Tăng {delta} điểm % so với tuần trước."
            elif delta < -5:
                msg += f" Giảm {abs(delta)} điểm % so với tuần trước."
        insights.append({"type": "warning", "message": msg})

    pos_leader = _aspect_positive_leader(stats)
    if pos_leader and pos_leader[1] >= 0.4:
        insights.append(
            {
                "type": "positive",
                "message": (
                    f"Khía cạnh được khen nhiều nhất: **{pos_leader[0]}** "
                    f"({round(pos_leader[1] * 100, 1)}% tích cực)."
                ),
            }
        )

    neg_kw = stats.get("top_keywords", {}).get("negative") or []
    if neg_kw:
        words = ", ".join(item["keyword"] for item in neg_kw[:5])
        insights.append(
            {
                "type": "keywords",
                "message": f"Top từ khóa tiêu cực: {words}.",
            }
        )

    low_conf = float(stats.get("low_confidence_rate", 0))
    if low_conf >= 0.08:
        insights.append(
            {
                "type": "quality",
                "message": (
                    f"{round(low_conf * 100, 1)}% review độ tin cậy thấp — "
                    "cân nhắc audit dữ liệu hoặc retrain."
                ),
            }
        )

    no_opinion = float(stats.get("no_opinion_rate", 0))
    if no_opinion >= 0.15:
        insights.append(
            {
                "type": "quality",
                "message": (
                    f"{round(no_opinion * 100, 1)}% review không trích xuất được khía cạnh — "
                    "kiểm tra chất lượng văn bản đầu vào."
                ),
            }
        )

    return insights


def render_markdown(report: dict[str, Any]) -> str:
    stats = report.get("stats") or {}
    lines = [
        f"# Báo cáo review tuần — {report.get('name', report.get('report_id', ''))}",
        "",
        f"- **Kỳ:** {report.get('period_start', '')} → {report.get('period_end', '')}",
        f"- **Model:** {report.get('model_id', '')}",
        f"- **Tổng review:** {stats.get('total_reviews', 0)}",
        "",
        "## Nhận định",
        "",
    ]
    for item in report.get("insights") or []:
        lines.append(f"- {item.get('message', '')}")
    lines.extend(["", "## Sentiment mix", ""])
    for key in SENTIMENT_KEYS:
        pct = round(float((stats.get("sentiment_mix") or {}).get(key, 0)) * 100, 1)
        lines.append(f"- {key}: {pct}%")
    lines.extend(["", "## Top keywords (tiêu cực)", ""])
    for item in (stats.get("top_keywords") or {}).get("negative") or []:
        lines.append(f"- {item['keyword']} ({item['count']})")
    return "\n".join(lines) + "\n"


def period_window(*, period_days: int = 7) -> tuple[str, str]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=period_days)
    start_iso = start.isoformat().replace("+00:00", "Z")
    end_iso = end.isoformat().replace("+00:00", "Z")
    return start_iso, end_iso
