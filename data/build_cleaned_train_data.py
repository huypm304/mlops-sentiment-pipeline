#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


VALID_ASPECTS = {"Product", "Ship", "Price", "App", "Service"}
VALID_SENTIMENTS = {0, 1, 2}

# Conservative blocklist for obviously broken target spans observed in the dataset.
BAD_TARGETS = {
    "bên",
    "biết",
    "gui",
    "lovee",
    "mau",
    "may",
    "tang",
    "trội_ôi",
    "tuy",
    "vừa",
}


def spans_overlap(left: tuple[int, int], right: tuple[int, int]) -> bool:
    return left[0] < right[1] and right[0] < left[1]


def validate_row(row: dict[str, Any]) -> list[str]:
    reasons: list[str] = []

    text = row.get("text")
    opinions = row.get("opinions")
    global_sentiment = row.get("global_sentiment")

    if not isinstance(text, str) or not isinstance(opinions, list):
        return ["invalid_schema"]

    if global_sentiment not in VALID_SENTIMENTS:
        reasons.append("invalid_global_sentiment")

    coverage = row.get("coverage")
    if isinstance(coverage, (int, float)) and coverage < 1.0:
        reasons.append("partial_coverage")

    seen_aspects: set[str] = set()
    spans: list[tuple[int, int, str, str]] = []

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
        if target.casefold() in BAD_TARGETS:
            reasons.append("bad_target_heuristic")
        spans.append((start, end, aspect, target))

    spans.sort()
    for index, left in enumerate(spans):
        for right in spans[index + 1 :]:
            if spans_overlap((left[0], left[1]), (right[0], right[1])):
                reasons.append("overlapping_spans")
                if {left[2], right[2]} == {"Ship", "Product"}:
                    reasons.append("ship_product_overlap")
                break
        else:
            continue
        break

    return sorted(set(reasons))


def build_cleaned_dataset(input_path: Path, output_path: Path, report_path: Path) -> dict[str, Any]:
    kept_rows: list[str] = []
    removal_counts: Counter[str] = Counter()
    source_kept_counts: Counter[str] = Counter()
    source_removed_counts: Counter[str] = Counter()
    sample_removed: dict[str, list[dict[str, Any]]] = {}

    total_rows = 0
    for line_number, raw_line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw_line.strip():
            continue
        total_rows += 1
        row = json.loads(raw_line)
        reasons = validate_row(row)
        source = row.get("source", "<missing>")

        if reasons:
            source_removed_counts[source] += 1
            for reason in reasons:
                removal_counts[reason] += 1
                if len(sample_removed.setdefault(reason, [])) < 5:
                    sample_removed[reason].append(
                        {
                            "line": line_number,
                            "text": row.get("text", "")[:220],
                            "opinions": row.get("opinions", []),
                        }
                    )
            continue

        source_kept_counts[source] += 1
        kept_rows.append(json.dumps(row, ensure_ascii=False))

    output_path.write_text("\n".join(kept_rows) + ("\n" if kept_rows else ""), encoding="utf-8")

    report = {
        "input": str(input_path),
        "output": str(output_path),
        "total_rows": total_rows,
        "kept_rows": len(kept_rows),
        "removed_rows": total_rows - len(kept_rows),
        "removal_counts": dict(sorted(removal_counts.items())),
        "source_kept_counts": dict(sorted(source_kept_counts.items())),
        "source_removed_counts": dict(sorted(source_removed_counts.items())),
        "sample_removed": sample_removed,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a conservative cleaned ABSA training set.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/train_data.jsonl"),
        help="Input JSONL file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/cleaned_train_data.jsonl"),
        help="Output cleaned JSONL file.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("data/processed/cleaned_train_data.report.json"),
        help="Path to write the cleaning report JSON.",
    )
    args = parser.parse_args()

    report = build_cleaned_dataset(args.input, args.output, args.report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())