#!/usr/bin/env python3

from __future__ import annotations

import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path


INPUT_FILE = Path("data/processed/train_final_v3.autofixed_aspect_split_refined.jsonl")
BASE_FINAL_FILE = Path("data/processed/train_final_v3.curated_augmented_natural_aspect_split_refined.jsonl")
SYNTHETIC_FILE = Path("data/processed/train_final_v3.synthetic_targeted_contrast_aspect_split_refined.jsonl")
FINAL_FILE = Path("data/processed/train_final_v3.curated_augmented_natural_aspect_split_refined_boosted.jsonl")
REPORT_FILE = Path("data/processed/train_final_v3.targeted_contrast_boost.report.json")

SEED = 42
MIN_TOKENS = 4
MAX_TOKENS = 24
MAX_PER_DIRECTION = 26
MAX_SNIPPET_REUSE = 1
MAX_CLAUSE_REUSE = 1

TARGET_PAIRS = [
    ("Fashion", "Price"),
    ("Electronics", "Price"),
    ("General", "Price"),
]

CLAUSE_SEPARATORS = r"[\n.!?;]"
CLAUSE_BREAKERS = r"\b(?:nhưng|tuy_nhiên|tuy nhiên|còn|dù_vậy|dù vậy|mà|song|trái_lại|trái lại)\b"
CONNECTORS = [" nhưng ", ". Tuy nhiên, ", "; còn ", ". Còn ", ", nhưng "]

POSITIVE_CUES = re.compile(
    r"\b(?:đẹp|tốt|xịn|xinh|ổn|mượt|nhanh|tiện|rẻ|hợp_lý|hợp lý|phù_hợp|phù hợp|"
    r"chất_lượng|chất lượng|chuẩn|ưng|ok|trâu|nhiệt_tình|nhiệt tình|cẩn_thận|cẩn thận|"
    r"chắc_chắn|chắc chắn|y hình)\b",
    flags=re.IGNORECASE,
)
NEGATIVE_CUES = re.compile(
    r"\b(?:xấu|tệ|kém|mỏng|rộng|chật|ngắn|dài|lỗi|lag|giật|đơ|chậm|lâu|trễ|đắt|mắc|"
    r"cao|ảo|rách|bẩn|hôi|nhăn|không đúng|không giống|không đẹp|không ổn|không mượt|"
    r"không trả_lời|không trả lời|giao sai|giao thiếu)\b",
    flags=re.IGNORECASE,
)

ASPECT_PATTERNS = {
    "Price": re.compile(r"(?:giá|tầm giá|giá tiền|tiền|voucher|mã giảm giá|phí ship)", flags=re.IGNORECASE),
    "Fashion": re.compile(r"(?:áo|quần|váy|vải|size|form|phom|giày|dép|túi|đầm|đường may|kiểu_dáng|mẫu)", flags=re.IGNORECASE),
    "Electronics": re.compile(r"(?:pin|màn_hình|màn hình|camera|máy|củ_sạc|cáp_sạc|cục_sạc|điện thoại|ổ_cứng|bàn_phím|chuột|loa|wifi|vân_tay|vân tay|chip|ram|sóng|sạc)", flags=re.IGNORECASE),
    "General": re.compile(r"(?:hàng|sản_phẩm|sản phẩm|màu|chất|chất_liệu|chất_lượng|đóng_gói|hình|hộp|bề_mặt|độ_bền|gói hàng)", flags=re.IGNORECASE),
}

