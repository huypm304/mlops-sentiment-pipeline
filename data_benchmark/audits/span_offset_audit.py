#!/usr/bin/env python3
import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple


def pct(n: int, d: int) -> float:
    return 0.0 if d == 0 else round(n * 100.0 / d, 4)


def iter_rows(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if line.strip():
                yield line_no, json.loads(line)


def is_too_wide_span(span_text: str, target: str) -> bool:
    s_len = len(span_text.strip())
    t_len = len(target.strip())
    if t_len == 0:
        return False
    if s_len <= t_len + 3:
        return False
    return s_len > (2 * t_len)


def audit_file(path: Path) -> Dict[str, Any]:
    total_rows = 0
    total_ops = 0

    exact_match = 0
    trimmed_match = 0
    empty_span = 0
    out_of_bound = 0
    too_wide = 0
    missing_offsets = 0

    duplicate_exact_opinion_rows = 0
    duplicate_same_aspect_rows = 0
    duplicate_exact_opinion_total = 0

    samples = {
        "offset_mismatch": [],
        "empty_span": [],
        "out_of_bound": [],
        "too_wide_span": [],
        "duplicate_exact_opinion": [],
        "duplicate_same_aspect": [],
    }

    for line_no, obj in iter_rows(path):
        total_rows += 1
        text = obj.get("text", "")
        opinions = obj.get("opinions", [])

        seen_exact = Counter()
        seen_aspect = Counter()

        for op in opinions:
            total_ops += 1

            target = op.get("target", "")
            aspect = op.get("aspect")
            sentiment = op.get("sentiment")
            start = op.get("start")
            end = op.get("end")

            seen_aspect[aspect] += 1

            if not isinstance(start, int) or not isinstance(end, int):
                missing_offsets += 1
                continue

            if start < 0 or end < 0 or end <= start or end > len(text):
                out_of_bound += 1
                if len(samples["out_of_bound"]) < 20:
                    samples["out_of_bound"].append(
                        {"line": line_no, "start": start, "end": end, "text_len": len(text)}
                    )
                continue

            span_text = text[start:end]
            op_key = (start, end, aspect, sentiment)
            seen_exact[op_key] += 1

            if (not isinstance(target, str)) or target.strip() == "":
                empty_span += 1
                if len(samples["empty_span"]) < 20:
                    samples["empty_span"].append({"line": line_no, "target": target})
                continue

            if span_text == target:
                exact_match += 1
                trimmed_match += 1
            elif span_text.strip() == target.strip():
                trimmed_match += 1
                if len(samples["offset_mismatch"]) < 20:
                    samples["offset_mismatch"].append(
                        {"line": line_no, "target": target, "span_text": span_text}
                    )
            else:
                if len(samples["offset_mismatch"]) < 20:
                    samples["offset_mismatch"].append(
                        {"line": line_no, "target": target, "span_text": span_text}
                    )

            if is_too_wide_span(span_text, target):
                too_wide += 1
                if len(samples["too_wide_span"]) < 20:
                    samples["too_wide_span"].append(
                        {
                            "line": line_no,
                            "target": target,
                            "span_text": span_text,
                            "start": start,
                            "end": end,
                        }
                    )

        row_exact_dup = sum(v - 1 for v in seen_exact.values() if v > 1)
        if row_exact_dup > 0:
            duplicate_exact_opinion_rows += 1
            duplicate_exact_opinion_total += row_exact_dup
            if len(samples["duplicate_exact_opinion"]) < 20:
                samples["duplicate_exact_opinion"].append(
                    {"line": line_no, "duplicate_count": row_exact_dup}
                )

        aspect_dups = {a: c for a, c in seen_aspect.items() if c > 1}
        if aspect_dups:
            duplicate_same_aspect_rows += 1
            if len(samples["duplicate_same_aspect"]) < 20:
                samples["duplicate_same_aspect"].append(
                    {"line": line_no, "aspects": aspect_dups}
                )

    valid_offset_ops = total_ops - missing_offsets - out_of_bound

    report = {
        "file": str(path),
        "rows": total_rows,
        "opinions": total_ops,
        "metrics": {
            "exact_offset_match_count": exact_match,
            "exact_offset_match_pct": pct(exact_match, valid_offset_ops),
            "trimmed_offset_match_count": trimmed_match,
            "trimmed_offset_match_pct": pct(trimmed_match, valid_offset_ops),
            "empty_span_count": empty_span,
            "empty_span_pct": pct(empty_span, total_ops),
            "out_of_bound_count": out_of_bound,
            "out_of_bound_pct": pct(out_of_bound, total_ops),
            "span_too_wide_count": too_wide,
            "span_too_wide_pct": pct(too_wide, total_ops),
            "duplicate_exact_opinion_count": duplicate_exact_opinion_total,
            "duplicate_exact_opinion_pct": pct(duplicate_exact_opinion_total, total_ops),
            "duplicate_same_aspect_rows_count": duplicate_same_aspect_rows,
            "duplicate_same_aspect_rows_pct": pct(duplicate_same_aspect_rows, total_rows),
            "missing_offsets_count": missing_offsets,
            "missing_offsets_pct": pct(missing_offsets, total_ops),
        },
        "thresholds": {
            "exact_offset_match_target_pct": 99.5,
            "trimmed_offset_match_target_pct": 99.8,
            "empty_span_target_pct": 0.0,
            "out_of_bound_target_pct": 0.0,
            "span_too_wide_target_pct_lt": 1.0,
            "duplicate_exact_opinion_target_pct_lt": 0.5,
            "pass_exact_offset": pct(exact_match, valid_offset_ops) >= 99.5,
            "pass_trimmed_offset": pct(trimmed_match, valid_offset_ops) >= 99.8,
            "pass_empty_span": empty_span == 0,
            "pass_out_of_bound": out_of_bound == 0,
            "pass_span_too_wide": pct(too_wide, total_ops) < 1.0,
            "pass_duplicate_exact_opinion": pct(duplicate_exact_opinion_total, total_ops) < 0.5,
        },
        "samples": samples,
    }
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--dev", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    train_report = audit_file(args.train)
    dev_report = audit_file(args.dev)

    combined = {
        "rows": train_report["rows"] + dev_report["rows"],
        "opinions": train_report["opinions"] + dev_report["opinions"],
    }

    out = {"train": train_report, "dev": dev_report, "combined": combined}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(json.dumps({"saved": str(args.output), "combined": combined}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
