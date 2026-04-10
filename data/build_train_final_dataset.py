#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


HIGH_RISK_REASONS = {
    "neg_global_pos_opinion",
    "pos_global_neg_opinion",
    "suspect_target",
}


def load_drop_map(review_path: Path) -> tuple[set[int], Counter[str]]:
    lines_to_drop: set[int] = set()
    reason_counts: Counter[str] = Counter()

    for raw_line in review_path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        item = json.loads(raw_line)
        reasons = set(item["review_reasons"])
        risky_reasons = sorted(reasons & HIGH_RISK_REASONS)
        if not risky_reasons:
            continue
        lines_to_drop.add(int(item["line"]))
        reason_counts.update(risky_reasons)

    return lines_to_drop, reason_counts


def build_train_final(
    repaired_path: Path,
    review_path: Path,
    output_path: Path,
    report_path: Path,
) -> dict[str, Any]:
    lines_to_drop, reason_counts = load_drop_map(review_path)

    kept_rows: list[str] = []
    dropped_examples: list[dict[str, Any]] = []
    total_rows = 0
    dropped_rows = 0

    for line_number, raw_line in enumerate(repaired_path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw_line.strip():
            continue
        total_rows += 1
        if line_number in lines_to_drop:
            dropped_rows += 1
            if len(dropped_examples) < 20:
                row = json.loads(raw_line)
                dropped_examples.append(
                    {
                        "line": line_number,
                        "text": row["text"][:220],
                    }
                )
            continue
        kept_rows.append(raw_line)

    output_path.write_text("\n".join(kept_rows) + ("\n" if kept_rows else ""), encoding="utf-8")

    report = {
        "input": str(repaired_path),
        "review_input": str(review_path),
        "output": str(output_path),
        "total_rows": total_rows,
        "kept_rows": len(kept_rows),
        "dropped_rows": dropped_rows,
        "drop_rate": round(dropped_rows / total_rows, 6) if total_rows else 0.0,
        "drop_reasons": dict(sorted(reason_counts.items())),
        "high_risk_reason_set": sorted(HIGH_RISK_REASONS),
        "dropped_examples": dropped_examples,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a high-confidence final training dataset.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/train_data.repaired.jsonl"),
        help="Input repaired dataset.",
    )
    parser.add_argument(
        "--review-input",
        type=Path,
        default=Path("data/processed/train_data.review_candidates.jsonl"),
        help="Review candidates file with risk annotations.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/train_final.jsonl"),
        help="Output final dataset.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("data/processed/train_final.report.json"),
        help="Output report path.",
    )
    args = parser.parse_args()

    report = build_train_final(args.input, args.review_input, args.output, args.report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())