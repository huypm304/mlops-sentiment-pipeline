#!/usr/bin/env python3

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


INPUT_FILE = Path("data/processed/train_final_v3.jsonl")
OUTPUT_FILE = Path("data/processed/train_final_v3.autofixed.jsonl")
REVIEW_FILE = Path("data/processed/train_final_v3.autofix_review.jsonl")
REPORT_FILE = Path("data/processed/train_final_v3.autofix_report.json")
MIN_TOKENS = 3

VALID_ASPECTS = {"Product", "Service", "Ship", "Price", "App"}
VALID_SENTIMENTS = {0, 1, 2}

OPINION_WORDS = {
    "tệ", "xấu", "kém", "chậm", "đắt", "tồi", "dở", "lỗi", "mỏng", "rộng", "nhỏ",
    "to", "bẩn", "hôi", "nhạt", "cứng", "nặng", "sai", "thiếu", "trễ", "lâu",
    "đẹp", "tốt", "nhanh", "rẻ", "mượt", "mịn", "chắc", "chuẩn", "ổn", "xinh",
    "ngon", "hay", "tuyệt", "ok", "oke", "bình_thường", "tạm", "được", "thôi",
}

STRONG_NEGATIVE_PATTERNS = [
    r"không\s+(?:tốt|ổn|ok|đẹp|mượt|nhanh|hài_lòng|hài lòng|được|vừa|giống)",
    r"(?:bị|rất|quá|hơi)?\s*(?:lỗi|lag|giật|đơ|chậm|kém|tệ|hỏng|rách|mỏng|hôi|bẩn|sai|thiếu|tụt|yếu|nóng|lem|phai|cũ)",
    r"không\s+(?:trả_lời|trả lời|phản_hồi|phản hồi|hỗ_trợ|hỗ trợ|gọi|giao|nhận)",
    r"(?:giao|ship|vận_chuyển|vận chuyển).{0,18}(?:chậm|lâu|trễ|sai|thiếu|hoàn|hủy)",
    r"(?:shop|nhân_viên|nhân viên|dịch_vụ|dịch vụ).{0,18}(?:kém|tệ|cẩu_thả|cẩu thả|không\s+trả_lời|không\s+hỗ_trợ)",
    r"(?:giá|tiền|voucher|phí\s*ship|tầm\s*giá).{0,18}(?:đắt|cao|mắc|không\s+dùng\s+được|không\s+áp_dụng\s+được|không\s+áp dụng\s+được)",
    r"(?:pin|màn\s*hình|màn_hình|máy|áo|vải|chất|size|form|màu|củ_sạc|khuy|camera|ứng_dụng|ứng dụng|app|phần_mềm|phần mềm).{0,18}(?:chậm|kém|tệ|lỗi|nhỏ|to|rộng|chật|mỏng|xấu|nóng|yếu|tụt)",
]

STRONG_POSITIVE_PATTERNS = [
    r"(?:rất|khá|cực|siêu)?\s*(?:đẹp|tốt|ok|ổn|ngon|mượt|nhanh|nhiệt_tình|nhiệt tình|chu_đáo|chu đáo|tận_tâm|tận tâm|chắc_chắn|chắc chắn|cẩn_thận|cẩn thận|vừa_vặn|vừa vặn|hợp_lý|hợp lý|phù_hợp|phù hợp|đáng\s*tiền)",
    r"(?:giao|ship|vận_chuyển|vận chuyển).{0,18}(?:nhanh|ổn|ok|đúng)",
    r"(?:shop|nhân_viên|nhân viên|dịch_vụ|dịch vụ|trả_lời|trả lời).{0,18}(?:nhiệt_tình|nhiệt tình|chu_đáo|chu đáo|tốt|ổn|ok|dễ_thương|dễ thương)",
    r"(?:giá|tiền|voucher|tầm\s*giá).{0,18}(?:rẻ|hợp_lý|hợp lý|phù_hợp|phù hợp|ổn|ok|đáng\s*tiền)",
]

EXPLICIT_NEUTRAL_PATTERNS = [
    r"bình_thường|bình thường",
    r"tạm_được|tạm được",
    r"cũng_được|cũng được",
    r"tạm_ổn|tạm ổn",
]

CONTRAST_MARKERS = ["nhưng", "tuy_nhiên", "tuy nhiên", "mà", "dù", "trừ"]

