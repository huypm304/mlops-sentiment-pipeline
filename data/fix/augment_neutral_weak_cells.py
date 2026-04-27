#!/usr/bin/env python3

from __future__ import annotations

import json
import math
import random
import re
from collections import Counter, defaultdict
from pathlib import Path


BASE_FILE = Path("data/processed/triplet_data_absolutely_clean.jsonl")
AUGMENT_ONLY_FILE = Path("data/processed/triplet_data_balanced_neu_augment_only.jsonl")
OUTPUT_FILE = Path("data/processed/triplet_data_balanced_neu.jsonl")
REPORT_FILE = Path("data/processed/triplet_data_balanced_neu.report.json")

SOURCE_FILES = [
    Path("data/processed/data_train_v8_aste.modifier_auto_merged.qa_fixed.jsonl"),
    Path("data/processed/data_train_v8_aste.modifier_force_auto_merged.qa_fixed.jsonl"),
    Path("data/processed/data_train_v8_aste.modifier_merged.jsonl"),
    Path("data/processed/data_train_v8_aste.jsonl"),
]

SEED = 42
SIMILARITY_THRESHOLD = 0.30
TARGET_RATIO = 1.5
TARGET_CELLS = [("Fashion", 2), ("Electronics", 2)]

SAFE_NEU_OPINIONS = {
    "Fashion": ["bình_thường", "tạm được", "được", "tạm ổn", "ổn"],
    "Electronics": ["bình_thường", "tạm được", "được", "tạm ổn", "ổn"],
}

NEGATIVE_GUARDS = re.compile(
    r"\b(?:tệ|xấu|kém|lỗi|lag|giật|đơ|chậm|lâu|trễ|rách|bẩn|hôi|nhỏ|chật|rộng|mỏng|yếu|hỏng|không\s+được|quá\s+đắt)\b",
    flags=re.IGNORECASE,
)
POSITIVE_GUARDS = re.compile(
    r"\b(?:đẹp|xịn|tuyệt|hoàn_hảo|hoàn hảo|xuất_sắc|xuất sắc|mượt|nhanh|quá\s+ổn|rất\s+ổn|cực\s+ổn|trâu|siêu\s+tốt)\b",
    flags=re.IGNORECASE,
)

FASHION_INTROS = [
    "mặc vài buổi thì thấy",
    "nếu xét cho nhu_cầu mặc hằng ngày thì",
    "xét riêng phần dùng bình_thường thì",
    "sau khi thử qua mấy lần thì",
    "nếu chỉ dùng cho sinh_hoạt cơ_bản thì",
    "nhìn chung với nhu_cầu mặc thường ngày thì",
    "trải nghiệm nhanh mấy hôm nay thì",
    "nếu không quá khó_tính khi mặc thì",
    "đánh_giá công_bằng mà nói thì",
    "xét trong tầm dùng cơ_bản thì",
]

FASHION_BODIES = [
    "{target} nhìn chung {opinion}, không quá nổi bật nhưng cũng không có gì phải lăn_tăn thêm.",
    "{target} đang ở mức {opinion}, dùng cho nhu_cầu cơ_bản là vừa.",
    "{target} cho cảm_giác {opinion}, mặc hằng ngày thì vẫn ổn định.",
    "{target} hiện tại ở mức {opinion}, chưa có điểm gì quá khác so với kỳ_vọng ban đầu.",
    "{target} theo cảm_nhận cá_nhân là {opinion}, giữ nguyên như vậy cũng được.",
    "{target} đánh_giá nhanh là {opinion}, mặc đi làm hay đi học đều không gây khó_chịu.",
    "{target} ở mức {opinion}, không quá khác biệt so với mặt_bằng chung.",
    "{target} lên form khá {opinion}, chưa tới mức phải chỉnh sửa gì thêm.",
    "{target} tổng_thể là {opinion}, dùng theo kiểu đơn_giản thì hợp.",
    "{target} hiện cho cảm_giác {opinion}, mặc thường ngày vẫn đáp_ứng được.",
]

FASHION_TAILS = [
    "Mình giữ nguyên như vậy cũng thấy hợp với nhu_cầu hiện tại.",
    "Nếu dùng theo kiểu đơn_giản thì không có gì phải suy_nghĩ thêm.",
    "Với nhu_cầu cơ_bản thì mức này là chấp_nhận được.",
    "Mình chưa thấy cần đổi sang lựa_chọn khác ngay lúc này.",
    "Nhìn tổng_thể thì đây là kiểu dễ dùng mỗi ngày.",
    "Cảm_nhận chung là dùng ổn theo cách thông_thường.",
    "Với mục_đích mặc đều đặn thì như vậy là vừa sức.",
    "Hiện tại mình thấy giữ mức này là đủ dùng.",
    "Nếu không đặt kỳ_vọng cao thì phần này khá dễ chấp_nhận.",
    "Nhìn theo hướng thực_dụng thì như vậy là ổn định rồi.",
    "Tổng_thể mình thấy phần này chưa tạo cảm_giác phải chỉnh sửa thêm.",
    "Mình đánh_giá đây là mức trung_tính khá dễ chịu.",
    "Nếu mặc trong lịch sinh_hoạt bình_thường thì vẫn hợp lý.",
    "Xét cho nhu_cầu cơ_bản thì như vậy là vừa tầm.",
    "Mình chưa có lý_do rõ ràng để phàn_nàn thêm về phần này.",
]

