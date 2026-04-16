#!/usr/bin/env python3

from __future__ import annotations

import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path


INPUT_FILE = Path("data/processed/train_final_v3.autofixed.jsonl")
PRUNED_FILE = Path("data/processed/train_final_v3.natural_pruned.jsonl")
SYNTHETIC_FILE = Path("data/processed/train_final_v3.synthetic_multi_aspect_natural.jsonl")
FINAL_FILE = Path("data/processed/train_final_v3.curated_augmented_natural.jsonl")
REPORT_FILE = Path("data/processed/train_final_v3.curated_augmented_natural.report.json")

SEED = 42
MIN_TOKENS = 4
MAX_TOKENS = 24
MAX_PER_DIRECTION = 14
MAX_SNIPPET_REUSE = 1
MAX_CLAUSE_REUSE = 1

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

DISALLOWED_TARGETS = {
    "Ship": {"gửi", "ship", "giao"},
    "Price": {"tiền", "giám"},
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

CLAUSE_SEPARATORS = r"[\n.!?;]"
CLAUSE_BREAKERS = r"\b(?:nhưng|tuy_nhiên|tuy nhiên|còn|dù_vậy|dù vậy|mà|song|trái_lại|trái lại)\b"

CONNECTORS = {
    "contrast": [" nhưng ", ". Tuy nhiên, ", "; còn ", ". Còn ", ", nhưng "],
    "support": [" và ", ". Đồng thời, ", ", thêm nữa "],
}

POSITIVE_CUES = re.compile(
    r"\b(?:đẹp|tốt|ổn|ổn_định|mượt|nhanh|tiện|tiện_lợi|hợp_lý|hợp lý|phù_hợp|phù hợp|rẻ|"
    r"nhiệt_tình|nhiệt tình|chu_đáo|chu đáo|tận_tâm|tận tâm|đúng_hẹn|đúng hẹn|trâu|"
    r"chất_lượng|chất lượng|ok|ổn áp)\b",
    flags=re.IGNORECASE,
)
NEGATIVE_CUES = re.compile(
    r"\b(?:lỗi|lag|giật|đơ|chậm|lâu|trễ|tệ|kém|xấu|mỏng|hôi|bẩn|rách|tụt|cao|đắt|mắc|"
    r"không trả_lời|không trả lời|không đúng|sai|thiếu|nhầm|hủy|không phản_hồi|không phản hồi|"
    r"không tốt|quá cao|khó_chịu|khó chịu|ko đc mượt|ko được mượt|không được mượt|"
    r"ko đc ổn|ko được ổn|không được ổn|không mượt|không ổn)\b",
    flags=re.IGNORECASE,
)

ASPECT_LEAKAGE_PATTERNS = {
    "App": re.compile(r"\b(?:shipper|giao hàng|vận_chuyển|vận chuyển|shop|nhân_viên|nhân viên|giá|voucher|mã giảm giá)\b", flags=re.IGNORECASE),
    "Ship": re.compile(r"\b(?:app|ứng_dụng|ứng dụng|phần_mềm|phần mềm|cập_nhật|cập nhật|giá|voucher|nhân_viên|nhân viên|tư_vấn|tư vấn)\b", flags=re.IGNORECASE),
    "Service": re.compile(r"\b(?:app|ứng_dụng|ứng dụng|phần_mềm|phần mềm|cập_nhật|cập nhật|giao hàng|shipper|vận_chuyển|vận chuyển|giá|voucher)\b", flags=re.IGNORECASE),
    "Price": re.compile(r"\b(?:app|ứng_dụng|ứng dụng|phần_mềm|phần mềm|cập_nhật|cập nhật|giao hàng|shipper|vận_chuyển|vận chuyển|shop|nhân_viên|nhân viên|tư_vấn|tư vấn)\b", flags=re.IGNORECASE),
    "Product": re.compile(r"\b(?:app|ứng_dụng|ứng dụng|phần_mềm|phần mềm|cập_nhật|cập nhật|giao hàng|shipper|vận_chuyển|vận chuyển|shop|nhân_viên|nhân viên|tư_vấn|tư vấn|giá|voucher)\b", flags=re.IGNORECASE),
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
    if not trimmed or new_start < 0 or new_end <= new_start or new_end > len(text):
        return None, "invalid_trimmed_target"
    if text[new_start:new_end] != trimmed:
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
    lowered = text.lower()
    lowered = re.sub(r"[^\w\s_]+", " ", lowered)
    lowered = normalize_spaces(lowered)
    tokens = lowered.split()
    return " ".join(tokens[:8])


def target_allowed(opinion: dict) -> bool:
    target = opinion["target"].lower()
    if opinion["aspect"] == "Product" and target in GENERIC_PRODUCT_TARGETS:
        return False
    if target in DISALLOWED_TARGETS.get(opinion["aspect"], set()):
        return False
    return True


def sentiment_cue_ok(clause: str, sentiment: int) -> bool:
    lowered = clause.lower()
    has_pos = bool(POSITIVE_CUES.search(lowered))
    has_neg = bool(NEGATIVE_CUES.search(lowered))
    if sentiment == 1:
        return has_pos and not has_neg
    if sentiment == 0:
        return has_neg and not has_pos
    return False


def has_aspect_leakage(clause: str, opinion: dict) -> bool:
    pattern = ASPECT_LEAKAGE_PATTERNS.get(opinion["aspect"])
    if pattern is None:
        return False
    return bool(pattern.search(clause))


def snippet_quality_ok(clause: str, opinion: dict) -> bool:
    lowered = clause.lower()
    target = opinion["target"].lower()
    if count_tokens(clause) < MIN_TOKENS or count_tokens(clause) > MAX_TOKENS:
        return False
    if not sentiment_cue_ok(clause, opinion["sentiment"]):
        return False
    if has_aspect_leakage(clause, opinion):
        return False
    if opinion["aspect"] == "Ship":
        if not re.search(r"(?:giao|shipper|vận_chuyển|vận chuyển).{0,20}(?:nhanh|đúng_hẹn|đúng hẹn|chậm|lâu|trễ|sai|thiếu|nhầm|không đúng|hoàn|hủy|không gọi)", lowered):
            return False
    if opinion["aspect"] == "Price":
        if not re.search(r"(?:giá|tầm giá|voucher|phí ship|mã giảm giá|tiền).{0,20}(?:rẻ|hợp_lý|hợp lý|phù_hợp|phù hợp|đắt|cao|mắc|ảo)", lowered):
            return False
    if opinion["aspect"] == "Service":
        if not re.search(r"(?:shop|nhân_viên|nhân viên|tư_vấn|tư vấn|phục_vụ|phục vụ|trả_lời|trả lời).{0,20}(?:nhiệt_tình|nhiệt tình|chu_đáo|chu đáo|tận_tâm|tận tâm|tốt|kém|tệ|không trả_lời|không trả lời)", lowered):
            return False
    if opinion["aspect"] == "App":
        if not re.search(r"(?:app|ứng_dụng|ứng dụng|phần_mềm|phần mềm|cập_nhật|cập nhật).{0,20}(?:tốt|ổn|mượt|nhanh|tiện|lỗi|lag|giật|đơ|chậm|không phản_hồi|không phản hồi)", lowered):
            return False
    if opinion["aspect"] == "Product":
        if target in {"pin", "màn hình", "màn_hình", "camera", "máy", "vải", "chất_liệu", "chất liệu", "chất_lượng", "chất lượng", "cáp_sạc", "củ_sạc", "giày", "đường may", "đường_may"}:
            return True
        if re.search(r"(?:pin|màn_hình|màn hình|camera|máy|vải|chất_liệu|chất liệu|chất_lượng|chất lượng|cáp_sạc|củ_sạc|giày|đường may).{0,20}(?:đẹp|tốt|ổn|mượt|trâu|mỏng|xấu|kém|lỗi|tụt|cứng|hôi|bẩn|rách|ẩu)", lowered):
            return True
        return False
    return True


def build_snippet(record: dict, opinions: list[dict], opinion: dict, line_no: int) -> dict | None:
    if opinion.get("sentiment") not in {0, 1}:
        return None
    if not target_allowed(opinion):
        return None
    bounds = clause_bounds(record["text"], opinion["start"], opinion["end"])
    if bounds is None:
        return None
    left, right = bounds
    # keep only clauses with a single labelled opinion to reduce semantic leakage
    opinions_in_clause = [
        other for other in opinions
        if max(left, other["start"]) < min(right, other["end"])
    ]
    if len(opinions_in_clause) != 1:
        return None

    raw_clause = record["text"][left:right]
    stripped_left = len(raw_clause) - len(raw_clause.lstrip())
    clause = clean_clause_text(raw_clause)
    if not clause:
        return None
    approx_local_start = opinion["start"] - left - stripped_left
    mapped = remap_target(clause, opinion["target"], approx_local_start)
    if mapped is None:
        return None
    local_start, local_end = mapped
    rebuilt = clause[local_start:local_end]
    if rebuilt != opinion["target"]:
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
    if left["aspect"] == right["aspect"]:
        return None
    left_text = clean_clause_text(left["text"])
    right_text = clean_clause_text(right["text"])
    if not left_text or not right_text:
        return None

    if connector.startswith("."):
        text = maybe_upper_first(left_text) + connector + maybe_upper_first(right_text)
        right_prefix_len = len(maybe_upper_first(left_text) + connector)
        right_target = right["target"]
        right_clause = maybe_upper_first(right_text)
    else:
        text = maybe_upper_first(left_text) + connector + maybe_lower_first(right_text)
        right_prefix_len = len(maybe_upper_first(left_text) + connector)
        right_target = right["target"]
        right_clause = maybe_lower_first(right_text)

    left_start = left["start"]
    left_end = left["end"]
    mapped_right = remap_target(right_clause, right_target, right["start"])
    if mapped_right is None:
        return None
    right_start = right_prefix_len + mapped_right[0]
    right_end = right_prefix_len + mapped_right[1]
    if text[left_start:left_end] != left["target"] or text[right_start:right_end] != right_target:
        return None

    opinions = [
        {
            "target": left["target"],
            "aspect": left["aspect"],
            "sentiment": left["sentiment"],
            "start": left_start,
            "end": left_end,
        },
        {
            "target": right_target,
            "aspect": right["aspect"],
            "sentiment": right["sentiment"],
            "start": right_start,
            "end": right_end,
        },
    ]
    return {
        "text": text,
        "opinions": opinions,
        "global_sentiment": 2,
    }


def dataset_summary(records: list[dict]) -> dict:
    aspect_counter = Counter()
    num_ops_counter = Counter()
    multi_aspect = 0
    contrast = 0
    for record in records:
        opinions = record.get("opinions", [])
        num_ops_counter[len(opinions)] += 1
        aspects = {op.get("aspect") for op in opinions}
        sentiments = {op.get("sentiment") for op in opinions}
        if len(aspects) >= 2:
            multi_aspect += 1
        if 0 in sentiments and 1 in sentiments:
            contrast += 1
        for opinion in opinions:
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
            raw_opinions = record.get("opinions", [])
            normalized_opinions = []
            for opinion in raw_opinions:
                normalized, error = normalize_target(text, opinion)
                if error or normalized is None:
                    stats["invalid_opinions_skipped"] += 1
                    continue
                if normalized["aspect"] == "Product" and normalized["target"].lower() in GENERIC_PRODUCT_TARGETS:
                    stats["pruned_generic_product_targets"] += 1
                    continue
                normalized_opinions.append(normalized)

            if not normalized_opinions:
                stats["dropped_empty_after_prune"] += 1
                continue

            updated = dict(record)
            updated["opinions"] = normalized_opinions
            pruned_records.append(updated)
            existing_texts.add(updated["text"])

            for opinion in normalized_opinions:
                snippet = build_snippet(updated, normalized_opinions, opinion, line_no)
                if snippet is None:
                    stats["snippet_candidates_skipped"] += 1
                    continue
                source_pools[(snippet["aspect"], snippet["sentiment"])].append(snippet)

    for key, pool in list(source_pools.items()):
        deduped = []
        seen_clause_keys = set()
        for snippet in pool:
            if snippet["clause_key"] in seen_clause_keys:
                continue
            seen_clause_keys.add(snippet["clause_key"])
            deduped.append(snippet)
        source_pools[key] = deduped

    for key in source_pools:
        rng.shuffle(source_pools[key])

    synthetic_records = []
    synthetic_texts = set()
    pair_counts = Counter()
    snippet_usage = Counter()
    clause_usage = Counter()
    fingerprint_usage = Counter()

    for aspect_a, aspect_b in ASPECT_PAIRS:
        directions = [
            ((aspect_a, 1), (aspect_b, 0)),
            ((aspect_a, 0), (aspect_b, 1)),
        ]
        for left_key, right_key in directions:
            generated = 0
            left_pool = list(source_pools.get(left_key, []))
            right_pool = list(source_pools.get(right_key, []))
            left_pool.sort(key=lambda item: (clause_usage[item["clause_key"]], fingerprint_usage[item["fingerprint"]], snippet_usage[item["source_key"]]))
            right_pool.sort(key=lambda item: (clause_usage[item["clause_key"]], fingerprint_usage[item["fingerprint"]], snippet_usage[item["source_key"]]))

            for left in left_pool:
                if generated >= MAX_PER_DIRECTION:
                    break
                if snippet_usage[left["source_key"]] >= MAX_SNIPPET_REUSE:
                    continue
                if clause_usage[left["clause_key"]] >= MAX_CLAUSE_REUSE:
                    continue
                for right in right_pool:
                    if generated >= MAX_PER_DIRECTION:
                        break
                    if left["source_line"] == right["source_line"]:
                        continue
                    if left["fingerprint"] == right["fingerprint"]:
                        continue
                    if snippet_usage[right["source_key"]] >= MAX_SNIPPET_REUSE:
                        continue
                    if clause_usage[right["clause_key"]] >= MAX_CLAUSE_REUSE:
                        continue
                    connector = rng.choice(CONNECTORS["contrast"])
                    synthetic = compose_record(left, right, connector)
                    if synthetic is None:
                        continue
                    text = synthetic["text"]
                    if text in existing_texts or text in synthetic_texts:
                        continue
                    if count_tokens(text) > 36:
                        continue

                    synthetic_records.append(synthetic)
                    synthetic_texts.add(text)
                    snippet_usage[left["source_key"]] += 1
                    snippet_usage[right["source_key"]] += 1
                    clause_usage[left["clause_key"]] += 1
                    clause_usage[right["clause_key"]] += 1
                    fingerprint_usage[left["fingerprint"]] += 1
                    fingerprint_usage[right["fingerprint"]] += 1
                    pair_counts[(left_key, right_key)] += 1
                    generated += 1

    rng.shuffle(synthetic_records)
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