ASPECT_LEAKAGE = {
    "Price": re.compile(r"\b(?:app|ứng_dụng|ứng dụng|phần_mềm|phần mềm|shop|nhân_viên|nhân viên|giao hàng|shipper|vận_chuyển|vận chuyển)\b", flags=re.IGNORECASE),
    "Fashion": re.compile(r"\b(?:app|ứng_dụng|ứng dụng|phần_mềm|phần mềm|shop|nhân_viên|nhân viên|giao hàng|shipper|vận_chuyển|vận chuyển|voucher|mã giảm giá)\b", flags=re.IGNORECASE),
    "Electronics": re.compile(r"\b(?:app|ứng_dụng|ứng dụng|phần_mềm|phần mềm|shop|nhân_viên|nhân viên|giao hàng|shipper|vận_chuyển|vận chuyển|voucher|mã giảm giá)\b", flags=re.IGNORECASE),
    "General": re.compile(r"\b(?:app|ứng_dụng|ứng dụng|phần_mềm|phần mềm|shop|nhân_viên|nhân viên|giao hàng|shipper|vận_chuyển|vận chuyển)\b", flags=re.IGNORECASE),
}


def count_tokens(text: str) -> int:
    return len(re.findall(r"\S+", text))


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_clause_text(text: str) -> str:
    return normalize_spaces(text).strip(" ,.;:!?-")


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
    if not trimmed or text[new_start:new_end] != trimmed:
        return None, "offset_mismatch"

    updated = dict(opinion)
    updated["target"] = trimmed
    updated["start"] = new_start
    updated["end"] = new_end
    return updated, None


def clause_bounds(text: str, start: int, end: int) -> tuple[int, int] | None:
    separators = [0, len(text)]
    for match in re.finditer(CLAUSE_SEPARATORS, text):
        separators.extend([match.start(), match.end()])
    for match in re.finditer(CLAUSE_BREAKERS, text, flags=re.IGNORECASE):
        separators.extend([match.start(), match.end()])
    left = max(point for point in separators if point <= start)
    right = min(point for point in separators if point >= end)
    if right <= left:
        return None
    return left, right


def remap_target(clause: str, target: str, approx_start: int) -> tuple[int, int] | None:
    matches = [match.start() for match in re.finditer(re.escape(target), clause)]
    if not matches:
        return None
    best = min(matches, key=lambda pos: abs(pos - approx_start))
    return best, best + len(target)


def aspect_fingerprint(text: str) -> str:
    lowered = re.sub(r"[^\w\s_]+", " ", text.lower())
    lowered = normalize_spaces(lowered)
    return " ".join(lowered.split()[:8])


def sentiment_cue_ok(clause: str, sentiment: int) -> bool:
    lowered = clause.lower()
    has_pos = bool(POSITIVE_CUES.search(lowered))
    has_neg = bool(NEGATIVE_CUES.search(lowered))
    if sentiment == 1:
        return has_pos and not has_neg
    if sentiment == 0:
        return has_neg and not has_pos
    return False


def snippet_quality_ok(clause: str, opinion: dict) -> bool:
    if count_tokens(clause) < MIN_TOKENS or count_tokens(clause) > MAX_TOKENS:
        return False
    if opinion["sentiment"] not in {0, 1}:
        return False
    if not sentiment_cue_ok(clause, opinion["sentiment"]):
        return False
    pattern = ASPECT_PATTERNS.get(opinion["aspect"])
    if pattern is None or not pattern.search(clause):
        return False
    leakage = ASPECT_LEAKAGE.get(opinion["aspect"])
    if leakage is not None and leakage.search(clause):
        return False
    return True


def build_snippet(record: dict, opinions: list[dict], opinion: dict, line_no: int) -> dict | None:
    bounds = clause_bounds(record["text"], opinion["start"], opinion["end"])
    if bounds is None:
        return None
    left, right = bounds
    opinions_in_clause = [other for other in opinions if max(left, other["start"]) < min(right, other["end"])]
    if len(opinions_in_clause) != 1:
        return None
    raw_clause = record["text"][left:right]
    stripped_left = len(raw_clause) - len(raw_clause.lstrip())
    clause = clean_clause_text(raw_clause)
    if not clause:
        return None
    mapped = remap_target(clause, opinion["target"], opinion["start"] - left - stripped_left)
    if mapped is None:
        return None
    local_start, local_end = mapped
    if clause[local_start:local_end] != opinion["target"]:
        return None
    if not snippet_quality_ok(clause, opinion):
        return None
    return {
        "text": clause,
        "target": opinion["target"],
        "start": local_start,
        "end": local_end,
        "aspect": opinion["aspect"],
        "sentiment": opinion["sentiment"],
        "source_line": line_no,
        "source_key": f"{line_no}|{opinion['aspect']}|{opinion['sentiment']}|{opinion['target']}|{clause}",
        "clause_key": f"{opinion['aspect']}|{opinion['sentiment']}|{opinion['target']}|{clause.lower()}",
        "fingerprint": aspect_fingerprint(clause),
    }