ASPECT_NEG_RULES = {
    "Ship": [
        r"(?:giao|ship|vận_chuyển|vận chuyển|shipper).{0,16}(?<!\w)(?:chậm|lâu|trễ|sai|thiếu|hoàn|hủy|không\s+gọi|không\s+nhận|không\s+đúng)(?!\w)",
    ],
    "Service": [
        r"(?:shop|nhân_viên|nhân viên|dịch_vụ|dịch vụ|trả_lời|trả lời|phản_hồi|phản hồi).{0,16}(?<!\w)(?:không\s+trả_lời|không\s+phản_hồi|không\s+hỗ_trợ|kém|tệ|cẩu_thả|cẩu thả)(?!\w)",
    ],
    "App": [
        r"(?:app|ứng_dụng|ứng dụng|phần_mềm|phần mềm|hệ\s*điều\s*hành|cập_nhật|cập nhật).{0,16}(?<!\w)(?:lỗi|lag|giật|đơ|chậm|khóa|văng|tự\s*thoát|không\s+dùng\s+được)(?!\w)",
    ],
    "Price": [
        r"(?:giá|tiền|voucher|phí\s*ship|tầm\s*giá).{0,16}(?<!\w)(?:đắt|cao|mắc|không\s+áp_dụng\s+được|không\s+áp dụng\s+được|không\s+dùng\s+được)(?!\w)",
    ],
}

ASPECT_POS_RULES = {
    "Ship": [
        r"(?:giao|ship|vận_chuyển|vận chuyển).{0,12}(?<!\w)(?:nhanh|đúng_hẹn|đúng hẹn|ổn|ok)(?!\w)",
    ],
    "Service": [
        r"(?:shop|nhân_viên|nhân viên|dịch_vụ|dịch vụ|trả_lời|trả lời).{0,16}(?<!\w)(?:nhiệt_tình|nhiệt tình|chu_đáo|chu đáo|tận_tâm|tận tâm|tốt|ổn|ok)(?!\w)",
    ],
    "App": [
        r"(?:app|ứng_dụng|ứng dụng|phần_mềm|phần mềm).{0,12}(?<!\w)(?:tốt|ổn|ok|mượt|nhanh|tiện_lợi|tiện lợi|hữu_ích|hữu ích)(?!\w)",
    ],
    "Price": [
        r"(?:giá|tiền|voucher|tầm\s*giá).{0,12}(?<!\w)(?:rẻ|hợp_lý|hợp lý|phù_hợp|phù hợp|ổn|ok|đáng\s*tiền)(?!\w)",
    ],
}

PRODUCT_NEG_TARGET_RULES = {
    "pin": [r"pin.{0,12}(?<!\w)(?:tụt|yếu|kém|chậm)(?!\w)"],
    "màn_hình": [r"(?:màn_hình|màn hình).{0,12}(?<!\w)(?:lỗi|kém|tối|xấu)(?!\w)"],
    "camera": [r"camera.{0,12}(?<!\w)(?:mờ|xấu|kém)(?!\w)"],
    "củ_sạc": [r"củ_sạc.{0,12}(?<!\w)(?:tuột|chậm|lỗi)(?!\w)"],
    "vải": [r"(?:vải|chất_liệu|chất liệu|chất_lượng|chất lượng).{0,12}(?<!\w)(?:mỏng|xấu|cứng|hôi|bẩn|rách)(?!\w)"],
    "đường_may": [r"(?:đường\s*may|khuy).{0,12}(?<!\w)(?:ẩu|rách|lộ|rơi)(?!\w)"],
}

PRODUCT_POS_TARGET_RULES = {
    "pin": [r"pin.{0,8}(?<!\w)(?:trâu|ổn|tốt)(?!\w)"],
    "máy": [r"máy.{0,8}(?<!\w)(?:mượt|tốt|ổn)(?!\w)"],
    "màn_hình": [r"(?:màn_hình|màn hình).{0,8}(?<!\w)(?:đẹp|tốt|ổn)(?!\w)"],
    "camera": [r"camera.{0,8}(?<!\w)(?:đẹp|tốt|ổn)(?!\w)"],
    "vải": [r"(?:vải|chất_liệu|chất liệu|chất_lượng|chất lượng).{0,8}(?<!\w)(?:đẹp|tốt|ổn|mát)(?!\w)"],
    "đường_may": [r"(?:đường\s*may).{0,8}(?<!\w)(?:đẹp|tốt|ổn)(?!\w)"],
}

