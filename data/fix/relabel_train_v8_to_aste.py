#!/usr/bin/env python3

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


INPUT_FILE = Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/data_train_v8.jsonl")
OUTPUT_FILE = Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/data_train_v8_aste.jsonl")
REVIEW_FILE = Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/data_train_v8_aste.review.jsonl")
REPORT_FILE = Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/data_train_v8_aste.report.json")
GROUPED_REVIEW_FILES = {
    "khong_co": Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/data_train_v8_aste.review.khong_co.jsonl"),
    "bi_loi": Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/data_train_v8_aste.review.bi_loi.jsonl"),
    "hoi_adj": Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/data_train_v8_aste.review.hoi_adj.jsonl"),
    "qua_adj": Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/data_train_v8_aste.review.qua_adj.jsonl"),
    "other": Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/data_train_v8_aste.review.other.jsonl"),
}

BOUNDARY_PATTERN = re.compile(
    r"[,.;!?\n]|\b(?:nhưng|tuy_nhiên|tuy|bù_lại|trái_lại|song|cơ_mà|còn)\b",
    re.IGNORECASE,
)
TOKEN_PATTERN = re.compile(r"\S+")
STRIP_CHARS = " \t\r\n.,;:!?()[]{}\"'“”‘’👍🙂☺️"
ADJACENT_CUES = {
    0: {"không", "chưa", "bị", "tệ", "xấu", "lỗi", "chậm", "lag", "đơ", "thiếu", "sai", "trễ", "lâu", "đéo", "méo", "rách", "hỏng", "dính", "ẩu"},
    1: {"đẹp", "tốt", "nhanh", "mượt", "mịn", "ưng", "hài_lòng", "nhiệt_tình", "đúng", "chuẩn", "tuyệt", "y", "cẩn_thận", "thân_thiện", "hời", "tư_vấn", "phục_vụ", "có_tâm", "giữ_lời"},
    2: {"được", "ổn", "ok", "oke", "tạm", "bình_thường", "vừa", "cũng", "không", "chấp_nhận", "tư_vấn", "phục_vụ", "còn", "nguyên"},
}
ALL_CUE_TOKENS = set().union(*ADJACENT_CUES.values())
EASY_GROUP_PATTERNS = {
    "khong_co": re.compile(r"(?:không|đéo)\s+có(?:\s+\S+){0,3}", re.IGNORECASE),
    "bi_loi": re.compile(r"(?:bị\s+\S+(?:\s+\S+){0,2}|lỗi(?:\s+\S+){0,2})", re.IGNORECASE),
    "hoi_adj": re.compile(r"hơi\s+\S+(?:\s+\S+){0,2}", re.IGNORECASE),
    "qua_adj": re.compile(r"quá\s+\S+(?:\s+\S+){0,2}", re.IGNORECASE),
}
SPECIAL_MODIFIER_PATTERNS = {
    "hoi_strict": re.compile(r"hơi\s+(?:chật|tối|loe|bó|rộng|ngắn|dão|khó_chịu|khó_khăn|khác|bé|nhỏ|tiếc|buồn|đuối|cứng|bạc|cũ|trầy|sâu|kích|rão|co|kinh|thô|rít)\S*(?:\s+\S+){0,2}", re.IGNORECASE),
    "qua_strict": re.compile(r"(?:không\s+quá\s+\S+(?:\s+\S+){0,2}|quá\s+(?:tệ|nhiều|nhìu|đậm|to|bé|nhỏ|rộng|hẹp|yếu|chát|đắt|kém|buồn|ngon|đẹp|hợp|chất_lượng|mỏng|lâu|chán|mượt)\S*(?:\s+\S+){0,2})", re.IGNORECASE),
}
EXTRACTION_PATTERNS = {
    "kha_adj": re.compile(r"khá\s+\S+(?:\s+\S+){0,2}", re.IGNORECASE),
    "rat_adj": re.compile(r"rất\s+\S+(?:\s+\S+){0,2}", re.IGNORECASE),
    "van_adj": re.compile(r"vẫn\s+\S+(?:\s+\S+){0,2}", re.IGNORECASE),
    "cung_adj": re.compile(r"cũng\s+\S+(?:\s+\S+){0,2}", re.IGNORECASE),
}
VALID_PATTERN_TOKENS = {
    "khong_co": {"có", "size", "dây", "hộp", "độ", "gì", "phần", "google", "voucher", "màu", "túi", "sạc"},
    "bi_loi": {"bị", "lỗi", "dính", "rách", "gạt", "nhảy", "out", "thủng", "trễ", "móp", "méo", "rụng", "lag", "đơ"},
    "hoi_adj": {"hơi", "chật", "tối", "loe", "bó", "rộng", "ngắn", "xấu", "mỏng", "nóng", "lỏng", "nặng", "bí", "đắt"},
    "qua_adj": {"quá", "tệ", "ổn", "nhiều", "đậm", "sai", "xấu", "chán", "mắc", "cao", "nhanh", "lâu"},
}
VALID_EXTRACTION_TOKENS = {
    "kha_adj": {"khá", "mềm", "ổn", "xấu", "đều", "hay", "nhanh", "hời", "tốt", "rẻ", "hữu_ích"},
    "rat_adj": {"rất", "hữu_ích", "có", "đẹp", "tốt", "nhanh", "nhiệt_tình", "ổn", "tệ", "hài_lòng", "có_ý"},
    "van_adj": {"vẫn", "còn", "ổn", "được", "tốt", "tạm"},
    "cung_adj": {"cũng", "được", "ổn", "ok", "tạm", "khó", "nhanh", "tốt"},
    "hoi_strict": {"hơi", "chật", "tối", "loe", "bó", "rộng", "ngắn", "dão", "khó_chịu", "khó_khăn", "khác", "bé", "nhỏ", "tiếc", "buồn", "đuối", "cứng", "bạc", "cũ", "trầy", "sâu", "kích", "rão", "co", "kinh", "thô", "rít"},
    "qua_strict": {"quá", "không", "tệ", "nhiều", "nhìu", "đậm", "to", "bé", "nhỏ", "rộng", "yếu", "chát", "đắt", "kém", "buồn", "ngon", "đẹp", "hợp", "chất_lượng", "mỏng", "lâu", "chán", "mượt"},
}


