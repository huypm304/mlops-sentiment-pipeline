#!/usr/bin/env python3

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


INPUT_FILE = Path("data/processed/train_final_v3.jsonl")
OUTPUT_FILE = Path("data/processed/train_final_v3.cleaned.jsonl")
REVIEW_FILE = Path("data/processed/train_final_v3.review.jsonl")
REPORT_FILE = Path("data/processed/train_final_v3.clean_report.json")
MIN_TOKENS = 3
WINDOW = 5

VALID_ASPECTS = {"Product", "Service", "Ship", "Price", "App"}
VALID_SENTIMENTS = {0, 1, 2}

OPINION_WORDS = {
    "tệ", "xấu", "kém", "chậm", "đắt", "tồi", "dở", "lỗi", "mỏng", "rộng", "nhỏ",
    "to", "bẩn", "hôi", "nhạt", "cứng", "nặng", "sai", "thiếu", "trễ", "lâu",
    "đẹp", "tốt", "nhanh", "rẻ", "mượt", "mịn", "chắc", "chuẩn", "ổn", "xinh",
    "ngon", "hay", "tuyệt", "ok", "oke", "bình_thường", "tạm", "được", "thôi",
}

NEG_KEYWORDS = [
    "không", "tệ", "xấu", "kém", "chậm", "đắt", "tồi", "dở", "lỗi", "mỏng",
    "thiếu", "sai", "trễ", "lâu", "hỏng", "rách", "bẩn", "hôi", "tệ_hại",
    "không giống", "không đúng", "không đẹp", "thất_vọng", "thất vọng", "bực",
    "phiền", "ghét", "chán", "tụt", "yếu", "lag", "đơ", "giật",
]

POS_KEYWORDS = [
    "đẹp", "tốt", "nhanh", "rẻ", "mượt", "tuyệt", "xinh", "ngon", "chất",
    "ưng", "thích", "hài_lòng", "hài lòng", "xuất_sắc", "xuất sắc", "hoàn_hảo",
    "hoàn hảo", "chuẩn", "nhiệt_tình", "nhiệt tình",
]

NEU_KEYWORDS = [
    "bình_thường", "bình thường", "tạm_được", "tạm được", "cũng_được", "cũng được",
    "ổn", "tạm_ổn", "tạm ổn", "bình thường thôi", "khắc_phục_được", "khắc phục được",
    "cũng ok",
]


def count_tokens(text: str) -> int:
    return len(re.findall(r"\S+", text))


def normalize_target(text: str, opinion: dict) -> tuple[dict | None, str | None]:
    target = opinion.get("target", "")
    start = opinion.get("start", -1)
    end = opinion.get("end", -1)
    if not isinstance(target, str) or not isinstance(start, int) or not isinstance(end, int):
        return None, "invalid_schema"
    if start < 0 or end <= start or end > len(text):
        return None, "invalid_offset"

    trimmed = target.strip()
    left_trim = len(target) - len(target.lstrip())
    right_trim = len(target) - len(target.rstrip())
    new_start = start + left_trim
    new_end = end - right_trim

    if not trimmed or new_start < 0 or new_end <= new_start or new_end > len(text):
        return None, "invalid_trimmed_target"
    if text[new_start:new_end] != trimmed:
        return None, "offset_mismatch_after_trim"

    updated = dict(opinion)
    updated["target"] = trimmed
    updated["start"] = new_start
    updated["end"] = new_end
    return updated, None


def context_window(text: str, char_s: int, char_e: int, radius: int = WINDOW) -> str:
    spans = [m.span() for m in re.finditer(r"\S+", text)]
    token_ids = []
    for i, (tok_s, tok_e) in enumerate(spans):
        if max(tok_s, char_s) < min(tok_e, char_e):
            token_ids.append(i)
    if not token_ids:
        return text.lower()

    lo = max(0, token_ids[0] - radius)
    hi = min(len(spans) - 1, token_ids[-1] + radius)
    return " ".join(text[s:e].lower() for s, e in spans[lo:hi + 1])