GENERIC_PRODUCT_TARGETS = {
    "áo", "hàng", "form", "size", "màu", "sản_phẩm", "sản phẩm", "mẫu", "kích_cỡ", "kích cỡ",
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
        return None, "offset_mismatch_after_trim"

    updated = dict(opinion)
    updated["target"] = trimmed
    updated["start"] = new_start
    updated["end"] = new_end
    return updated, None


def local_window(text: str, start: int, end: int, radius: int = 5) -> str:
    spans = [m.span() for m in re.finditer(r"\S+", text)]
    token_ids = []
    for i, (tok_s, tok_e) in enumerate(spans):
        if max(tok_s, start) < min(tok_e, end):
            token_ids.append(i)
    if not token_ids:
        return text.lower()
    lo = max(0, token_ids[0] - radius)
    hi = min(len(spans) - 1, token_ids[-1] + radius)
    return " ".join(text[s:e].lower() for s, e in spans[lo:hi + 1])


def clause_window(text: str, start: int, end: int) -> str:
    separators = [0, len(text)]
    for match in re.finditer(r"[\n,.!?;:]", text):
        separators.extend([match.start(), match.end()])
    left = max(point for point in separators if point <= start)
    right = min(point for point in separators if point >= end)
    return text[left:right].strip().lower()


def has_any(patterns: list[str], text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def has_contrast(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in CONTRAST_MARKERS)


def classify_conflict(text: str, opinion: dict) -> tuple[bool, str | None, str]:
    local = local_window(text, opinion["start"], opinion["end"], radius=5)
    has_neg = has_any(STRONG_NEGATIVE_PATTERNS, local)
    has_pos = has_any(STRONG_POSITIVE_PATTERNS, local)
    has_neutral = has_any(EXPLICIT_NEUTRAL_PATTERNS, local)
    sentiment = opinion["sentiment"]

    if sentiment == 1 and has_neg and not has_pos:
        return True, "negative_context", local
    if sentiment == 0 and has_pos and not has_neg:
        return True, "positive_context", local
    if sentiment == 1 and has_neutral and not has_pos and not has_neg:
        return True, "neutral_context", local
    return False, None, local


def direct_target_positive(opinion: dict, text: str) -> bool:
    window = local_window(text, opinion["start"], opinion["end"], radius=3)
    if opinion["aspect"] != "Product":
        return has_any(ASPECT_POS_RULES.get(opinion["aspect"], []), window)

    target = opinion["target"].lower()
    if target in GENERIC_PRODUCT_TARGETS:
        return False
    rules = []
    if "pin" in target:
        rules.extend(PRODUCT_POS_TARGET_RULES["pin"])
    if "máy" in target:
        rules.extend(PRODUCT_POS_TARGET_RULES["máy"])
    if "màn_hình" in target or "màn hình" in target:
        rules.extend(PRODUCT_POS_TARGET_RULES["màn_hình"])
    if "camera" in target:
        rules.extend(PRODUCT_POS_TARGET_RULES["camera"])
    if any(token in target for token in ["vải", "chất_liệu", "chất liệu", "chất_lượng", "chất lượng"]):
        rules.extend(PRODUCT_POS_TARGET_RULES["vải"])
    if "đường may" in target or "khuy" in target:
        rules.extend(PRODUCT_POS_TARGET_RULES["đường_may"])
    return has_any(rules, window) if rules else False


def direct_target_negative(opinion: dict, text: str) -> bool:
    window = local_window(text, opinion["start"], opinion["end"], radius=4)
    if opinion["aspect"] != "Product":
        return has_any(ASPECT_NEG_RULES.get(opinion["aspect"], []), window)

    target = opinion["target"].lower()
    if target in GENERIC_PRODUCT_TARGETS:
        return False
    rules = []
    if "pin" in target:
        rules.extend(PRODUCT_NEG_TARGET_RULES["pin"])
    if "màn_hình" in target or "màn hình" in target:
        rules.extend(PRODUCT_NEG_TARGET_RULES["màn_hình"])
    if "camera" in target:
        rules.extend(PRODUCT_NEG_TARGET_RULES["camera"])
    if "củ_sạc" in target:
        rules.extend(PRODUCT_NEG_TARGET_RULES["củ_sạc"])
    if any(token in target for token in ["vải", "chất_liệu", "chất liệu", "chất_lượng", "chất lượng"]):
        rules.extend(PRODUCT_NEG_TARGET_RULES["vải"])
    if "đường may" in target or "khuy" in target:
        rules.extend(PRODUCT_NEG_TARGET_RULES["đường_may"])
    return has_any(rules, window) if rules else False


def suggest_sentiment_fix(text: str, opinion: dict, conflict_type: str) -> tuple[int | None, str | None, str]:
    local = local_window(text, opinion["start"], opinion["end"], radius=5)
    clause = clause_window(text, opinion["start"], opinion["end"])
    sentiment = opinion["sentiment"]

    has_neg_local = has_any(STRONG_NEGATIVE_PATTERNS, local)
    has_pos_local = has_any(STRONG_POSITIVE_PATTERNS, local)
    has_neutral_local = has_any(EXPLICIT_NEUTRAL_PATTERNS, local)
    contrast_local = has_contrast(local)

    if conflict_type == "negative_context" and sentiment == 1:
        if direct_target_negative(opinion, text) and not has_pos_local:
            return 0, "pos_to_neg_direct_negative", local

    if conflict_type == "neutral_context" and sentiment == 1:
        if has_neutral_local and not has_pos_local and not has_neg_local:
            return 2, "pos_to_neu_explicit_neutral", local

    if conflict_type == "positive_context" and sentiment == 0:
        if direct_target_positive(opinion, text) and not has_neg_local and not contrast_local:
            return 1, "neg_to_pos_direct_positive", local

    return None, None, local


def main() -> int:
    stats = Counter()
    output_records = []
    review_records = []

    with INPUT_FILE.open(encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, 1):
            raw_line = raw_line.strip()
            if not raw_line:
                continue

            stats["input_records"] += 1
            record = json.loads(raw_line)
            text = record.get("text", "")
            opinions = record.get("opinions", [])

            if not isinstance(text, str) or not isinstance(opinions, list):
                stats["invalid_records"] += 1
                review_records.append({"line_no": line_no, "review_reasons": ["invalid_record_schema"], "row": record})
                continue
            if count_tokens(text) < MIN_TOKENS:
                stats["dropped_short_records"] += 1
                review_records.append({"line_no": line_no, "review_reasons": ["short_text"], "row": record})
                continue

            updated_record = dict(record)
            kept_opinions = []
            pending_reasons = []

            for opinion in opinions:
                stats["input_opinions"] += 1
                aspect = opinion.get("aspect")
                sentiment = opinion.get("sentiment")
                if aspect not in VALID_ASPECTS or sentiment not in VALID_SENTIMENTS:
                    stats["dropped_invalid_labels"] += 1
                    pending_reasons.append("invalid_aspect_or_sentiment")
                    continue

                normalized, error = normalize_target(text, opinion)
                if error:
                    stats[f"drop_{error}"] += 1
                    pending_reasons.append(error)
                    continue
                if normalized["target"] != opinion.get("target"):
                    stats["fixed_dirty_targets"] += 1

                if normalized["target"].lower() in OPINION_WORDS:
                    stats["dropped_opinion_word_targets"] += 1
                    pending_reasons.append("opinion_word_target")
                    continue

                has_conflict, conflict_type, evidence = classify_conflict(text, normalized)
                if not has_conflict:
                    kept_opinions.append(normalized)
                    continue

                suggested_sentiment, reason, evidence = suggest_sentiment_fix(text, normalized, conflict_type)
                if suggested_sentiment is not None and suggested_sentiment != normalized["sentiment"]:
                    updated = dict(normalized)
                    original_sentiment = normalized["sentiment"]
                    updated["sentiment"] = suggested_sentiment
                    kept_opinions.append(updated)
                    stats["autofixed_sentiment_conflicts"] += 1
                    stats[f"fix_{reason}"] += 1
                    stats[f"sent_{original_sentiment}_to_{suggested_sentiment}"] += 1
                    continue

                stats["remaining_review_conflicts"] += 1
                review_records.append({
                    "line_no": line_no,
                    "review_reasons": [conflict_type or "remaining_sentiment_conflict"],
                    "context": evidence,
                    "opinion": normalized,
                    "text": text,
                })
                continue

            if not kept_opinions:
                stats["dropped_empty_records"] += 1
                review_records.append({
                    "line_no": line_no,
                    "review_reasons": sorted(set(pending_reasons or ["empty_after_cleaning"])),
                    "row": record,
                })
                continue

            updated_record["opinions"] = kept_opinions
            output_records.append(updated_record)
            stats["output_records"] += 1
            stats["output_opinions"] += len(kept_opinions)

    OUTPUT_FILE.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in output_records), encoding="utf-8")
    REVIEW_FILE.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in review_records), encoding="utf-8")
    REPORT_FILE.write_text(json.dumps(dict(sorted(stats.items())), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(dict(sorted(stats.items())), ensure_ascii=False, indent=2))
    print(f"autofixed -> {OUTPUT_FILE}")
    print(f"review    -> {REVIEW_FILE}")
    print(f"report    -> {REPORT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())