def normalize_text(value: str) -> str:
    value = value.lower().replace("_", " ")
    value = re.sub(r"\s+", " ", value).strip(STRIP_CHARS)
    return value


def build_lexicon() -> dict[str, set[int]]:
    lexicon: dict[str, set[int]] = {}

    def add(phrases: list[str], sentiments: set[int]) -> None:
        for phrase in phrases:
            lexicon.setdefault(normalize_text(phrase), set()).update(sentiments)

    add(
        [
            "đẹp", "tốt", "nhanh", "rẻ", "mượt", "mịn", "chắc", "chuẩn", "xinh", "ngon", "hay",
            "tuyệt", "tuyệt_vời", "hài lòng", "ưng", "ưng_ý", "nhiệt_tình", "thân_thiện", "dễ_chịu",
            "cẩn_thận", "ổn_định", "đúng hẹn", "đúng_hẹn", "đúng giờ", "đúng_giờ", "hợp_lý", "hời",
            "êm", "mát", "phù_hợp", "tin_cậy", "trâu", "sáng", "sắc_nét", "đáng khen", "đáng_khen",
            "yên_tâm", "nhẹ đầu", "nhẹ_đầu", "vừa tay", "vừa_tay", "chủ_động", "rõ_ràng", "tiện_lợi",
            "tiện_dụng", "giữ dáng", "giữ_dáng", "co_giãn tốt", "co_giãn_tốt", "đúng mẫu", "đúng_mẫu",
            "nhanh_chóng", "vui_tính", "nhiệt_huyết", "uy_tín", "đa_dạng", "đầy_đủ", "y hình", "y_hình",
            "như hình", "như_hình", "tới sớm", "tới_sớm", "tới đúng", "tới_đúng", "còn nguyên", "còn_nguyên",
            "gọn gàng", "gọn_gàng", "chắc_chắn", "hữu_ích", "thanks", "cảm_ơn", "ủng_hộ", "rất hữu_ích",
            "rất_hữu_ích", "có ý", "có_ý", "vẫn còn", "vẫn_còn", "nhìn chắc_chắn", "giao gọn", "giao_gọn",
            "có tâm", "có_tâm", "giữ lời", "giữ_lời", "tận tình", "tận_tình", "tư vấn", "tư_vấn", "phục vụ", "phục_vụ",
        ],
        {1},
    )
    add(
        [
            "ổn", "ok", "oke", "okk", "được", "tạm", "tạm_ổn", "tạm được", "tạm_được", "cũng được",
            "cũng_được", "khá ổn", "khá_ổn", "ổn thôi", "ổn_thôi", "dùng được", "dùng_được",
            "chấp nhận được", "chấp_nhận_được", "vừa phải", "vừa_phải", "không tệ", "không_tệ",
            "không bị trễ", "không_bị_trễ", "không có gì đặc biệt", "không_có_gì_đặc_biệt", "không vấn đề gì",
            "không_vấn_đề_gì", "không quá nhanh", "không_quá_nhanh", "không quá tốt", "không_quá_tốt",
            "không quá ấn tượng", "không_quá_ấn_tượng", "bình thường", "bình_thường", "tạm dùng", "tạm_dùng",
            "vẫn ổn", "vẫn_ổn", "không sao", "tạm chấp nhận", "tạm_chấp_nhận", "không phát sinh",
            "không_phát_sinh", "đúng và đầy đủ", "đúng_và_đầy_đủ", "nhẹ đầu", "nhẹ_đầu", "khá đều", "khá_đều",
            "như vậy", "như_vậy", "tạm ổn", "tạm_ổn", "được thôi", "được_thôi", "còn nguyên", "còn_nguyên", "tư vấn", "tư_vấn", "phục vụ", "phục_vụ",
        ],
        {2},
    )
    add(["ổn", "ok", "oke", "okk", "quá ổn", "quá_ổn", "rất ổn", "rất_ổn"], {1, 2})
    add(
        [
            "tệ", "xấu", "kém", "chậm", "đắt", "tồi", "dở", "lỗi", "mỏng", "rộng", "nhỏ", "to",
            "bẩn", "hôi", "nhạt", "cứng", "nặng", "sai", "thiếu", "trễ", "lâu", "khó_chịu", "ẩu",
            "cẩu_thả", "rối", "khựng", "lag", "giật", "đơ", "nóng", "yếu", "lệch", "móp", "méo",
            "rách", "không đúng", "không_đúng", "không như hình", "không_như_hình", "không giống",
            "không_giống", "không đẹp", "không_đẹp", "không nhạy", "không_nhạy", "không ổn", "không_ổn",
            "không tốt", "không_tốt", "không vừa", "không_vừa", "không mượt", "không_mượt", "không tải được",
            "không_tải_được", "không dùng được", "không_dùng_được", "thất_vọng", "phiền", "mệt", "sốt_ruột",
            "ngán", "bực", "cáu", "văng", "khó", "lo", "bí", "lộ", "chật", "ngắn", "ngứa", "thủng",
            "tuột", "hụt_hẫng", "mắc", "chát", "cao", "trễ hẹn", "trễ_hẹn", "lòng_vòng", "sơ_sài",
            "chập_chờn", "lăn_tăn", "bịp", "lừa_dối", "mất_công", "cực", "kháu", "khá bực", "khá_bực",
            "bị dính màu", "bị_dính_màu", "không gửi được", "không_gửi_được", "lằng_nhằng", "quá chán",
            "quá_chán", "bị out", "bị_out", "quá xấu", "quá_xấu", "không kiểm_tra", "không_kiểm_tra",
            "không có", "không_có", "đéo có", "đéo_có",
            "giao nhầm", "giao_nhầm", "nhầm màu", "nhầm_màu", "rơi mất", "rơi_mất", "đắng", "lô lắm", "lô_lắm",
            "tự_động chạy", "tự động chạy", "rắc_rối", "lạnh_nhạt", "xử_lý ì", "xử_lý_ì", "gọi muộn", "gọi_muộn",
            "kéo dài", "kéo_dài", "lừa_đảo", "vui thật", "vui_thật", "làm rơi", "làm_rơi", "nhầm mẫu", "nhầm_mẫu",
        ],
        {0},
    )

    modifiers = ["rất", "quá", "hơi", "khá", "cực", "siêu", "cũng", "vẫn", "tương_đối", "tạm"]
    heads = {
        1: ["đẹp", "tốt", "nhanh", "mượt", "mịn", "ngon", "êm", "mát", "hời", "chuẩn", "xinh"],
        2: ["ổn", "ok", "được", "tạm", "bình_thường"],
        0: ["tệ", "xấu", "kém", "chậm", "đắt", "mỏng", "cứng", "lâu", "phiền", "lag", "giật", "đơ", "nóng", "chật", "ngắn"],
    }
    for sentiment, words in heads.items():
        for word in words:
            for modifier in modifiers:
                add([f"{modifier} {word}", f"{modifier}_{word}"], {sentiment})

    return lexicon