ELECTRONICS_INTROS = [
    "dùng mấy hôm thì thấy",
    "nếu xét cho nhu_cầu dùng cơ_bản thì",
    "trải nghiệm nhanh một thời_gian ngắn thì",
    "với nhu_cầu sử_dụng bình_thường thì",
    "sau khi xài thử mấy ngày thì",
    "nhìn chung khi dùng hằng ngày thì",
    "nếu không đòi_hỏi quá cao thì",
    "xét trong tầm sử_dụng cơ_bản thì",
    "đánh_giá ngắn_gọn mà nói thì",
    "nếu dùng cho tác_vụ thông_thường thì",
]

ELECTRONICS_BODIES = [
    "{target} ở mức {opinion}, dùng hằng ngày không quá nổi bật nhưng cũng không gây phiền.",
    "{target} hiện tại {opinion}, chưa có điểm gì quá khác biệt khi sử_dụng thường ngày.",
    "{target} nhìn chung {opinion}, đáp_ứng nhu_cầu cơ_bản là ổn.",
    "{target} cho cảm_giác {opinion}, dùng trong công_việc thường ngày thì không có gì quá đáng ngại.",
    "{target} đang ở mức {opinion}, giữ nguyên như vậy cũng tạm được.",
    "{target} theo đánh_giá nhanh là {opinion}, vẫn dùng được cho nhu_cầu bình_thường.",
    "{target} ở mức {opinion}, chưa tạo cảm_giác quá khác so với mặt_bằng chung.",
    "{target} hiện cho trải_nghiệm {opinion}, chưa thấy có điểm gì quá nổi trội hay quá bất_ổn.",
    "{target} nhìn sơ thì {opinion}, phục_vụ nhu_cầu cơ_bản là đủ.",
    "{target} hiện vẫn {opinion}, dùng theo kiểu đơn_giản thì chấp_nhận được.",
]

ELECTRONICS_TAILS = [
    "Nếu chỉ dùng cho tác_vụ cơ_bản thì mình thấy mức này là đủ.",
    "Tổng_thể hiện tại mình chưa thấy cần can_thiệp gì thêm.",
    "Với nhu_cầu thường ngày thì như vậy là chấp_nhận được.",
    "Mình thấy giữ trạng_thái này để dùng tiếp cũng ổn.",
    "Nếu không đặt kỳ_vọng quá cao thì phần này không thành vấn_đề.",
    "Nhìn theo góc_độ thực_dụng thì mức này khá vừa.",
    "Cho nhu_cầu thông_thường thì chưa có gì làm mình phải đổi ý.",
    "Mình đánh_giá đây là trạng_thái trung_tính và dễ dùng.",
    "Xét trong quá_trình dùng cơ_bản thì phần này đủ đáp_ứng.",
    "Nhìn chung mình vẫn dùng tiếp bình_thường với mức này.",
    "Nếu chỉ để phục_vụ công_việc cơ_bản thì chưa có gì đáng lo.",
    "Ở mặt bằng hiện tại thì mình thấy mức này khá cân.",
    "Mình chưa gặp lý_do rõ ràng để phải thay đổi phần này.",
    "Xét về dùng lâu hơn thì hiện tại mình vẫn thấy ổn để tiếp tục.",
    "Cho nhu_cầu phổ_thông thì giữ như vậy cũng hợp lý.",
]


def normalize(text: str) -> str:
    text = text.lower().replace("_", " ")
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def token_ngrams(text: str, n: int = 3) -> set[tuple[str, ...]]:
    words = normalize(text).split()
    if not words:
        return set()
    if len(words) < n:
        return {tuple(words)}
    return {tuple(words[index:index + n]) for index in range(len(words) - n + 1)}


def trigram_jaccard(text_a: str, text_b: str) -> float:
    grams_a = token_ngrams(text_a)
    grams_b = token_ngrams(text_b)
    if not grams_a and not grams_b:
        return 1.0
    if not grams_a or not grams_b:
        return 0.0
    return len(grams_a & grams_b) / len(grams_a | grams_b)


