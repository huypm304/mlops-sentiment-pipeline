#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/data_train_v8_aste.modifier_force_auto_merged.jsonl")
DEFAULT_ERRORS = Path("/home/uph3hc/project/mlops-sentiment-pipeline/aste_force_audit_errors.jsonl")
DEFAULT_OUT_DIR = Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/aste_force_auto_batches")

BATCH_SPECS = [
    ("batch_01_span_exact", "Span-only fixes with exact actionable span corrections", True),
    ("batch_02_sentiment_only", "Sentiment-only fixes with clear polarity cues", True),
    ("batch_03_aspect_only", "Aspect-only fixes based on target keyword matches", True),
    ("batch_04_mixed_safe", "Mixed safe fixes without unresolved span issues", True),
    ("batch_05_unresolved_review", "Records still needing manual review because span cannot be fixed safely", False),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split ASTE QA fixes into sequential batches and apply safe batches step by step")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--errors", type=Path, default=DEFAULT_ERRORS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--chunk-size", type=int, default=250)
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def is_actionable_span(error: dict[str, Any]) -> bool:
    return error.get("type") == "Span lệch" and error.get("suggestion") != error.get("current")


def is_unresolved_span(error: dict[str, Any]) -> bool:
    return error.get("type") == "Span lệch" and error.get("suggestion") == error.get("current")


def categorize_error_record(row: dict[str, Any]) -> str:
    errors = row.get("errors", [])
    types = {error.get("type") for error in errors}
    has_unresolved = any(is_unresolved_span(error) for error in errors)
    has_actionable_span = any(is_actionable_span(error) for error in errors)

    if has_unresolved:
        return "batch_05_unresolved_review"
    if types == {"Span lệch"} and has_actionable_span:
        return "batch_01_span_exact"
    if types == {"Sentiment sai"}:
        return "batch_02_sentiment_only"
    if types == {"Aspect sai"}:
        return "batch_03_aspect_only"
    return "batch_04_mixed_safe"


def chunk_rows(rows: list[dict[str, Any]], chunk_size: int) -> list[list[dict[str, Any]]]:
    return [rows[index:index + chunk_size] for index in range(0, len(rows), chunk_size)]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def apply_batch(lines: list[str], rows: list[dict[str, Any]]) -> list[str]:
    updated = list(lines)
    for row in rows:
        line_index = int(row["line_no"]) - 1
        fixed_record = {
            "text": row["text"],
            "triplets": row["fixed_triplets"],
        }
        updated[line_index] = json.dumps(fixed_record, ensure_ascii=False) + "\n"
    return updated


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    error_rows = load_jsonl(args.errors)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in error_rows:
        grouped[categorize_error_record(row)].append(row)

    manifest_dir = args.out_dir / "manifests"
    checkpoint_dir = args.out_dir / "checkpoints"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    summary_rows: list[dict[str, Any]] = []
    chunk_counter: Counter[str] = Counter()

    for batch_name, description, applyable in BATCH_SPECS:
        rows = sorted(grouped.get(batch_name, []), key=lambda item: item["line_no"])
        chunks = chunk_rows(rows, args.chunk_size)
        for idx, chunk in enumerate(chunks, start=1):
            manifest_path = manifest_dir / f"{batch_name}.part_{idx:02d}.jsonl"
            write_jsonl(manifest_path, chunk)
        chunk_counter[batch_name] = len(chunks)
        summary_rows.append(
            {
                "batch": batch_name,
                "description": description,
                "applyable": applyable,
                "records": len(rows),
                "chunks": len(chunks),
            }
        )

    with open(args.input, encoding="utf-8") as handle:
        current_lines = handle.readlines()

    checkpoint_paths: list[str] = []
    for batch_index, (batch_name, description, applyable) in enumerate(BATCH_SPECS, start=1):
        if not applyable:
            continue
        rows = sorted(grouped.get(batch_name, []), key=lambda item: item["line_no"])
        if not rows:
            continue
        current_lines = apply_batch(current_lines, rows)
        checkpoint_path = checkpoint_dir / f"step_{batch_index:02d}_{batch_name}.jsonl"
        with open(checkpoint_path, "w", encoding="utf-8") as handle:
            handle.writelines(current_lines)
        checkpoint_paths.append(str(checkpoint_path))

    final_path = checkpoint_dir / "final_safe_batched_fix.jsonl"
    with open(final_path, "w", encoding="utf-8") as handle:
        handle.writelines(current_lines)

    report = {
        "input": str(args.input),
        "errors": str(args.errors),
        "out_dir": str(args.out_dir),
        "chunk_size": args.chunk_size,
        "batches": summary_rows,
        "checkpoint_paths": checkpoint_paths,
        "final_safe_output": str(final_path),
    }

    report_path = args.out_dir / "batch_report.json"
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)

    md_lines = [
        "# ASTE QA Batch Report",
        f"**Input**: {args.input.name}",
        f"**Error Source**: {args.errors.name}",
        f"**Chunk size**: {args.chunk_size}",
        "",
        "| Batch | Description | Apply | Records | Chunks |",
        "|---|---|---:|---:|---:|",
    ]
    for row in summary_rows:
        md_lines.append(
            f"| {row['batch']} | {row['description']} | {'yes' if row['applyable'] else 'no'} | {row['records']} | {row['chunks']} |"
        )
    md_lines.extend([
        "",
        f"**Final safe output**: {final_path.name}",
    ])

    markdown_path = args.out_dir / "batch_report.md"
    with open(markdown_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(md_lines) + "\n")

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()