LEXICON = build_lexicon()


def find_clause_bounds(text: str, start: int, end: int) -> tuple[int, int]:
    prev_boundary = -1
    next_boundary = len(text)
    for match in BOUNDARY_PATTERN.finditer(text):
        boundary = match.start()
        if boundary < start:
            prev_boundary = boundary
        elif boundary >= end:
            next_boundary = boundary
            break

    clause_start = prev_boundary + 1
    clause_end = next_boundary
    while clause_start < len(text) and text[clause_start].isspace():
        clause_start += 1
    while clause_end > clause_start and text[clause_end - 1].isspace():
        clause_end -= 1
    return clause_start, clause_end


def token_spans(text: str, start: int, end: int) -> list[tuple[int, int]]:
    return [(match.start(), match.end()) for match in TOKEN_PATTERN.finditer(text, start, end)]


def overlaps(span_a: tuple[int, int], span_b: tuple[int, int]) -> bool:
    return max(span_a[0], span_b[0]) < min(span_a[1], span_b[1])


def score_phrase_tokens(normalized: str, sentiment: int) -> float:
    tokens = normalized.split()
    if not tokens:
        return -1.0
    any_cue_hits = sum(token in ALL_CUE_TOKENS for token in tokens)
    sentiment_cue_hits = sum(token in ADJACENT_CUES[sentiment] for token in tokens)
    lexicon_any = 1.0 if normalized in LEXICON else 0.0
    lexicon_match = 1.0 if normalized in LEXICON and sentiment in LEXICON[normalized] else 0.0
    if any_cue_hits == 0 and lexicon_any == 0.0:
        return -1.0
    return any_cue_hits * 1.6 + sentiment_cue_hits * 0.8 + lexicon_any * 0.8 + lexicon_match * 0.8 - max(0, len(tokens) - 3) * 0.25


