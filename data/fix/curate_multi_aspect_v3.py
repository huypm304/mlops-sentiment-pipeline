#!/usr/bin/env python3

from __future__ import annotations

import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path


INPUT_FILE = Path("data/processed/train_final_v3.autofixed.jsonl")
PRUNED_FILE = Path("data/processed/train_final_v3.pruned.jsonl")
SYNTHETIC_FILE = Path("data/processed/train_final_v3.synthetic_multi_aspect.jsonl")
FINAL_FILE = Path("data/processed/train_final_v3.curated_augmented.jsonl")
REPORT_FILE = Path("data/processed/train_final_v3.curated_augmented.report.json")

SEED = 42
MIN_TOKENS = 3
MAX_TOKENS = 28
MAX_PER_PAIR_DIRECTION = 18
MAX_SNIPPET_REUSE = 2

GENERIC_PRODUCT_TARGETS = {
    "áo",
    "hàng",
    "sản_phẩm",
    "sản phẩm",
    "màu",
    "form",
    "size",
    "mẫu",
    "kiểu",
    "chất",
}

ASPECT_PAIRS = [
    ("App", "Ship"),
    ("App", "Price"),
    ("App", "Service"),
    ("Price", "Ship"),
    ("Price", "Service"),
    ("Service", "Ship"),
    ("App", "Product"),
    ("Price", "Product"),
]

DISALLOWED_SYNTHETIC_TARGETS = {
    "Ship": {"gửi"},
    "Price": {"giám"},
}


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
        return None, "offset_mismatch"

    updated = dict(opinion)
    updated["target"] = trimmed
    updated["start"] = new_start
    updated["end"] = new_end
    return updated, None


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_clause_text(text: str) -> str:
    text = normalize_whitespace(text)
    return text.strip(" .,!?:;-")


def extract_clause(text: str, start: int, end: int) -> tuple[str, int, int] | None:
    separators = [0, len(text)]
    for match in re.finditer(r"[\n.!?;]", text):
        separators.extend([match.start(), match.end()])
    for match in re.finditer(r"\b(?:nhưng|tuy_nhiên|tuy nhiên|mà|song|cơ_mà|trừ)\b", text, flags=re.IGNORECASE):
        separators.extend([match.start(), match.end()])
    left = max(point for point in separators if point <= start)
    right = min(point for point in separators if point >= end)
    clause = text[left:right]
    if not clause.strip():
        return None

    stripped_left = len(clause) - len(clause.lstrip())
    clause = clause.strip()
    local_start = start - left - stripped_left
    local_end = end - left - stripped_left
    if local_start < 0 or local_end <= local_start or local_end > len(clause):
        return None
    return clause, local_start, local_end


def lower_first(text: str) -> str:
    if not text:
        return text
    return text[:1].lower() + text[1:]


def upper_first(text: str) -> str:
    if not text:
        return text
    return text[:1].upper() + text[1:]


def build_snippet(record: dict, opinion: dict, line_no: int) -> dict | None:
    if opinion.get("sentiment") not in {0, 1}:
        return None
    lowered_target = opinion["target"].lower()
    if lowered_target in DISALLOWED_SYNTHETIC_TARGETS.get(opinion["aspect"], set()):
        return None
    extracted = extract_clause(record["text"], opinion["start"], opinion["end"])
    if extracted is None:
        return None
    clause, local_start, local_end = extracted
    clause = clean_clause_text(clause)
    if not clause:
        return None

    target = opinion["target"]
    matches = [match.start() for match in re.finditer(re.escape(target), clause)]
    if not matches:
        return None

    matched_start = None
    for candidate in matches:
        if candidate <= local_start <= candidate + len(target):
            matched_start = candidate
            break
    if matched_start is None:
        matched_start = matches[0]
    local_start = matched_start
    local_end = matched_start + len(target)

    token_count = count_tokens(clause)
    if token_count < MIN_TOKENS or token_count > MAX_TOKENS:
        return None
    if opinion["aspect"] == "Ship" and "không đúng" not in clause.lower() and opinion["target"].lower() == "giao":
        # Keep generic "giao" only when the clause is explicitly about incorrect delivery.
        if not re.search(r"\b(?:giao|ship|vận_chuyển|vận chuyển)\b.{0,16}\b(?:chậm|lâu|trễ|sai|thiếu|nhầm|không đúng|không gọi|hoàn|hủy)\b", clause, flags=re.IGNORECASE):
            return None

    return {
        "text": clause,
        "target": target,
        "start": local_start,
        "end": local_end,
        "aspect": opinion["aspect"],
        "sentiment": opinion["sentiment"],
        "source_line": line_no,
        "source_key": f"{opinion['aspect']}|{opinion['sentiment']}|{line_no}|{target}|{clause}",
    }


def compose_synthetic(first: dict, second: dict) -> dict | None:
    first_text = clean_clause_text(first["text"])
    second_text = clean_clause_text(second["text"])
    if not first_text or not second_text:
        return None
    if first["aspect"] == second["aspect"]:
        return None

    connector = " nhưng "
    text = upper_first(first_text) + connector + lower_first(second_text)

    first_start = first["start"]
    first_end = first["end"]
    second_start = len(upper_first(first_text)) + len(connector) + second["start"]
    second_end = second_start + len(second["target"])

    opinions = [
        {
            "target": text[first_start:first_end],
            "aspect": first["aspect"],
            "sentiment": first["sentiment"],
            "start": first_start,
            "end": first_end,
        },
        {
            "target": text[second_start:second_end],
            "aspect": second["aspect"],
            "sentiment": second["sentiment"],
            "start": second_start,
            "end": second_end,
        },
    ]
    return {
        "text": text,
        "opinions": opinions,
        "global_sentiment": 2,
    }