def maybe_lower_first(text: str) -> str:
    if not text:
        return text
    if len(text) > 1 and text[1].isupper():
        return text
    return text[:1].lower() + text[1:]


def maybe_upper_first(text: str) -> str:
    if not text:
        return text
    return text[:1].upper() + text[1:]


def compose_record(left: dict, right: dict, connector: str) -> dict | None:
    left_text = clean_clause_text(left["text"])
    right_text = clean_clause_text(right["text"])
    if connector.startswith("."):
        text = maybe_upper_first(left_text) + connector + maybe_upper_first(right_text)
        right_clause = maybe_upper_first(right_text)
    else:
        text = maybe_upper_first(left_text) + connector + maybe_lower_first(right_text)
        right_clause = maybe_lower_first(right_text)
    prefix = len(text) - len(right_clause)
    mapped_right = remap_target(right_clause, right["target"], right["start"])
    if mapped_right is None:
        return None
    right_start = prefix + mapped_right[0]
    right_end = prefix + mapped_right[1]
    if text[left["start"]:left["end"]] != left["target"]:
        return None
    if text[right_start:right_end] != right["target"]:
        return None
    return {
        "text": text,
        "opinions": [
            {"target": left["target"], "aspect": left["aspect"], "sentiment": left["sentiment"], "start": left["start"], "end": left["end"]},
            {"target": right["target"], "aspect": right["aspect"], "sentiment": right["sentiment"], "start": right_start, "end": right_end},
        ],
        "global_sentiment": 2,
    }


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            raw_line = raw_line.strip()
            if raw_line:
                rows.append(json.loads(raw_line))
    return rows


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records), encoding="utf-8")


def dataset_summary(records: list[dict]) -> dict:
    aspect_counter = Counter()
    contrast_counter = Counter()
    for record in records:
        ops = record.get("opinions", [])
        sentiments = {op.get("sentiment") for op in ops}
        for op in ops:
            aspect_counter[op.get("aspect")] += 1
        if 0 in sentiments and 1 in sentiments and len(ops) == 2:
            left, right = ops
            contrast_counter[f"{left['aspect']}_{left['sentiment']}__{right['aspect']}_{right['sentiment']}"] += 1
    return {
        "records": len(records),
        "opinions": sum(len(record.get("opinions", [])) for record in records),
        "aspect_counter": dict(sorted(aspect_counter.items())),
        "contrast_counter": dict(sorted(contrast_counter.items())),
    }


