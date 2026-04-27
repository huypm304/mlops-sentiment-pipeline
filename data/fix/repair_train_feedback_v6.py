#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from copy import deepcopy
from pathlib import Path


DEFAULT_INPUT = Path("data/processed/data_train_v6_final.jsonl")
DEFAULT_OUTPUT = Path("data/processed/data_train_v6_final.train_feedback_fixed.jsonl")
DEFAULT_REVIEW = Path("data/processed/data_train_v6_final.train_feedback_review.jsonl")
DEFAULT_REPORT = Path("data/processed/data_train_v6_final.train_feedback_report.json")

SHIP_TARGETS = {
    "ship",
    "shipper",
    "giao hàng",
    "giao_hàng",
    "vận chuyển",
    "vận_chuyển",
    "đơn hàng",
    "đơn_hàng",
    "phí ship",
    "phí_ship",
    "thời gian giao",
    "thời_gian_giao",
}

GENERAL_AMBIGUOUS_TARGETS = {
    "hàng",
    "sản phẩm",
    "sản_phẩm",
    "shop",
    "đơn",
    "gói hàng",
    "gói_hàng",
}

SHIP_REVIEW_TARGETS = {
    "giao",
    "gửi",
    "hàng",
    "đơn",
    "shop",
}

SHIP_LEXEMES = {
    "ship",
    "shipper",
    "giao",
    "vận",
    "chuyển",
    "đơn",
    "gửi",
    "phí",
}

SHIP_CONTEXT_PATTERNS = [
    r"(?:giao|ship|shipper|vận\s*chuyển).{0,18}(?:nhanh|chậm|lâu|trễ|đúng\s*hẹn|sai|thiếu|hoàn|hủy)",
    r"(?:phí\s*ship|phí_ship).{0,12}(?:cao|đắt|rẻ|ổn|ok|hợp\s*lý)",
    r"(?:đơn\s*hàng|đơn_hàng).{0,18}(?:giao|đến|nhận|trễ|hủy|hoàn)",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Targeted data repair from v6 training feedback")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            raw_line = raw_line.strip()
            if raw_line:
                records.append(json.loads(raw_line))
    return records


def write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def normalize(text: str) -> str:
    lowered = text.lower().strip()
    return re.sub(r"\s+", " ", lowered)


def local_window(text: str, start: int, end: int, radius: int = 5) -> str:
    spans = [match.span() for match in re.finditer(r"\S+", text)]
    token_ids = []
    for idx, (tok_start, tok_end) in enumerate(spans):
        if max(tok_start, start) < min(tok_end, end):
            token_ids.append(idx)
    if not token_ids:
        return text.lower()
    low = max(0, token_ids[0] - radius)
    high = min(len(spans) - 1, token_ids[-1] + radius)
    return " ".join(text[start_idx:end_idx].lower() for start_idx, end_idx in spans[low : high + 1])


def has_ship_signal(opinion: dict, text: str) -> bool:
    target = normalize(opinion.get("target", ""))
    if target in SHIP_TARGETS:
        return True
    window = local_window(text, opinion.get("start", 0), opinion.get("end", 0), radius=6)
    return any(re.search(pattern, window, flags=re.IGNORECASE) for pattern in SHIP_CONTEXT_PATTERNS)


def has_ship_lexeme(target: str) -> bool:
    normalized = normalize(target).replace("_", " ")
    tokens = {token for token in normalized.split() if token}
    return bool(tokens & SHIP_LEXEMES)


def needs_ship_general_review(opinion: dict, text: str) -> bool:
    target = normalize(opinion.get("target", ""))
    if opinion.get("aspect") not in {"Ship", "General"}:
        return False

    # Remaining General targets with no ship signal are low-value reviews;
    # keep the queue focused on cases where the model is actually likely confused.
    if opinion.get("aspect") == "General":
        return False

    window = local_window(text, opinion.get("start", 0), opinion.get("end", 0), radius=6)
    ship_hits = sum(bool(re.search(pattern, window, flags=re.IGNORECASE)) for pattern in SHIP_CONTEXT_PATTERNS)
    if target in SHIP_REVIEW_TARGETS:
        return True
    if target in SHIP_TARGETS:
        return False
    return ship_hits == 0 and not has_ship_lexeme(target)


def maybe_fix_global_sentiment(record: dict) -> tuple[int | None, str | None]:
    sentiments = [op.get("sentiment") for op in record.get("opinions", []) if op.get("sentiment") in {0, 1, 2}]
    if not sentiments:
        return None, None
    counts = Counter(sentiments)
    if len(counts) == 1:
        unanimous = sentiments[0]
        if record.get("global_sentiment") != unanimous:
            return unanimous, "global_unanimous_aspect_fix"
    return None, None


def main() -> int:
    args = parse_args()
    if not args.input.exists():
        raise FileNotFoundError(f"Missing input file: {args.input}")

    records = read_jsonl(args.input)
    fixed_records: list[dict] = []
    review_records: list[dict] = []
    stats = Counter()

    for line_no, record in enumerate(records, start=1):
        updated = deepcopy(record)
        changes = []
        review_reasons = []

        for opinion_idx, opinion in enumerate(updated.get("opinions", [])):
            aspect = opinion.get("aspect")
            if aspect == "General" and has_ship_signal(opinion, updated.get("text", "")):
                opinion["aspect"] = "Ship"
                changes.append(
                    {
                        "type": "GeneralToShip",
                        "opinion_idx": opinion_idx,
                        "target": opinion.get("target", ""),
                    }
                )
                stats["GeneralToShip"] += 1
            elif needs_ship_general_review(opinion, updated.get("text", "")):
                review_reasons.append(
                    {
                        "type": "ShipGeneralAmbiguous",
                        "opinion_idx": opinion_idx,
                        "target": opinion.get("target", ""),
                        "aspect": aspect,
                    }
                )
                stats["ShipGeneralReview"] += 1

        new_global, reason = maybe_fix_global_sentiment(updated)
        if new_global is not None:
            changes.append(
                {
                    "type": reason,
                    "old_global_sentiment": updated.get("global_sentiment"),
                    "new_global_sentiment": new_global,
                }
            )
            updated["global_sentiment"] = new_global
            stats[reason] += 1

        fixed_records.append(updated)
        if changes:
            stats["records_changed"] += 1
        if review_reasons:
            review_records.append(
                {
                    "line_no": line_no,
                    "text": updated.get("text", ""),
                    "reasons": review_reasons,
                    "record": updated,
                }
            )
            stats["records_for_review"] += 1

    write_jsonl(args.output, fixed_records)
    write_jsonl(args.review, review_records)

    report = {
        "input_file": str(args.input),
        "output_file": str(args.output),
        "review_file": str(args.review),
        "total_records": len(records),
        "records_changed": stats["records_changed"],
        "records_for_review": stats["records_for_review"],
        "change_counts": dict(stats),
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())