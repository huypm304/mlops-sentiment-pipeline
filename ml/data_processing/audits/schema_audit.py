#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

VALID_ASPECTS = {
    "Fashion",
    "Electronics",
    "General",
    "Service",
    "Ship",
    "Price",
    "App",
}

VALID_SENTIMENTS = {0, 1, 2}


def pct(n: int, d: int) -> float:
    return 0.0 if d == 0 else round(n * 100.0 / d, 4)


def iter_lines(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if line.strip():
                yield line_no, line


def is_valid_span(opinion: Dict[str, Any], text: str) -> bool:
    if "start" not in opinion or "end" not in opinion:
        return False
    start = opinion.get("start")
    end = opinion.get("end")
    if not isinstance(start, int) or not isinstance(end, int):
        return False
    if start < 0 or end < 0 or end <= start:
        return False
    if end > len(text):
        return False
    return True


def audit_file(path: Path) -> Dict[str, Any]:
    counters = {
        "total_non_empty_lines": 0,
        "json_valid": 0,
        "has_text": 0,
        "has_opinions_key": 0,
        "opinions_is_list": 0,
        "has_global_sentiment": 0,
        "global_sentiment_valid": 0,
        "opinions_non_empty": 0,
        "all_opinions_aspect_valid": 0,
        "all_opinions_sentiment_valid": 0,
        "all_opinions_have_target": 0,
        "all_opinions_start_end_valid": 0,
    }

    opinion_total = 0
    opinion_with_offsets = 0

    parse_errors: List[Dict[str, Any]] = []
    schema_errors: List[Dict[str, Any]] = []

    for line_no, raw in iter_lines(path):
        counters["total_non_empty_lines"] += 1

        try:
            obj = json.loads(raw)
            counters["json_valid"] += 1
        except Exception as exc:
            if len(parse_errors) < 20:
                parse_errors.append({"line": line_no, "error": str(exc)})
            continue

        text = obj.get("text")
        opinions = obj.get("opinions")
        global_sentiment = obj.get("global_sentiment")

        has_text = isinstance(text, str) and text.strip() != ""
        if has_text:
            counters["has_text"] += 1

        has_opinions_key = "opinions" in obj
        if has_opinions_key:
            counters["has_opinions_key"] += 1

        opinions_is_list = isinstance(opinions, list)
        if opinions_is_list:
            counters["opinions_is_list"] += 1

        has_global = "global_sentiment" in obj
        if has_global:
            counters["has_global_sentiment"] += 1

        global_ok = global_sentiment in VALID_SENTIMENTS
        if global_ok:
            counters["global_sentiment_valid"] += 1

        row_ok = True

        if not has_text:
            row_ok = False
        if not opinions_is_list:
            row_ok = False
        if not has_global or not global_ok:
            row_ok = False

        if opinions_is_list and len(opinions) > 0:
            counters["opinions_non_empty"] += 1

        aspect_ok = True
        sentiment_ok = True
        target_ok = True
        span_ok = True

        if opinions_is_list:
            for op in opinions:
                opinion_total += 1

                if not isinstance(op, dict):
                    aspect_ok = False
                    sentiment_ok = False
                    target_ok = False
                    span_ok = False
                    continue

                aspect = op.get("aspect")
                sentiment = op.get("sentiment")
                target = op.get("target")

                if aspect not in VALID_ASPECTS:
                    aspect_ok = False
                if sentiment not in VALID_SENTIMENTS:
                    sentiment_ok = False
                if not isinstance(target, str) or target.strip() == "":
                    target_ok = False

                if "start" in op or "end" in op:
                    opinion_with_offsets += 1
                if not (has_text and is_valid_span(op, text if isinstance(text, str) else "")):
                    span_ok = False

        if aspect_ok:
            counters["all_opinions_aspect_valid"] += 1
        if sentiment_ok:
            counters["all_opinions_sentiment_valid"] += 1
        if target_ok:
            counters["all_opinions_have_target"] += 1
        if span_ok:
            counters["all_opinions_start_end_valid"] += 1

        if not row_ok and len(schema_errors) < 20:
            schema_errors.append(
                {
                    "line": line_no,
                    "has_text": has_text,
                    "opinions_is_list": opinions_is_list,
                    "has_global_sentiment": has_global,
                    "global_sentiment_valid": global_ok,
                }
            )

    rows = counters["total_non_empty_lines"]

    checklist = {
        "json_valid_100pct": pct(counters["json_valid"], rows),
        "has_text_100pct": pct(counters["has_text"], rows),
        "has_opinions_key_100pct": pct(counters["has_opinions_key"], rows),
        "opinions_is_list_100pct": pct(counters["opinions_is_list"], rows),
        "global_sentiment_valid_100pct": pct(counters["global_sentiment_valid"], rows),
        "opinions_non_empty_100pct": pct(counters["opinions_non_empty"], rows),
        "aspect_valid_100pct": pct(counters["all_opinions_aspect_valid"], rows),
        "sentiment_valid_100pct": pct(counters["all_opinions_sentiment_valid"], rows),
        "target_present_100pct": pct(counters["all_opinions_have_target"], rows),
        "start_end_integer_and_bounds_100pct": pct(counters["all_opinions_start_end_valid"], rows),
    }

    critical_error_rows = rows - counters["json_valid"]
    critical_schema_error_rate = pct(critical_error_rows, rows)

    return {
        "file": str(path),
        "rows": rows,
        "opinions_total": opinion_total,
        "opinions_with_start_or_end": opinion_with_offsets,
        "counts": counters,
        "checklist_pct": checklist,
        "thresholds": {
            "critical_schema_error_target_pct": 0.0,
            "must_fix_if_over_pct": 0.5,
            "critical_schema_error_actual_pct": critical_schema_error_rate,
            "critical_schema_pass": critical_schema_error_rate == 0.0,
            "must_fix_before_training": critical_schema_error_rate > 0.5,
        },
        "samples": {
            "parse_errors": parse_errors,
            "schema_errors": schema_errors,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--dev", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    train_report = audit_file(args.train)
    dev_report = audit_file(args.dev)

    combined_rows = train_report["rows"] + dev_report["rows"]
    combined_critical_rows = (
        train_report["counts"]["total_non_empty_lines"] - train_report["counts"]["json_valid"]
    ) + (
        dev_report["counts"]["total_non_empty_lines"] - dev_report["counts"]["json_valid"]
    )

    combined = {
        "rows": combined_rows,
        "critical_schema_error_pct": pct(combined_critical_rows, combined_rows),
    }

    out = {
        "train": train_report,
        "dev": dev_report,
        "combined": combined,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(json.dumps({"saved": str(args.output), "combined": combined}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