def score_adjacent_phrase(text: str, span: tuple[int, int], sentiment: int) -> float:
    raw_phrase = text[span[0]:span[1]].strip(STRIP_CHARS)
    normalized = normalize_text(raw_phrase)
    if not normalized:
        return -1.0
    return score_phrase_tokens(normalized, sentiment)


def infer_pattern_opinion(text: str, clause_start: int, clause_end: int, target_start: int, target_end: int, sentiment: int) -> tuple[str, list[int], str] | None:
    target_span = (target_start, target_end)
    candidates: list[tuple[float, int, int, str]] = []
    clause_text = text[clause_start:clause_end]

    ordered_patterns = {}
    ordered_patterns.update(SPECIAL_MODIFIER_PATTERNS)
    ordered_patterns.update(EASY_GROUP_PATTERNS)
    ordered_patterns.update(EXTRACTION_PATTERNS)

    for group_name, pattern in ordered_patterns.items():
        for match in pattern.finditer(clause_text):
            span = (clause_start + match.start(), clause_start + match.end())
            if overlaps(span, target_span):
                continue
            raw_phrase = text[span[0]:span[1]].strip(STRIP_CHARS)
            normalized = normalize_text(raw_phrase)
            if not normalized:
                continue
            token_set = set(normalized.split())
            valid_tokens = VALID_PATTERN_TOKENS.get(group_name, VALID_EXTRACTION_TOKENS.get(group_name, set()))
            if not (token_set & valid_tokens):
                continue
            phrase_score = score_phrase_tokens(normalized, sentiment)
            if phrase_score < 0:
                phrase_score = 0.5 if group_name in {"bi_loi", "khong_co"} else -1.0
            if phrase_score < 0:
                continue
            distance = min(abs(span[0] - target_end), abs(target_start - span[1])) if span[1] <= target_start or span[0] >= target_end else 0
            side_bonus = 0.15 if span[0] >= target_end else 0.0
            score = distance - phrase_score - side_bonus
            candidates.append((score, span[0], span[1], group_name))

    if not candidates:
        return None

    _, opinion_start, opinion_end, group_name = sorted(candidates)[0]
    opinion = text[opinion_start:opinion_end].strip(STRIP_CHARS)
    return opinion, [opinion_start, opinion_end], f"pattern:{group_name}"


