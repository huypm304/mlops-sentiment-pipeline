"""Per-record validators for Vietnamese ABSA JSONL."""

from __future__ import annotations

from typing import Any

from .constants import SENTIMENT_LABELS, VALID_ASPECTS, VALID_SENTIMENTS


def _normalize_span_text(text: str, start: int, end: int) -> str:
    return text[start:end].strip().lower().replace(" ", "_")


def validate_record(record: Any, line_no: int) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    metrics = {
        "opinion_count": 0,
        "span_checked": 0,
        "span_mismatch": 0,
        "duplicate_opinions": 0,
        "empty_targets": 0,
        "invalid_aspect": 0,
        "invalid_sentiment": 0,
        "global_inconsistent": 0,
        "overlapping_spans": 0,
    }

    if not isinstance(record, dict):
        issues.append(
            {
                "line": line_no,
                "code": "RECORD_TYPE",
                "severity": "error",
                "message": "Each line must be a JSON object",
            }
        )
        return {"line": line_no, "passed": False, "issues": issues, "metrics": metrics}

    text = record.get("text")
    if not isinstance(text, str) or not text.strip():
        issues.append(
            {
                "line": line_no,
                "code": "EMPTY_TEXT",
                "severity": "error",
                "message": "Field 'text' must be a non-empty string",
            }
        )
        text = text if isinstance(text, str) else ""

    opinions = record.get("opinions")
    if opinions is None:
        opinions = []
    if not isinstance(opinions, list):
        issues.append(
            {
                "line": line_no,
                "code": "OPINIONS_TYPE",
                "severity": "error",
                "message": "Field 'opinions' must be a list",
            }
        )
        opinions = []

    global_sentiment = record.get("global_sentiment")
    if global_sentiment not in VALID_SENTIMENTS:
        issues.append(
            {
                "line": line_no,
                "code": "GLOBAL_SENTIMENT",
                "severity": "error",
                "message": "global_sentiment must be 0 (neg), 1 (pos), or 2 (neutral)",
            }
        )

    seen_keys: set[tuple[str, str]] = set()
    spans: list[tuple[int, int]] = []
    sentiment_votes: list[int] = []

    for idx, op in enumerate(opinions):
        if not isinstance(op, dict):
            issues.append(
                {
                    "line": line_no,
                    "code": "OPINION_TYPE",
                    "severity": "error",
                    "message": f"opinions[{idx}] must be an object",
                }
            )
            continue

        metrics["opinion_count"] += 1
        target = op.get("target", "")
        aspect = op.get("aspect")
        sentiment = op.get("sentiment")
        start, end = op.get("start"), op.get("end")

        if not isinstance(target, str) or not target.strip():
            metrics["empty_targets"] += 1
            issues.append(
                {
                    "line": line_no,
                    "code": "EMPTY_TARGET",
                    "severity": "error",
                    "message": f"opinions[{idx}].target is empty",
                }
            )

        if aspect not in VALID_ASPECTS:
            metrics["invalid_aspect"] += 1
            issues.append(
                {
                    "line": line_no,
                    "code": "INVALID_ASPECT",
                    "severity": "error",
                    "message": f"opinions[{idx}].aspect '{aspect}' not in VLSP schema",
                }
            )

        if sentiment not in VALID_SENTIMENTS:
            metrics["invalid_sentiment"] += 1
            issues.append(
                {
                    "line": line_no,
                    "code": "INVALID_SENTIMENT",
                    "severity": "error",
                    "message": f"opinions[{idx}].sentiment must be 0, 1, or 2",
                }
            )
        else:
            sentiment_votes.append(int(sentiment))

        dup_key = (str(target).strip().lower(), str(aspect))
        if dup_key in seen_keys:
            metrics["duplicate_opinions"] += 1
            issues.append(
                {
                    "line": line_no,
                    "code": "DUPLICATE_OPINION",
                    "severity": "warning",
                    "message": f"Duplicate target+aspect: {target} / {aspect}",
                }
            )
        seen_keys.add(dup_key)

        if not isinstance(start, int) or not isinstance(end, int):
            issues.append(
                {
                    "line": line_no,
                    "code": "SPAN_TYPE",
                    "severity": "error",
                    "message": f"opinions[{idx}] start/end must be integers",
                }
            )
            continue

        metrics["span_checked"] += 1
        if start < 0 or end > len(text) or start >= end:
            metrics["span_mismatch"] += 1
            issues.append(
                {
                    "line": line_no,
                    "code": "SPAN_BOUNDS",
                    "severity": "error",
                    "message": f"Invalid span [{start}:{end}] for text length {len(text)}",
                }
            )
            continue

        spans.append((start, end))
        slice_norm = _normalize_span_text(text, start, end)
        target_norm = str(target).strip().lower().replace(" ", "_")
        if slice_norm != target_norm:
            metrics["span_mismatch"] += 1
            issues.append(
                {
                    "line": line_no,
                    "code": "SPAN_OFFSET",
                    "severity": "error",
                    "message": (
                        f"text[{start}:{end}]='{text[start:end]}' "
                        f"does not match target '{target}'"
                    ),
                }
            )

    for i, (a0, a1) in enumerate(spans):
        for b0, b1 in spans[i + 1 :]:
            if not (a1 <= b0 or b1 <= a0):
                metrics["overlapping_spans"] += 1
                issues.append(
                    {
                        "line": line_no,
                        "code": "OVERLAPPING_SPAN",
                        "severity": "warning",
                        "message": f"Overlapping opinion spans [{a0}:{a1}] and [{b0}:{b1}]",
                    }
                )
                break

    if sentiment_votes and global_sentiment in VALID_SENTIMENTS:
        majority = max(set(sentiment_votes), key=sentiment_votes.count)
        if int(global_sentiment) != majority:
            metrics["global_inconsistent"] += 1
            issues.append(
                {
                    "line": line_no,
                    "code": "GLOBAL_INCONSISTENT",
                    "severity": "warning",
                    "message": (
                        f"global_sentiment={global_sentiment} "
                        f"differs from majority opinion sentiment={majority}"
                    ),
                }
            )

    has_errors = any(i["severity"] == "error" for i in issues)
    return {
        "line": line_no,
        "passed": not has_errors,
        "issues": issues,
        "metrics": metrics,
    }
