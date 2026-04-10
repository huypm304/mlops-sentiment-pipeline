#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


VALID_ASPECTS = {"Product", "Ship", "Price", "App", "Service"}
VALID_SENTIMENTS = {0, 1, 2}

POSITIVE_OPINION_TARGETS = {
    "thích",
    "xứng_đáng",
    "ổn",
    "ok",
    "tốt",
    "đẹp",
    "mượt",
    "nhanh",
    "ngon",
    "xịn",
}

SUSPECT_TARGETS = {
    "thích",
    "xứng_đáng",
    "ổn",
    "ok",
    "tốt",
    "đẹp",
    "kèm",
    "lỗi",
    "ngon",
    "lâu",
    "cao",
    "mắc",
}

POLAR_GLOBAL_NO_OPINION = {0, 1}


def extract_clause(text: str, start: int, end: int) -> str:
    separators = [0, len(text)]
    for match in re.finditer(r"[\n,.!?;]", text):
        separators.append(match.start())
        separators.append(match.end())
    for match in re.finditer(r"\b(?:nhưng|tuy_nhiên|nhma|nmà|song|trừ|except)\b", text, flags=re.IGNORECASE):
        separators.append(match.start())
        separators.append(match.end())
    left = max(point for point in separators if point <= start)
    right = min(point for point in separators if point >= end)
    return text[left:right].strip().lower()


def extract_window(text: str, start: int, end: int, before: int = 8, after: int = 20) -> str:
    left = max(0, start - before)
    right = min(len(text), end + after)
    return text[left:right].strip().lower()