def trigram_jaccard_sets(grams_a: set[tuple[str, ...]], grams_b: set[tuple[str, ...]]) -> float:
    if not grams_a and not grams_b:
        return 1.0
    if not grams_a or not grams_b:
        return 0.0
    return len(grams_a & grams_b) / len(grams_a | grams_b)


def read_jsonl(path: Path) -> list[dict]:
    records = []
    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            raw_line = raw_line.strip()
            if raw_line:
                records.append(json.loads(raw_line))
    return records


def write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def max_similarity(text: str, existing_texts: list[str]) -> float:
    best = 0.0
    for existing in existing_texts:
        best = max(best, trigram_jaccard(text, existing))
        if best > SIMILARITY_THRESHOLD:
            return best
    return best


def max_similarity_signature(signature: set[tuple[str, ...]], existing_signatures: list[set[tuple[str, ...]]]) -> float:
    best = 0.0
    for existing in existing_signatures:
        best = max(best, trigram_jaccard_sets(signature, existing))
        if best > SIMILARITY_THRESHOLD:
            return best
    return best


def make_triplet_record(text: str, aspect: str, target: str, opinion: str) -> dict | None:
    target_start = text.find(target)
    if target_start == -1:
        return None
    target_end = target_start + len(target)
    opinion_start = text.find(opinion, target_end)
    if opinion_start == -1:
        opinion_start = text.find(opinion)
    if opinion_start == -1:
        return None
    opinion_end = opinion_start + len(opinion)
    if not (target_end <= opinion_start or opinion_end <= target_start):
        return None
    return {
        "text": text,
        "triplets": [
            {
                "aspect": aspect,
                "target": target,
                "target_span": [target_start, target_end],
                "opinion": opinion,
                "opinion_span": [opinion_start, opinion_end],
                "aspect_opinion_pair": f"{target} {opinion}",
                "sentiment": 2,
            }
        ],
    }


def build_base_state(records: list[dict]) -> tuple[dict, dict, dict, list[dict]]:
    counts = defaultdict(Counter)
    target_pool = defaultdict(Counter)
    existing_texts = defaultdict(list)
    valid_records = []

    for record in records:
        valid_records.append(record)
        text = record.get("text", "")
        for triplet in record.get("triplets", []):
            aspect = triplet.get("aspect")
            sentiment = triplet.get("sentiment")
            counts[aspect][sentiment] += 1
            target = triplet.get("target")
            if isinstance(target, str) and target.strip():
                target_pool[aspect][target] += 1
            if (aspect, sentiment) in TARGET_CELLS:
                existing_texts[(aspect, sentiment)].append(text)

    return counts, target_pool, existing_texts, valid_records


def required_additions(counts: dict) -> dict:
    additions = {}
    for aspect, sentiment in TARGET_CELLS:
        current = counts[aspect][sentiment]
        max_count = max(counts[aspect][0], counts[aspect][1], counts[aspect][2])
        target_min = math.ceil(max_count / TARGET_RATIO)
        additions[(aspect, sentiment)] = max(0, target_min - current)
    return additions


def is_safe_source_record(record: dict) -> bool:
    text = record.get("text", "")
    if not text or len(normalize(text).split()) < 6:
        return False
    if len(record.get("triplets", [])) != 1:
        return False
    if NEGATIVE_GUARDS.search(text) or POSITIVE_GUARDS.search(text):
        return False
    return True


def collect_source_candidates(existing_texts: dict, existing_signatures: dict) -> dict:
    candidates = defaultdict(list)
    seen = {key: {normalize(text) for text in texts} for key, texts in existing_texts.items()}

    for path in SOURCE_FILES:
        if not path.exists():
            continue
        for record in read_jsonl(path):
            text = record.get("text", "")
            for triplet in record.get("triplets", []):
                aspect = triplet.get("aspect")
                sentiment = triplet.get("sentiment")
                key = (aspect, sentiment)
                if key not in TARGET_CELLS:
                    continue
                target = triplet.get("target")
                opinion = triplet.get("opinion")
                if opinion not in SAFE_NEU_OPINIONS.get(aspect, []):
                    continue
                if not isinstance(target, str) or not target.strip():
                    continue
                if triplet.get("opinion_span") == [-1, -1]:
                    continue
                if not is_safe_source_record(record):
                    continue
                norm = normalize(text)
                signature = token_ngrams(text)
                if norm in seen[key]:
                    continue
                if max_similarity_signature(signature, existing_signatures[key]) > SIMILARITY_THRESHOLD:
                    continue
                seen[key].add(norm)
                candidates[key].append(record)

    return candidates


