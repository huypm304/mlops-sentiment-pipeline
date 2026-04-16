#!/usr/bin/env python3

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


BASE_INPUT = Path("data/processed/train_final_v3.autofixed.jsonl")
SYNTHETIC_INPUT = Path("data/processed/train_final_v3.synthetic_multi_aspect_natural.jsonl")

BASE_OUTPUT = Path("data/processed/train_final_v3.autofixed_aspect_split.jsonl")
SYNTHETIC_OUTPUT = Path("data/processed/train_final_v3.synthetic_multi_aspect_natural_aspect_split.jsonl")
FINAL_OUTPUT = Path("data/processed/train_final_v3.curated_augmented_natural_aspect_split.jsonl")
REPORT_OUTPUT = Path("data/processed/train_final_v3.aspect_split.report.json")

FASHION_KEYWORDS = {
    "áo",
    "quần",
    "váy",
    "vải",
    "size",
    "form",
    "phom",
}

GENERAL_KEYWORDS = {
    "hàng",
    "sản phẩm",
    "sản_phẩm",
    "sp",
    "mặt hàng",
    "mặt_hàng",
    "gói hàng",
    "gói_hàng",
}

ELECTRONICS_KEYWORDS = {
    "pin",
    "màn hình",
    "màn_hình",
    "camera",
    "máy",
    "củ sạc",
    "củ_sạc",
    "cục sạc",
    "cục_sạc",
    "cáp sạc",
    "cáp_sạc",
}


def normalize_target(target: str) -> str:
    lowered = target.lower().strip()
    lowered = re.sub(r"\s+", " ", lowered)
    return lowered


def token_set(target: str) -> set[str]:
    normalized = normalize_target(target).replace("_", " ")
    return {token for token in normalized.split() if token}


def remap_product_aspect(target: str) -> str:
    normalized = normalize_target(target)
    tokens = token_set(target)

    if normalized in ELECTRONICS_KEYWORDS:
        return "Electronics"
    if normalized in FASHION_KEYWORDS:
        return "Fashion"
    if normalized in GENERAL_KEYWORDS:
        return "General"

    if tokens & {"pin", "camera", "máy"}:
        return "Electronics"
    if {"màn", "hình"}.issubset(tokens):
        return "Electronics"
    if {"củ", "sạc"}.issubset(tokens) or {"cục", "sạc"}.issubset(tokens) or {"cáp", "sạc"}.issubset(tokens):
        return "Electronics"

    if tokens & {"áo", "quần", "váy", "vải", "size", "form", "phom"}:
        return "Fashion"

    if tokens & {"hàng", "sản", "phẩm", "sp"}:
        return "General"

    return "General"


def remap_record(record: dict, counters: Counter, examples: dict[str, list[dict]]) -> dict:
    updated = dict(record)
    updated_opinions = []

    for opinion in record.get("opinions", []):
        new_opinion = dict(opinion)
        old_aspect = opinion.get("aspect")
        if old_aspect == "Product":
            new_aspect = remap_product_aspect(opinion.get("target", ""))
            new_opinion["aspect"] = new_aspect
            counters[f"Product->{new_aspect}"] += 1
            if len(examples[new_aspect]) < 8:
                examples[new_aspect].append(
                    {
                        "text": record.get("text", ""),
                        "target": opinion.get("target", ""),
                        "sentiment": opinion.get("sentiment"),
                    }
                )
        updated_opinions.append(new_opinion)

    updated["opinions"] = updated_opinions
    return updated


def read_jsonl(path: Path) -> list[dict]:
    records = []
    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            raw_line = raw_line.strip()
            if raw_line:
                records.append(json.loads(raw_line))
    return records


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def aspect_counts(records: list[dict]) -> dict[str, int]:
    counts = Counter()
    for record in records:
        for opinion in record.get("opinions", []):
            counts[opinion.get("aspect", "<missing>")] += 1
    return dict(sorted(counts.items()))


def main() -> int:
    counters = Counter()
    examples = {"Fashion": [], "General": [], "Electronics": []}

    base_records = [remap_record(record, counters, examples) for record in read_jsonl(BASE_INPUT)]
    synthetic_records = [remap_record(record, counters, examples) for record in read_jsonl(SYNTHETIC_INPUT)]
    final_records = base_records + synthetic_records

    write_jsonl(BASE_OUTPUT, base_records)
    write_jsonl(SYNTHETIC_OUTPUT, synthetic_records)
    write_jsonl(FINAL_OUTPUT, final_records)

    report = {
        "base_input": str(BASE_INPUT),
        "synthetic_input": str(SYNTHETIC_INPUT),
        "base_output": str(BASE_OUTPUT),
        "synthetic_output": str(SYNTHETIC_OUTPUT),
        "final_output": str(FINAL_OUTPUT),
        "remap_counts": dict(sorted(counters.items())),
        "base_aspect_counts": aspect_counts(base_records),
        "synthetic_aspect_counts": aspect_counts(synthetic_records),
        "final_aspect_counts": aspect_counts(final_records),
        "examples": examples,
    }
    REPORT_OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())