def validate_row(row: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    text = row.get("text")
    opinions = row.get("opinions")
    global_sentiment = row.get("global_sentiment")

    if not isinstance(text, str) or not isinstance(opinions, list):
        return ["invalid_schema"]
    if global_sentiment not in VALID_SENTIMENTS:
        reasons.append("invalid_global_sentiment")

    seen_aspects: set[str] = set()
    for opinion in opinions:
        if not isinstance(opinion, dict):
            reasons.append("invalid_opinion_schema")
            continue
        target = opinion.get("target")
        aspect = opinion.get("aspect")
        sentiment = opinion.get("sentiment")
        start = opinion.get("start")
        end = opinion.get("end")
        if not isinstance(target, str) or not target:
            reasons.append("invalid_target")
            continue
        if aspect not in VALID_ASPECTS:
            reasons.append("invalid_aspect")
        if sentiment not in VALID_SENTIMENTS:
            reasons.append("invalid_sentiment")
        if not isinstance(start, int) or not isinstance(end, int):
            reasons.append("invalid_offsets")
            continue
        if not (0 <= start <= end <= len(text)):
            reasons.append("offset_out_of_bounds")
            continue
        if text[start:end] != target:
            reasons.append("offset_mismatch")
        if aspect in seen_aspects:
            reasons.append("duplicate_aspect")
        seen_aspects.add(aspect)
    return sorted(set(reasons))


def repair_opinion(text: str, opinion: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    updated = dict(opinion)
    reasons: list[str] = []
    target = str(updated["target"])
    aspect = updated["aspect"]
    sentiment = updated["sentiment"]
    start = updated["start"]
    end = updated["end"]
    clause = extract_clause(text, start, end)
    window = extract_window(text, start, end)
    lower_target = target.lower()

    if lower_target in POSITIVE_OPINION_TARGETS and sentiment == 1:
        if re.search(rf"(?:rất\s+)?không\s+{re.escape(lower_target)}\b", window, flags=re.IGNORECASE):
            updated["sentiment"] = 0
            reasons.append("negated_positive_target")
            return updated, reasons

    if aspect == "Price" and sentiment == 1:
        if lower_target in {"giá", "giá_thành", "giá tiền", "tầm giá", "phí ship", "xứng_đáng"} and re.search(
            r"(?:giá|giá_thành|giá tiền|tầm giá).{0,12}(?:hơi\s+|khá\s+|quá\s+|rất\s+)?(?:đắt|cao|mắc)"
            r"|phí\s*ship.{0,10}cao"
            r"|(?:rất\s+)?không\s+xứng_đáng",
            window,
            flags=re.IGNORECASE,
        ):
            updated["sentiment"] = 0
            reasons.append("price_clause_negative")
            return updated, reasons

    if aspect == "App" and sentiment == 1:
        if lower_target in {"app", "ứng_dụng", "ứng dụng", "phần_mềm", "phần mềm", "cập nhật", "ứng_dụng shopee", "ứng_dụng lazada"} and re.search(
            r"không\s+dùng\s+được|bị\s+lỗi|\blag\b|\bgiật\b|\bđơ\b|\bkhóa\b|không\s+còn",
            window,
            flags=re.IGNORECASE,
        ):
            updated["sentiment"] = 0
            reasons.append("app_clause_negative")
            return updated, reasons

    if aspect == "Ship" and sentiment == 1:
        if lower_target in {"giao", "giao hàng", "shipper", "vận_chuyển", "ship", "gửi"} and re.search(
            r"(?:giao|ship|shipper|vận_chuyển|gửi).{0,12}(?:chậm|lâu|trễ|sai)"
            r"|không\s+giao|giao\s+sai|không\s+gọi|hoàn_trả|hủy\s+đơn",
            window,
            flags=re.IGNORECASE,
        ):
            updated["sentiment"] = 0
            reasons.append("ship_clause_negative")
            return updated, reasons

    return updated, reasons


def collect_review_reasons(row: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    text = row["text"]
    opinions = row["opinions"]
    global_sentiment = row["global_sentiment"]

    if global_sentiment in POLAR_GLOBAL_NO_OPINION and not opinions:
        reasons.append("polar_global_no_opinion")
    if len(text.split()) <= 3:
        reasons.append("very_short_text")

    for opinion in opinions:
        target = str(opinion["target"]).strip().lower()
        aspect = opinion["aspect"]
        sentiment = opinion["sentiment"]
        if target in SUSPECT_TARGETS:
            reasons.append("suspect_target")
        if global_sentiment == 0 and sentiment == 1:
            reasons.append("neg_global_pos_opinion")
        if global_sentiment == 1 and sentiment == 0:
            reasons.append("pos_global_neg_opinion")
        clause = extract_clause(text, opinion["start"], opinion["end"])
        window = extract_window(text, opinion["start"], opinion["end"])
        if target in {"giá", "giá_thành", "giá tiền", "tầm giá", "phí ship", "xứng_đáng"} and aspect == "Price" and sentiment == 1 and re.search(
            r"(?:giá|giá_thành|giá tiền|tầm giá).{0,12}(?:hơi\s+|khá\s+|quá\s+|rất\s+)?(?:đắt|cao|mắc)"
            r"|phí\s*ship.{0,10}cao"
            r"|(?:rất\s+)?không\s+xứng_đáng",
            window,
            flags=re.IGNORECASE,
        ):
            reasons.append("price_contradiction")
        if target in {"app", "ứng_dụng", "ứng dụng", "phần_mềm", "phần mềm", "cập nhật", "ứng_dụng shopee", "ứng_dụng lazada"} and aspect == "App" and sentiment == 1 and re.search(r"không\s+dùng\s+được|bị\s+lỗi|\blag\b|\bgiật\b|\bđơ\b|\bkhóa\b", window, flags=re.IGNORECASE):
            reasons.append("app_contradiction")
        if target in {"giao", "giao hàng", "shipper", "vận_chuyển", "ship", "gửi"} and aspect == "Ship" and sentiment == 1 and re.search(
            r"(?:giao|ship|shipper|vận_chuyển|gửi).{0,12}(?:chậm|lâu|trễ|sai)"
            r"|không\s+giao|giao\s+sai|không\s+gọi|hoàn_trả|hủy\s+đơn",
            window,
            flags=re.IGNORECASE,
        ):
            reasons.append("ship_contradiction")

    return sorted(set(reasons))


def repair_dataset(
    input_path: Path,
    output_path: Path,
    report_path: Path,
    review_path: Path,
) -> dict[str, Any]:
    repaired_lines: list[str] = []
    review_lines: list[str] = []
    fix_counts: Counter[str] = Counter()
    review_counts: Counter[str] = Counter()
    sample_fixes: dict[str, list[dict[str, Any]]] = {}

    total_rows = 0
    repaired_rows = 0
    review_rows = 0

    for line_number, raw_line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw_line.strip():
            continue
        total_rows += 1
        row = json.loads(raw_line)

        validation_reasons = validate_row(row)
        if validation_reasons:
            for reason in validation_reasons:
                review_counts[reason] += 1
            review_rows += 1
            review_lines.append(
                json.dumps(
                    {
                        "line": line_number,
                        "review_reasons": validation_reasons,
                        "row": row,
                    },
                    ensure_ascii=False,
                )
            )
            continue

        updated_row = dict(row)
        updated_opinions: list[dict[str, Any]] = []
        row_fix_reasons: list[str] = []
        for opinion in row["opinions"]:
            updated_opinion, reasons = repair_opinion(row["text"], opinion)
            updated_opinions.append(updated_opinion)
            row_fix_reasons.extend(reasons)
            for reason in reasons:
                fix_counts[reason] += 1
                if len(sample_fixes.setdefault(reason, [])) < 8:
                    sample_fixes[reason].append(
                        {
                            "line": line_number,
                            "text": row["text"][:220],
                            "before": opinion,
                            "after": updated_opinion,
                        }
                    )
        updated_row["opinions"] = updated_opinions
        if row_fix_reasons:
            repaired_rows += 1

        repaired_lines.append(json.dumps(updated_row, ensure_ascii=False))

        review_reasons = collect_review_reasons(updated_row)
        if review_reasons:
            review_rows += 1
            for reason in review_reasons:
                review_counts[reason] += 1
            review_lines.append(
                json.dumps(
                    {
                        "line": line_number,
                        "review_reasons": review_reasons,
                        "row": updated_row,
                    },
                    ensure_ascii=False,
                )
            )

    output_path.write_text("\n".join(repaired_lines) + ("\n" if repaired_lines else ""), encoding="utf-8")
    review_path.write_text("\n".join(review_lines) + ("\n" if review_lines else ""), encoding="utf-8")

    report = {
        "input": str(input_path),
        "output": str(output_path),
        "review_output": str(review_path),
        "total_rows": total_rows,
        "repaired_rows": repaired_rows,
        "review_rows": review_rows,
        "fix_counts": dict(sorted(fix_counts.items())),
        "review_counts": dict(sorted(review_counts.items())),
        "sample_fixes": sample_fixes,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Conservatively repair high-confidence ABSA labeling issues.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/train_data.jsonl"),
        help="Input JSONL dataset.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/train_data.repaired.jsonl"),
        help="Repaired JSONL dataset.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("data/processed/train_data.repaired.report.json"),
        help="Path for the repair report JSON.",
    )
    parser.add_argument(
        "--review-output",
        type=Path,
        default=Path("data/processed/train_data.review_candidates.jsonl"),
        help="Rows that still need manual review.",
    )
    args = parser.parse_args()

    report = repair_dataset(args.input, args.output, args.report, args.review_output)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())