def main() -> int:
    rng = random.Random(SEED)
    source_pools: dict[tuple[str, int], list[dict]] = defaultdict(list)
    stats = Counter()
    existing_rows = read_jsonl(BASE_FINAL_FILE)
    existing_texts = {row["text"] for row in existing_rows}

    for line_no, record in enumerate(read_jsonl(INPUT_FILE), 1):
        opinions = []
        for opinion in record.get("opinions", []):
            normalized, error = normalize_target(record.get("text", ""), opinion)
            if error or normalized is None:
                stats["invalid_opinions_skipped"] += 1
                continue
            opinions.append(normalized)
        if not opinions:
            continue
        normalized_record = dict(record)
        normalized_record["opinions"] = opinions
        for opinion in opinions:
            if opinion["aspect"] not in {"Fashion", "Electronics", "General", "Price"}:
                continue
            snippet = build_snippet(normalized_record, opinions, opinion, line_no)
            if snippet is None:
                stats["snippet_candidates_skipped"] += 1
                continue
            source_pools[(snippet["aspect"], snippet["sentiment"])].append(snippet)

    for key, pool in list(source_pools.items()):
        deduped = []
        seen = set()
        for snippet in pool:
            if snippet["clause_key"] in seen:
                continue
            seen.add(snippet["clause_key"])
            deduped.append(snippet)
        rng.shuffle(deduped)
        source_pools[key] = deduped

    synthetic_records = []
    synthetic_texts = set()
    pair_counts = Counter()
    snippet_usage = Counter()
    clause_usage = Counter()
    fingerprint_usage = Counter()

    for aspect_a, aspect_b in TARGET_PAIRS:
        directions = [((aspect_a, 1), (aspect_b, 0)), ((aspect_a, 0), (aspect_b, 1))]
        for left_key, right_key in directions:
            generated = 0
            left_pool = list(source_pools.get(left_key, []))
            right_pool = list(source_pools.get(right_key, []))
            left_pool.sort(key=lambda item: (clause_usage[item['clause_key']], fingerprint_usage[item['fingerprint']], snippet_usage[item['source_key']]))
            right_pool.sort(key=lambda item: (clause_usage[item['clause_key']], fingerprint_usage[item['fingerprint']], snippet_usage[item['source_key']]))
            for left in left_pool:
                if generated >= MAX_PER_DIRECTION:
                    break
                if snippet_usage[left['source_key']] >= MAX_SNIPPET_REUSE or clause_usage[left['clause_key']] >= MAX_CLAUSE_REUSE:
                    continue
                for right in right_pool:
                    if generated >= MAX_PER_DIRECTION:
                        break
                    if left['source_line'] == right['source_line']:
                        continue
                    if left['fingerprint'] == right['fingerprint']:
                        continue
                    if snippet_usage[right['source_key']] >= MAX_SNIPPET_REUSE or clause_usage[right['clause_key']] >= MAX_CLAUSE_REUSE:
                        continue
                    synthetic = compose_record(left, right, rng.choice(CONNECTORS))
                    if synthetic is None:
                        continue
                    if synthetic['text'] in existing_texts or synthetic['text'] in synthetic_texts:
                        continue
                    if count_tokens(synthetic['text']) > 34:
                        continue
                    synthetic_records.append(synthetic)
                    synthetic_texts.add(synthetic['text'])
                    snippet_usage[left['source_key']] += 1
                    snippet_usage[right['source_key']] += 1
                    clause_usage[left['clause_key']] += 1
                    clause_usage[right['clause_key']] += 1
                    fingerprint_usage[left['fingerprint']] += 1
                    fingerprint_usage[right['fingerprint']] += 1
                    pair_counts[f"{left_key[0]}_{left_key[1]}__{right_key[0]}_{right_key[1]}"] += 1
                    generated += 1

    rng.shuffle(synthetic_records)
    final_records = existing_rows + synthetic_records
    rng.shuffle(final_records)

    write_jsonl(SYNTHETIC_FILE, synthetic_records)
    write_jsonl(FINAL_FILE, final_records)

    report = {
        "input_file": str(INPUT_FILE),
        "base_final_file": str(BASE_FINAL_FILE),
        "synthetic_file": str(SYNTHETIC_FILE),
        "final_file": str(FINAL_FILE),
        "source_pool_sizes": {f"{aspect}_{sentiment}": len(pool) for (aspect, sentiment), pool in sorted(source_pools.items())},
        "pair_counts": dict(sorted(pair_counts.items())),
        "stats": dict(sorted(stats.items())),
        "synthetic_summary": dataset_summary(synthetic_records),
        "final_summary": dataset_summary(final_records),
    }
    REPORT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())