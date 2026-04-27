#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_INPUT_DIR = Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/aste_force_auto_batches/manifests")
DEFAULT_OUTPUT_DIR = Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/aste_force_auto_batches/batch05_mini_batches")

TARGET_GROUPS = {
    "fashion_color_size": {"màu", "size", "áo", "quần", "váy", "giày", "dép", "vải", "form", "chất", "chất_vải"},
    "service_shop_support": {"shop", "bảo hành", "nhân viên", "dịch_vụ", "dịch vụ", "tư_vấn", "tư vấn", "phục_vụ", "phục vụ"},
    "ship_delivery_packaging": {"giao", "ship", "đóng_gói", "đóng gói", "đơn_ship", "khâu_giao_đơn", "gói hàng", "giao_hàng", "giao hàng"},
    "price_value": {"giá", "tiền", "tầm giá", "phí", "đồng tiền"},
    "electronics_device": {"máy", "pin", "màn hình", "màn_hình", "loa", "chip", "sạc", "củ_sạc", "camera", "linh_kiện_điện_tử"},
    "app_platform": {"app", "ứng dụng", "ứng_dụng", "phần_mềm", "phần mềm", "cập nhật", "web"},
    "general_product": {"hàng", "sản_phẩm", "sản phẩm", "mẫu"},
}

TEXT_PATTERNS = [
    ("negation", re.compile(r"\b(?:không|ko|k|đéo)\b", re.IGNORECASE)),
    ("error_defect", re.compile(r"\b(?:bị|lỗi|lag|đơ|hỏng|rách|dính|móp|méo|tróc)\b", re.IGNORECASE)),
    ("modifier", re.compile(r"\b(?:hơi|quá|rất|khá|cũng|vẫn)\b", re.IGNORECASE)),
    ("comparison", re.compile(r"\b(?:như|hơn|kém|so với|đúng mẫu|y hình|như hình)\b", re.IGNORECASE)),
]

PRIORITY_ORDER = [
    "fashion_color_size",
    "service_shop_support",
    "ship_delivery_packaging",
    "price_value",
    "electronics_device",
    "app_platform",
    "general_product",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split batch 05 unresolved ASTE review rows into smaller pattern-based mini-batches")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--chunk-size", type=int, default=100)
    return parser.parse_args()


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower().replace("_", " ")).strip()


def load_batch05_rows(input_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(input_dir.glob("batch_05_unresolved_review.part_*.jsonl")):
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    return rows


def get_targets(row: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for error in row.get("errors", []):
        triplet = row["fixed_triplets"][error["triplet_idx"]]
        values.append(normalize_text(triplet.get("target", "")))
    return values


def get_aspects(row: dict[str, Any]) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for error in row.get("errors", []):
        aspect = row["fixed_triplets"][error["triplet_idx"]].get("aspect", "")
        if aspect and aspect not in seen:
            seen.add(aspect)
            values.append(aspect)
    return values


def pick_primary_family(targets: list[str], aspects: list[str], text: str) -> str:
    target_set = set(targets)
    for family in PRIORITY_ORDER:
        if target_set & {normalize_text(item) for item in TARGET_GROUPS[family]}:
            return family

    aspect_map = {
        "Fashion": "fashion_color_size",
        "Service": "service_shop_support",
        "Ship": "ship_delivery_packaging",
        "Price": "price_value",
        "Electronics": "electronics_device",
        "App": "app_platform",
        "General": "general_product",
    }
    for aspect in aspects:
        if aspect in aspect_map:
            return aspect_map[aspect]

    text_norm = normalize_text(text)
    for family in PRIORITY_ORDER:
        for keyword in TARGET_GROUPS[family]:
            if normalize_text(keyword) in text_norm:
                return family
    return "misc_other"


def pick_secondary_pattern(text: str) -> str:
    for label, pattern in TEXT_PATTERNS:
        if pattern.search(text):
            return label
    return "plain"


def chunk_rows(rows: list[dict[str, Any]], chunk_size: int) -> list[list[dict[str, Any]]]:
    return [rows[index:index + chunk_size] for index in range(0, len(rows), chunk_size)]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    rows = load_batch05_rows(args.input_dir)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    family_counter: Counter[str] = Counter()
    pattern_counter: Counter[str] = Counter()

    for row in rows:
        targets = get_targets(row)
        aspects = get_aspects(row)
        family = pick_primary_family(targets, aspects, row.get("text", ""))
        pattern = pick_secondary_pattern(row.get("text", ""))
        bucket = f"{family}__{pattern}"
        grouped[bucket].append(row)
        family_counter[family] += 1
        pattern_counter[pattern] += 1

    manifests_dir = args.output_dir / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)

    bucket_summaries: list[dict[str, Any]] = []
    for bucket, bucket_rows in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
        parts = chunk_rows(sorted(bucket_rows, key=lambda row: row["line_no"]), args.chunk_size)
        for idx, chunk in enumerate(parts, start=1):
            write_jsonl(manifests_dir / f"{bucket}.part_{idx:02d}.jsonl", chunk)
        bucket_summaries.append({
            "bucket": bucket,
            "records": len(bucket_rows),
            "chunks": len(parts),
            "sample_lines": [row["line_no"] for row in bucket_rows[:5]],
        })

    report = {
        "input_dir": str(args.input_dir),
        "output_dir": str(args.output_dir),
        "total_rows": len(rows),
        "chunk_size": args.chunk_size,
        "family_distribution": dict(family_counter),
        "pattern_distribution": dict(pattern_counter),
        "buckets": bucket_summaries,
    }

    with open(args.output_dir / "batch05_pattern_report.json", "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)

    md_lines = [
        "# Batch 05 Mini-Batch Report",
        f"**Total unresolved review rows**: {len(rows)}",
        f"**Chunk size**: {args.chunk_size}",
        "",
        "## Family Distribution",
        "",
        "| Family | Records |",
        "|---|---:|",
    ]
    for family, count in family_counter.most_common():
        md_lines.append(f"| {family} | {count} |")

    md_lines.extend([
        "",
        "## Pattern Distribution",
        "",
        "| Pattern | Records |",
        "|---|---:|",
    ])
    for pattern, count in pattern_counter.most_common():
        md_lines.append(f"| {pattern} | {count} |")

    md_lines.extend([
        "",
        "## Mini-Batches",
        "",
        "| Mini-batch | Records | Chunks | Sample lines |",
        "|---|---:|---:|---|",
    ])
    for row in bucket_summaries:
        sample_lines = ", ".join(str(item) for item in row["sample_lines"])
        md_lines.append(f"| {row['bucket']} | {row['records']} | {row['chunks']} | {sample_lines} |")

    with open(args.output_dir / "batch05_pattern_report.md", "w", encoding="utf-8") as handle:
        handle.write("\n".join(md_lines) + "\n")

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()