def generate_synthetic_records(
    aspect: str,
    need: int,
    target_counts: Counter,
    existing_texts: list[str],
    existing_signatures: list[set[tuple[str, ...]]],
    rng: random.Random,
) -> list[dict]:
    intros = FASHION_INTROS if aspect == "Fashion" else ELECTRONICS_INTROS
    bodies = FASHION_BODIES if aspect == "Fashion" else ELECTRONICS_BODIES
    tails = FASHION_TAILS if aspect == "Fashion" else ELECTRONICS_TAILS
    opinions = SAFE_NEU_OPINIONS[aspect][:]
    targets = [target for target, _count in target_counts.most_common() if target and len(normalize(target).split()) <= 4]
    if not targets:
        return []

    generated = []
    local_texts = list(existing_texts)
    target_usage = Counter()
    attempts = 0
    max_attempts = max(need * 120, 1000)

    while len(generated) < need and attempts < max_attempts:
        attempts += 1
        least_used = min(target_usage.get(target, 0) for target in targets)
        candidate_targets = [target for target in targets if target_usage.get(target, 0) == least_used]
        target = rng.choice(candidate_targets)
        opinion = rng.choice(opinions)
        intro = rng.choice(intros)
        body = rng.choice(bodies)
        tail = rng.choice(tails)
        pattern = rng.randint(0, 2)
        if pattern == 0:
            text = f"{intro} {body.format(target=target, opinion=opinion)} {tail}"
        elif pattern == 1:
            text = f"{tail} {intro} {body.format(target=target, opinion=opinion)}"
        else:
            text = f"{intro} {body.format(target=target, opinion=opinion)} {tail} Nhìn vậy là đủ cho nhu_cầu bình_thường."
        text = re.sub(r"\s+", " ", text).strip()
        signature = token_ngrams(text)
        if max_similarity_signature(signature, existing_signatures) > SIMILARITY_THRESHOLD:
            continue
        record = make_triplet_record(text, aspect, target, opinion)
        if record is None:
            continue
        generated.append(record)
        local_texts.append(text)
        existing_signatures.append(signature)
        target_usage[target] += 1

    return generated


def summarize(records: list[dict]) -> dict:
    counts = defaultdict(Counter)
    for record in records:
        for triplet in record.get("triplets", []):
            counts[triplet.get("aspect")][triplet.get("sentiment")] += 1

    summary = {}
    for aspect, _sentiment in TARGET_CELLS:
        aspect_counts = counts[aspect]
        maximum = max(aspect_counts[0], aspect_counts[1], aspect_counts[2])
        minimum = min(aspect_counts[0], aspect_counts[1], aspect_counts[2])
        ratio = float("inf") if minimum == 0 and maximum > 0 else (maximum / minimum if minimum else 1.0)
        summary[aspect] = {
            "Neg": aspect_counts[0],
            "Pos": aspect_counts[1],
            "Neu": aspect_counts[2],
            "ratio": ratio,
        }
    return summary


def main() -> None:
    rng = random.Random(SEED)
    base_records = read_jsonl(BASE_FILE)
    counts, target_pool, existing_texts, valid_records = build_base_state(base_records)
    additions_needed = required_additions(counts)
    existing_signatures = {key: [token_ngrams(text) for text in texts] for key, texts in existing_texts.items()}
    source_candidates = collect_source_candidates(existing_texts, existing_signatures)

    augment_records = []
    cell_report = {}

    for aspect, sentiment in TARGET_CELLS:
        key = (aspect, sentiment)
        need = additions_needed[key]
        source_taken = source_candidates.get(key, [])[:need]
        augment_records.extend(source_taken)
        existing_texts[key].extend(record["text"] for record in source_taken)
        existing_signatures[key].extend(token_ngrams(record["text"]) for record in source_taken)

        remaining = max(0, need - len(source_taken))
        synthetic = generate_synthetic_records(
            aspect,
            remaining,
            target_pool[aspect],
            existing_texts[key],
            existing_signatures[key],
            rng,
        )
        augment_records.extend(synthetic)
        existing_texts[key].extend(record["text"] for record in synthetic)

        cell_report[f"{aspect}-Neu"] = {
            "needed": need,
            "source_candidates_available": len(source_candidates.get(key, [])),
            "source_used": len(source_taken),
            "synthetic_used": len(synthetic),
            "generated_total": len(source_taken) + len(synthetic),
        }

    output_records = valid_records + augment_records
    write_jsonl(AUGMENT_ONLY_FILE, augment_records)
    write_jsonl(OUTPUT_FILE, output_records)

    report = {
        "seed": SEED,
        "similarity_metric": "token_trigram_jaccard",
        "similarity_threshold": SIMILARITY_THRESHOLD,
        "target_ratio": TARGET_RATIO,
        "input_records": len(valid_records),
        "augment_records": len(augment_records),
        "output_records": len(output_records),
        "cell_report": cell_report,
        "before": summarize(valid_records),
        "after": summarize(output_records),
    }
    REPORT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()