def classify_sentiment_conflict(text: str, opinion: dict) -> tuple[bool, str | None, str]:
    ctx = context_window(text, opinion["start"], opinion["end"])
    sentiment = opinion.get("sentiment")
    has_neg = any(keyword in ctx for keyword in NEG_KEYWORDS)
    has_pos = any(keyword in ctx for keyword in POS_KEYWORDS)
    has_neu = any(keyword in ctx for keyword in NEU_KEYWORDS)

    if sentiment == 1 and has_neg and not has_pos:
        return True, "negative_context", ctx
    if sentiment == 0 and has_pos and not has_neg:
        return True, "positive_context", ctx
    if sentiment == 1 and has_neu and not has_pos and not has_neg:
        return True, "neutral_context", ctx
    return False, None, ctx


def main() -> int:
    stats = Counter()
    cleaned_records = []
    review_records = []

    with INPUT_FILE.open(encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, 1):
            raw_line = raw_line.strip()
            if not raw_line:
                continue

            stats["input_records"] += 1
            record = json.loads(raw_line)
            text = record.get("text", "")
            opinions = record.get("opinions", [])

            if not isinstance(text, str) or not isinstance(opinions, list):
                stats["invalid_records"] += 1
                review_records.append({
                    "line_no": line_no,
                    "review_reasons": ["invalid_record_schema"],
                    "row": record,
                })
                continue

            if count_tokens(text) < MIN_TOKENS:
                stats["dropped_short_records"] += 1
                review_records.append({
                    "line_no": line_no,
                    "review_reasons": ["short_text"],
                    "row": record,
                })
                continue

            updated_record = dict(record)
            kept_opinions = []
            review_reasons = []

            for opinion in opinions:
                stats["input_opinions"] += 1

                aspect = opinion.get("aspect")
                sentiment = opinion.get("sentiment")
                if aspect not in VALID_ASPECTS or sentiment not in VALID_SENTIMENTS:
                    stats["dropped_invalid_labels"] += 1
                    review_reasons.append("invalid_aspect_or_sentiment")
                    continue

                normalized, error = normalize_target(text, opinion)
                if error:
                    stats[f"drop_{error}"] += 1
                    review_reasons.append(error)
                    continue
                if normalized["target"] != opinion.get("target"):
                    stats["fixed_dirty_targets"] += 1

                lowered = normalized["target"].lower()
                if lowered in OPINION_WORDS:
                    stats["dropped_opinion_word_targets"] += 1
                    review_reasons.append("opinion_word_target")
                    continue

                has_conflict, conflict_type, ctx = classify_sentiment_conflict(text, normalized)
                if has_conflict:
                    stats["flagged_sentiment_conflicts"] += 1
                    review_reasons.append(conflict_type or "sentiment_conflict")
                    review_records.append({
                        "line_no": line_no,
                        "review_reasons": [conflict_type or "sentiment_conflict"],
                        "context": ctx,
                        "opinion": normalized,
                        "text": text,
                    })
                    continue

                kept_opinions.append(normalized)

            if not kept_opinions:
                stats["dropped_empty_records"] += 1
                if not review_reasons:
                    review_reasons.append("empty_after_cleaning")
                review_records.append({
                    "line_no": line_no,
                    "review_reasons": sorted(set(review_reasons)),
                    "row": record,
                })
                continue

            updated_record["opinions"] = kept_opinions
            cleaned_records.append(updated_record)
            stats["output_records"] += 1
            stats["output_opinions"] += len(kept_opinions)

    OUTPUT_FILE.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in cleaned_records),
        encoding="utf-8",
    )
    REVIEW_FILE.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in review_records),
        encoding="utf-8",
    )
    REPORT_FILE.write_text(json.dumps(dict(sorted(stats.items())), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(dict(sorted(stats.items())), ensure_ascii=False, indent=2))
    print(f"cleaned -> {OUTPUT_FILE}")
    print(f"review  -> {REVIEW_FILE}")
    print(f"report  -> {REPORT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())