def dataset_summary(records: list[dict]) -> dict:
    multi_aspect = 0
    contrast = 0
    aspect_counter = Counter()
    num_ops_counter = Counter()
    for record in records:
        ops = record.get("opinions", [])
        num_ops_counter[len(ops)] += 1
        aspects = {op.get("aspect") for op in ops}
        sentiments = {op.get("sentiment") for op in ops}
        if len(aspects) >= 2:
            multi_aspect += 1
        if 0 in sentiments and 1 in sentiments:
            contrast += 1
        for opinion in ops:
            aspect_counter[opinion.get("aspect")] += 1
    return {
        "records": len(records),
        "opinions": sum(len(record.get("opinions", [])) for record in records),
        "multi_aspect_records": multi_aspect,
        "contrast_records": contrast,
        "aspect_counter": dict(sorted(aspect_counter.items())),
        "num_ops_counter": dict(sorted(num_ops_counter.items())),
    }


def main() -> int:
    rng = random.Random(SEED)
    stats = Counter()
    pruned_records = []
    source_pools: dict[tuple[str, int], list[dict]] = defaultdict(list)
    existing_texts = set()

    with INPUT_FILE.open(encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, 1):
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            stats["input_records"] += 1
            record = json.loads(raw_line)
            text = record.get("text", "")
            opinions = record.get("opinions", [])
            kept = []
            for opinion in opinions:
                normalized, error = normalize_target(text, opinion)
                if error or normalized is None:
                    stats["invalid_opinions_skipped"] += 1
                    continue
                target_key = normalized["target"].lower()
                if normalized["aspect"] == "Product" and target_key in GENERIC_PRODUCT_TARGETS:
                    stats["pruned_generic_product_targets"] += 1
                    continue
                kept.append(normalized)

            if not kept:
                stats["dropped_empty_after_prune"] += 1
                continue

            updated = dict(record)
            updated["opinions"] = kept
            pruned_records.append(updated)
            existing_texts.add(updated["text"])

            for opinion in kept:
                snippet = build_snippet(updated, opinion, line_no)
                if snippet is None:
                    stats["snippet_candidates_skipped"] += 1
                    continue
                source_pools[(snippet["aspect"], snippet["sentiment"])].append(snippet)

    synthetic_records = []
    synthetic_texts = set()
    pair_counts = Counter()
    snippet_usage = Counter()

    for aspect_a, aspect_b in ASPECT_PAIRS:
        directions = [
            ((aspect_a, 1), (aspect_b, 0)),
            ((aspect_a, 0), (aspect_b, 1)),
        ]
        for left_key, right_key in directions:
            left_pool = list(source_pools.get(left_key, []))
            right_pool = list(source_pools.get(right_key, []))
            rng.shuffle(left_pool)
            rng.shuffle(right_pool)
            generated = 0
            for left in left_pool:
                if generated >= MAX_PER_PAIR_DIRECTION:
                    break
                for right in right_pool:
                    if generated >= MAX_PER_PAIR_DIRECTION:
                        break
                    if left["source_line"] == right["source_line"]:
                        continue
                    if snippet_usage[left["source_key"]] >= MAX_SNIPPET_REUSE:
                        continue
                    if snippet_usage[right["source_key"]] >= MAX_SNIPPET_REUSE:
                        continue
                    synthetic = compose_synthetic(left, right)
                    if synthetic is None:
                        continue
                    text = synthetic["text"]
                    if text in existing_texts or text in synthetic_texts:
                        continue
                    synthetic_records.append(synthetic)
                    synthetic_texts.add(text)
                    snippet_usage[left["source_key"]] += 1
                    snippet_usage[right["source_key"]] += 1
                    generated += 1
                    pair_counts[(left_key, right_key)] += 1

    merged_records = pruned_records + synthetic_records
    rng.shuffle(merged_records)

    PRUNED_FILE.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in pruned_records), encoding="utf-8")
    SYNTHETIC_FILE.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in synthetic_records), encoding="utf-8")
    FINAL_FILE.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in merged_records), encoding="utf-8")

    report = {
        "input": str(INPUT_FILE),
        "pruned_file": str(PRUNED_FILE),
        "synthetic_file": str(SYNTHETIC_FILE),
        "final_file": str(FINAL_FILE),
        "stats": dict(sorted(stats.items())),
        "source_pool_sizes": {f"{aspect}_{sentiment}": len(pool) for (aspect, sentiment), pool in sorted(source_pools.items())},
        "synthetic_pair_counts": {
            f"{left_aspect}_{left_sent}__{right_aspect}_{right_sent}": count
            for ((left_aspect, left_sent), (right_aspect, right_sent)), count in sorted(pair_counts.items())
        },
        "pruned_summary": dataset_summary(pruned_records),
        "synthetic_summary": dataset_summary(synthetic_records),
        "final_summary": dataset_summary(merged_records),
    }
    REPORT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())