def classify_review_group(text: str, target_span: list[int]) -> str:
    start, end = target_span
    window = text[max(0, start - 40):min(len(text), end + 60)]
    for group_name, pattern in EASY_GROUP_PATTERNS.items():
        if pattern.search(window):
            return group_name
    return "other"


def infer_adjacent_opinion(text: str, tokens: list[tuple[int, int]], target_start: int, target_end: int, sentiment: int) -> tuple[str, list[int], str] | None:
    overlapping = [idx for idx, span in enumerate(tokens) if overlaps(span, (target_start, target_end))]
    if not overlapping:
        return None

    target_left = overlapping[0]
    target_right = overlapping[-1]
    candidates: list[tuple[float, int, int]] = []

    for width in range(1, 5):
        if target_left - width >= 0:
            span = (tokens[target_left - width][0], tokens[target_left - 1][1])
            score = score_adjacent_phrase(text, span, sentiment)
            if score >= 0:
                candidates.append((-(score + 0.1), span[0], span[1]))
        if target_right + width < len(tokens):
            span = (tokens[target_right + 1][0], tokens[target_right + width][1])
            score = score_adjacent_phrase(text, span, sentiment)
            if score >= 0:
                candidates.append((-(score + 0.2), span[0], span[1]))

    if not candidates:
        return None

    _, opinion_start, opinion_end = sorted(candidates)[0]
    opinion = text[opinion_start:opinion_end].strip(STRIP_CHARS)
    return opinion, [opinion_start, opinion_end], "adjacent"


def infer_opinion_span(text: str, target_start: int, target_end: int, sentiment: int) -> tuple[str, list[int], str]:
    clause_start, clause_end = find_clause_bounds(text, target_start, target_end)
    tokens = token_spans(text, clause_start, clause_end)
    target_span = (target_start, target_end)
    candidates: list[tuple[float, int, int]] = []

    for left in range(len(tokens)):
        for right in range(min(len(tokens), left + 4), left, -1):
            span = (tokens[left][0], tokens[right - 1][1])
            if overlaps(span, target_span):
                continue
            raw_phrase = text[span[0]:span[1]].strip(STRIP_CHARS)
            normalized = normalize_text(raw_phrase)
            if not normalized:
                continue
            phrase_sentiments = LEXICON.get(normalized)
            if not phrase_sentiments:
                continue
            exact = sentiment in phrase_sentiments
            sentiment_penalty = 0.0 if exact else 1.5
            distance = min(abs(span[0] - target_end), abs(target_start - span[1])) if span[1] <= target_start or span[0] >= target_end else 0
            length_bonus = (right - left) * 0.1
            side_bonus = 0.15 if span[0] >= target_end else 0.0
            score = distance + sentiment_penalty - length_bonus - side_bonus
            candidates.append((score, span[0], span[1]))

    if candidates:
        _, opinion_start, opinion_end = sorted(candidates)[0]
        opinion = text[opinion_start:opinion_end].strip(STRIP_CHARS)
        return opinion, [opinion_start, opinion_end], "heuristic"

    pattern_match = infer_pattern_opinion(text, clause_start, clause_end, target_start, target_end, sentiment)
    if pattern_match is not None:
        return pattern_match

    if not candidates:
        adjacent = infer_adjacent_opinion(text, tokens, target_start, target_end, sentiment)
        if adjacent is not None:
            return adjacent
        return "", [-1, -1], "unresolved"


