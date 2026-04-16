#!/usr/bin/env python3

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path


BASE_INPUT = Path("data/processed/train_final_v3.autofixed_aspect_split.jsonl")
SYNTHETIC_INPUT = Path("data/processed/train_final_v3.synthetic_multi_aspect_natural_aspect_split.jsonl")

BASE_OUTPUT = Path("data/processed/train_final_v3.autofixed_aspect_split_refined.jsonl")
SYNTHETIC_OUTPUT = Path("data/processed/train_final_v3.synthetic_multi_aspect_natural_aspect_split_refined.jsonl")
FINAL_OUTPUT = Path("data/processed/train_final_v3.curated_augmented_natural_aspect_split_refined.jsonl")
REPORT_OUTPUT = Path("data/processed/train_final_v3.general_refine.report.json")

FASHION_REMAP_TARGETS = {
    "giày",
    "dép",
    "túi",
    "đầm",
    "đường may",
    "đường_may",
    "kích_cỡ",
    "kích cỡ",
    "kiểu_dáng",
    "kiểu dáng",
    "mẫu",
    "ảnh_mẫu",
}

ELECTRONICS_REMAP_TARGETS = {
    "linh_kiện_điện_tử",
    "linh kiện điện tử",
    "ổ_cứng",
    "ổ cứng",
    "điện thoại",
    "bàn_phím",
    "bàn phím",
    "chuột",
    "loa",
    "wifi",
    "vân tay",
    "vân_tay",
    "chip",
    "sóng",
    "ram",
    "sạc",
    "khóa",
}

GENERAL_KEEP_TARGETS = {
    "hàng",
    "sản_phẩm",
    "sản phẩm",
    "màu",
    "màu_sắc",
    "chất",
    "chất_liệu",
    "chất liệu",
    "chất_lượng",
    "chất lượng",
    "chất_lượng sản_phẩm",
    "chất lượng sản phẩm",
    "đóng_gói",
    "đóng gói",
    "đóng_gói sản_phẩm",
    "đóng gói sản phẩm",
    "hình",
    "hình_ảnh",
    "gói hàng",
    "gói_hàng",
    "hộp",
    "bao_bì",
    "bao bì",
    "mùi",
    "độ_bền",
    "độ bền",
    "bề_mặt",
    "bề mặt",
    "giấy",
    "dây",
}

GENERAL_PRUNE_TARGETS = {
    "kiểu",
    "ngắn",
    "dài",
    "lần",
    "chưa",
    "chật",
    "minh",
    "dùng",
    "cây",
    "hang",
    "nói_chung",
    "hài_lòng",
    "hài lòng",
    "chat",
    "san",
    "khác",
    "thật_sự",
    "moi",
    "ly",
    "giô",
    "chữ",
}

LOW_SIGNAL_CONTEXT_PATTERNS = [
    re.compile(r"làm_ăn kiểu", flags=re.IGNORECASE),
    re.compile(r"các kiểu", flags=re.IGNORECASE),
    re.compile(r"nói_chung", flags=re.IGNORECASE),
]


def normalize_target(target: str) -> str:
    target = target.lower().strip()
    target = re.sub(r"\s+", " ", target)
    return target


def token_set(target: str) -> set[str]:
    normalized = normalize_target(target).replace("_", " ")
    return {token for token in normalized.split() if token}


def remap_general_target(target: str) -> str | None:
    normalized = normalize_target(target)
    tokens = token_set(target)

    if normalized in FASHION_REMAP_TARGETS:
        return "Fashion"
    if normalized in ELECTRONICS_REMAP_TARGETS:
        return "Electronics"
    if normalized in GENERAL_KEEP_TARGETS:
        return "General"
    if normalized in GENERAL_PRUNE_TARGETS:
        return None

    if tokens & {"giày", "dép", "túi", "đầm"}:
        return "Fashion"
    if {"đường", "may"}.issubset(tokens) or {"kích", "cỡ"}.issubset(tokens):
        return "Fashion"

    if tokens & {"wifi", "chip", "ram", "loa", "chuột", "khóa"}:
        return "Electronics"
    if {"điện", "thoại"}.issubset(tokens) or {"ổ", "cứng"}.issubset(tokens):
        return "Electronics"
    if {"bàn", "phím"}.issubset(tokens) or {"vân", "tay"}.issubset(tokens):
        return "Electronics"
    if tokens & {"sóng", "sạc"}:
        return "Electronics"

    if tokens & {"hàng", "màu", "chất", "hộp", "mùi", "giấy"}:
        return "General"
    if {"sản", "phẩm"}.issubset(tokens) or {"chất", "liệu"}.issubset(tokens):
        return "General"
    if {"chất", "lượng"}.issubset(tokens) or {"đóng", "gói"}.issubset(tokens):
        return "General"

    return None


def should_prune_general(opinion: dict, text: str) -> bool:
    target = normalize_target(opinion.get("target", ""))
    if target in GENERAL_PRUNE_TARGETS:
        return True
    if len(token_set(target)) == 1 and len(target) <= 3 and target not in {"màu", "hộp"}:
        return True
    for pattern in LOW_SIGNAL_CONTEXT_PATTERNS:
        if pattern.search(text):
            if target in {"kiểu", "nói_chung"}:
                return True
    return False


def refine_record(record: dict, counters: Counter, examples: dict[str, list[dict]]) -> dict | None:
    updated = dict(record)
    updated_opinions = []

    for opinion in record.get("opinions", []):
        new_opinion = dict(opinion)
        aspect = opinion.get("aspect")
        if aspect == "General":
            new_aspect = remap_general_target(opinion.get("target", ""))
            if new_aspect is None or should_prune_general(opinion, record.get("text", "")):
                counters["General->Pruned"] += 1
                if len(examples["Pruned"]) < 8:
                    examples["Pruned"].append(
                        {
                            "text": record.get("text", ""),
                            "target": opinion.get("target", ""),
                            "sentiment": opinion.get("sentiment"),
                        }
                    )
                continue
            if new_aspect != "General":
                counters[f"General->{new_aspect}"] += 1
                new_opinion["aspect"] = new_aspect
                if len(examples[new_aspect]) < 8:
                    examples[new_aspect].append(
                        {
                            "text": record.get("text", ""),
                            "target": opinion.get("target", ""),
                            "sentiment": opinion.get("sentiment"),
                        }
                    )
            else:
                counters["General->General"] += 1
        updated_opinions.append(new_opinion)

    if not updated_opinions:
        counters["RecordsDroppedEmpty"] += 1
        return None
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
    examples = defaultdict(list)

    base_records = []
    for record in read_jsonl(BASE_INPUT):
        refined = refine_record(record, counters, examples)
        if refined is not None:
            base_records.append(refined)

    synthetic_records = []
    for record in read_jsonl(SYNTHETIC_INPUT):
        refined = refine_record(record, counters, examples)
        if refined is not None:
            synthetic_records.append(refined)

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
        "refine_counts": dict(sorted(counters.items())),
        "base_aspect_counts": aspect_counts(base_records),
        "synthetic_aspect_counts": aspect_counts(synthetic_records),
        "final_aspect_counts": aspect_counts(final_records),
        "examples": {key: value for key, value in sorted(examples.items())},
    }
    REPORT_OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())