def relabel_record(record: dict) -> tuple[dict, bool]:
    triplets = []
    needs_review = False

    for opinion_item in record.get("opinions", []):
        target = opinion_item["target"]
        target_start = int(opinion_item["start"])
        target_end = int(opinion_item["end"])
        sentiment = int(opinion_item["sentiment"])
        opinion_text, opinion_span, source = infer_opinion_span(record["text"], target_start, target_end, sentiment)
        if source != "heuristic":
            needs_review = True
        triplets.append(
            {
                "aspect": opinion_item["aspect"],
                "target": target,
                "target_span": [target_start, target_end],
                "opinion": opinion_text,
                "opinion_span": opinion_span,
                "aspect_opinion_pair": f"{target} {opinion_text}".strip() if opinion_text else target,
                "sentiment": sentiment,
            }
        )

    return {"text": record["text"], "triplets": triplets}, needs_review


def main() -> None:
    total_records = 0
    total_triplets = 0
    unresolved_triplets = 0
    review_records = 0
    sentiment_counter = Counter()
    aspect_counter = Counter()
    grouped_review_counts = Counter()

    grouped_handles = {name: open(path, "w", encoding="utf-8") for name, path in GROUPED_REVIEW_FILES.items()}

    with open(INPUT_FILE, encoding="utf-8") as src, open(OUTPUT_FILE, "w", encoding="utf-8") as out, open(REVIEW_FILE, "w", encoding="utf-8") as review:
        for line_no, line in enumerate(src, start=1):
            line = line.strip()
            if not line:
                continue
            raw_record = json.loads(line)
            relabeled, needs_review = relabel_record(raw_record)
            total_records += 1
            total_triplets += len(relabeled["triplets"])
            for triplet in relabeled["triplets"]:
                sentiment_counter[triplet["sentiment"]] += 1
                aspect_counter[triplet["aspect"]] += 1
                if triplet["opinion_span"] == [-1, -1]:
                    unresolved_triplets += 1

            out.write(json.dumps(relabeled, ensure_ascii=False) + "\n")

            if needs_review:
                unresolved_record_triplets = [
                    triplet for triplet in relabeled["triplets"] if triplet["opinion_span"] == [-1, -1]
                ]
                review_payload = {
                    "line_no": line_no,
                    "text": raw_record["text"],
                    "triplets": unresolved_record_triplets,
                }
                review.write(json.dumps(review_payload, ensure_ascii=False) + "\n")
                review_records += 1

                groups_in_record = set()
                for triplet in unresolved_record_triplets:
                    group_name = classify_review_group(raw_record["text"], triplet["target_span"])
                    groups_in_record.add(group_name)
                for group_name in groups_in_record:
                    grouped_payload = {
                        "line_no": line_no,
                        "text": raw_record["text"],
                        "triplets": [
                            triplet for triplet in unresolved_record_triplets
                            if classify_review_group(raw_record["text"], triplet["target_span"]) == group_name
                        ],
                    }
                    grouped_handles[group_name].write(json.dumps(grouped_payload, ensure_ascii=False) + "\n")
                    grouped_review_counts[group_name] += 1

    for handle in grouped_handles.values():
        handle.close()

    report = {
        "input_file": str(INPUT_FILE),
        "output_file": str(OUTPUT_FILE),
        "review_file": str(REVIEW_FILE),
        "total_records": total_records,
        "total_triplets": total_triplets,
        "review_records": review_records,
        "resolved_triplets": total_triplets - unresolved_triplets,
        "unresolved_triplets": unresolved_triplets,
        "resolved_rate": round((total_triplets - unresolved_triplets) / max(total_triplets, 1), 4),
        "sentiment_distribution": dict(sentiment_counter),
        "aspect_distribution": dict(aspect_counter),
        "grouped_review_records": dict(grouped_review_counts),
    }
    with open(REPORT_FILE, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()