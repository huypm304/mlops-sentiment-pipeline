#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/data_train_v8_aste.modifier_auto_merged.jsonl")
DEFAULT_OUTPUT = Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/data_train_v8_aste.modifier_auto_merged.qa_fixed.jsonl")
DEFAULT_ERRORS = Path("/home/uph3hc/project/mlops-sentiment-pipeline/aste_audit_errors.jsonl")
DEFAULT_SUMMARY = Path("/home/uph3hc/project/mlops-sentiment-pipeline/aste_audit_summary.md")

STRIP_CHARS = " \t\r\n.,;:!?()[]{}\"'“”‘’👍🙂☺️"
VALID_ASPECTS = {"Fashion", "Electronics", "General", "Service", "Ship", "Price", "App"}

NEG_PHRASES = {
    "không đáng",
    "phí tiền",
    "quá tệ",
    "quá chán",
    "thất vọng",
    "không gửi được",
    "không dùng được",
    "không như hình",
    "không đúng",
    "không đẹp",
    "không ổn",
    "không tốt",
    "hơi mỏng",
    "bị dính màu",
    "không kiểm tra",
    "không kiểm_tra",
    "tự động nhảy",
    "lag đơ",
    "lag",
    "đơ",
}
NEG_WORDS = {
    "tệ", "xấu", "kém", "chậm", "đắt", "tồi", "dở", "lỗi", "mỏng", "rộng", "nhỏ", "to",
    "bẩn", "hôi", "nhạt", "cứng", "nặng", "sai", "thiếu", "trễ", "lâu", "lag", "giật", "đơ",
    "nóng", "yếu", "rách", "móp", "méo", "thủng", "ẩu", "khó", "bí", "chật", "ngắn", "dính",
    "buồn", "rít", "tróc", "tụt", "khựng", "thất_vọng", "chán", "phí", "vỡ", "out",
}
POS_PHRASES = {
    "rất đẹp",
    "quá đẹp",
    "rất tốt",
    "quá tốt",
    "hài lòng",
    "đáng tiền",
    "quá ngon",
    "rất ngon",
    "đẹp lắm",
    "nhanh lắm",
    "quá hay",
    "rất mượt",
    "quá mượt",
    "vừa tay",
    "nhẹ đầu",
    "y hình",
    "như hình",
}
POS_WORDS = {
    "đẹp", "tốt", "nhanh", "rẻ", "mượt", "mịn", "chắc", "chuẩn", "xinh", "ngon", "hay", "tuyệt",
    "ưng", "nhiệt_tình", "thân_thiện", "êm", "mát", "trâu", "nét", "sắc_nét",
    "hời", "thích", "ổn_áp", "okela", "xịn", "y_hình", "vui_tính", "vui", "nhiệt_huyết",
}
NEU_PHRASES = {
    "đúng mẫu",
    "đúng hẹn",
    "đúng giờ",
    "không phát sinh",
    "cũng được",
    "tạm được",
    "bình thường",
    "dùng được",
    "chấp nhận được",
    "còn nguyên",
    "không sao",
    "được thôi",
    "tạm ổn",
    "vẫn ổn",
}
NEU_WORDS = {"được", "ổn", "ok", "oke", "tạm", "bình_thường", "bth", "ổn_định"}
OBJECTIVE_OPINIONS = {
    "phục vụ", "tư vấn", "dịch vụ", "shop", "nhân viên", "sản phẩm", "máy", "app", "ứng dụng",
}

ASPECT_KEYWORDS = {
    "Price": {"giá", "tiền", "đồng tiền", "mức giá", "tầm giá", "phí", "giá_cả", "giá cả"},
    "Ship": {"ship", "giao", "giao_hàng", "giao hàng", "vận_chuyển", "vận chuyển", "đóng_gói", "đóng gói", "khâu_giao_đơn", "khâu giao đơn", "đơn hàng", "gói hàng"},
    "App": {"app", "ứng_dụng", "ứng dụng", "phần_mềm", "phần mềm", "web", "website", "tải", "đăng_nhập", "đăng nhập"},
    "Service": {"nhân_viên", "nhân viên", "shop", "cửa_hàng", "cửa hàng", "phục_vụ", "phục vụ", "tư_vấn", "tư vấn", "chăm_sóc", "chăm sóc", "bảo_hành", "bảo hành", "dịch_vụ", "dịch vụ", "thái độ"},
    "Electronics": {"máy", "pin", "loa", "camera", "màn_hình", "màn hình", "chip", "sạc", "củ_sạc", "củ sạc", "tai_nghe", "tai nghe", "ram", "rom", "vân_tay", "vân tay", "wifi", "bluetooth", "ios", "android", "iphone", "samsung"},
    "Fashion": {"áo", "quần", "váy", "giày", "dép", "vải", "chất_vải", "chất vải", "size", "form", "màu", "đế", "áo_khoác", "áo khoác", "áo_thun", "áo thun", "quần_jean", "quần jean", "dáng"},
    "General": {"sản_phẩm", "sản phẩm", "sp", "chất_lượng", "chất lượng", "mẫu"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit and auto-fix ASTE JSONL labels")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--errors", type=Path, default=DEFAULT_ERRORS)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    return parser.parse_args()


def normalize_text(value: str) -> str:
    value = value.lower().replace("_", " ")
    value = re.sub(r"\s+", " ", value).strip(STRIP_CHARS)
    return value


def find_occurrences(text: str, phrase: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    if not phrase:
        return spans
    start = 0
    while True:
        idx = text.find(phrase, start)
        if idx < 0:
            break
        spans.append((idx, idx + len(phrase)))
        start = idx + 1
    return spans


def choose_nearest(spans: list[tuple[int, int]], hint_start: int) -> tuple[int, int] | None:
    if not spans:
        return None
    return min(spans, key=lambda item: abs(item[0] - hint_start))


def repair_phrase_span(text: str, phrase: str, span: list[int] | tuple[int, int], field_name: str) -> tuple[str, list[int], dict[str, Any] | None]:
    try:
        start, end = int(span[0]), int(span[1])
    except Exception:
        start, end = -1, -1

    valid_span = 0 <= start <= end <= len(text)
    actual = text[start:end] if valid_span else ""
    if valid_span and actual == phrase:
        return phrase, [start, end], None

    occurrences = find_occurrences(text, phrase)
    chosen = choose_nearest(occurrences, start if start >= 0 else 0)
    if chosen is not None:
        return phrase, [chosen[0], chosen[1]], {
            "type": "Span lệch",
            "current": f'{field_name}: {json.dumps(phrase, ensure_ascii=False)} {list(span)}',
            "suggestion": f'{field_name}: {json.dumps(phrase, ensure_ascii=False)} {[chosen[0], chosen[1]]}',
            "reason": f'Span không khớp exact substring trong text; tìm thấy match gần nhất tại {[chosen[0], chosen[1]]}.',
        }

    if valid_span:
        return actual, [start, end], {
            "type": "Span lệch",
            "current": f'{field_name}: {json.dumps(phrase, ensure_ascii=False)} {list(span)}',
            "suggestion": f'{field_name}: {json.dumps(actual, ensure_ascii=False)} {[start, end]}',
            "reason": 'Không tìm thấy phrase exact trong text; dùng exact substring theo span hiện tại.',
        }

    return phrase, [start, end], {
        "type": "Span lệch",
        "current": f'{field_name}: {json.dumps(phrase, ensure_ascii=False)} {list(span)}',
        "suggestion": f'{field_name}: {json.dumps(phrase, ensure_ascii=False)} {list(span)}',
        "reason": 'Span nằm ngoài độ dài text và không có cách sửa chắc chắn.',
    }


def classify_clear_sentiment(opinion: str) -> int | None:
    normalized = normalize_text(opinion)
    if not normalized:
        return None
    if normalized in OBJECTIVE_OPINIONS:
        return None
    if normalized in {"không tệ", "không quá nhanh", "không quá tốt", "không bị trễ", "không vấn đề gì", "không sao"}:
        return 2
    if normalized.startswith("không quá "):
        return 2
    if normalized in NEG_PHRASES:
        return 0
    if normalized in POS_PHRASES:
        return 1
    if normalized in NEU_PHRASES:
        return 2

    tokens = set(normalized.split())
    neg_hits = sum(phrase in normalized for phrase in NEG_PHRASES) + sum(token in tokens for token in NEG_WORDS)
    pos_hits = sum(phrase in normalized for phrase in POS_PHRASES) + sum(token in tokens for token in POS_WORDS)
    neu_hits = sum(phrase in normalized for phrase in NEU_PHRASES) + sum(token in tokens for token in NEU_WORDS)

    if normalized.startswith("không "):
        if pos_hits > 0:
            return 0
        if neg_hits > 0:
            return 2

    if neg_hits > 0 and pos_hits == 0:
        return 0
    if pos_hits > 0 and neg_hits == 0 and neu_hits == 0:
        return 1
    if neu_hits > 0 and neg_hits == 0 and pos_hits == 0:
        return 2
    if normalized in {"được", "ổn", "ok", "oke", "bình thường", "tạm", "tạm ổn", "cũng được"}:
        return 2
    return None


def phrase_in_text(text: str, phrase: str) -> bool:
    padded_text = f" {text} "
    padded_phrase = f" {normalize_text(phrase)} "
    return padded_phrase in padded_text or text == normalize_text(phrase)


def guess_aspect(target: str, opinion: str) -> tuple[str | None, str | None]:
    target_norm = normalize_text(target)
    opinion_norm = normalize_text(opinion)
    matches: list[tuple[str, str]] = []
    for aspect, keywords in ASPECT_KEYWORDS.items():
        for keyword in keywords:
            if phrase_in_text(target_norm, keyword):
                matches.append((aspect, keyword))
                break

    if not matches and opinion_norm in {"giao nhanh", "đúng hẹn", "đóng gói cẩn thận"}:
        matches.append(("Ship", opinion_norm))

    if not matches:
        return None, None

    priority = ["Price", "Ship", "App", "Service", "Electronics", "Fashion", "General"]
    matches.sort(key=lambda item: priority.index(item[0]))
    return matches[0]


def build_pair(target: str, opinion: str) -> str:
    return f"{target} {opinion}".strip() if opinion else target


def audit_triplet(text: str, triplet: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    fixed = dict(triplet)
    errors: list[dict[str, Any]] = []

    fixed_target, fixed_target_span, target_error = repair_phrase_span(text, str(fixed.get("target", "")), fixed.get("target_span", [-1, -1]), "target")
    fixed["target"] = fixed_target
    fixed["target_span"] = fixed_target_span
    if target_error is not None:
        errors.append(target_error)

    fixed_opinion, fixed_opinion_span, opinion_error = repair_phrase_span(text, str(fixed.get("opinion", "")), fixed.get("opinion_span", [-1, -1]), "opinion")
    fixed["opinion"] = fixed_opinion
    fixed["opinion_span"] = fixed_opinion_span
    if opinion_error is not None:
        errors.append(opinion_error)

    expected_pair = build_pair(fixed["target"], fixed["opinion"])
    if fixed.get("aspect_opinion_pair") != expected_pair:
        errors.append(
            {
                "type": "Pair không tự nhiên",
                "current": f'aspect_opinion_pair: {json.dumps(fixed.get("aspect_opinion_pair", ""), ensure_ascii=False)}',
                "suggestion": f'aspect_opinion_pair: {json.dumps(expected_pair, ensure_ascii=False)}',
                "reason": 'Pair phải là tổ hợp tự nhiên giữa target và opinion theo schema ASTE.',
            }
        )
        fixed["aspect_opinion_pair"] = expected_pair

    clear_sentiment = classify_clear_sentiment(fixed["opinion"])
    if clear_sentiment is not None and fixed.get("sentiment") != clear_sentiment:
        errors.append(
            {
                "type": "Sentiment sai",
                "current": f'sentiment: {fixed.get("sentiment")}',
                "suggestion": f'sentiment: {clear_sentiment}',
                "reason": f'Opinion {json.dumps(fixed["opinion"], ensure_ascii=False)} thể hiện polarity rõ ràng.',
            }
        )
        fixed["sentiment"] = clear_sentiment

    guessed_aspect, keyword = guess_aspect(fixed["target"], fixed["opinion"])
    if guessed_aspect is not None and guessed_aspect in VALID_ASPECTS and fixed.get("aspect") != guessed_aspect:
        errors.append(
            {
                "type": "Aspect sai",
                "current": f'aspect: {fixed.get("aspect")}',
                "suggestion": f'aspect: {guessed_aspect}',
                "reason": f'Target/opinion khớp mạnh với nhóm {guessed_aspect} qua keyword {json.dumps(keyword, ensure_ascii=False)}.',
            }
        )
        fixed["aspect"] = guessed_aspect

    return fixed, errors


def render_summary(
    input_path: Path,
    output_path: Path,
    total_records: int,
    records_with_errors: int,
    error_counter: Counter,
    sample_rows: list[dict[str, Any]],
) -> str:
    error_pct = (records_with_errors / total_records * 100) if total_records else 0.0
    lines = [
        "# ASTE Data QA Report",
        f"**Input**: {input_path.name}",
        f"**Corrected Output**: {output_path.name}",
        f"**Total records**: {total_records}",
        f"**Records có lỗi**: {records_with_errors} ({error_pct:.2f}%)",
        "",
        "## Tổng hợp lỗi",
        "",
        "| Loại lỗi | Số lần |",
        "|---|---:|",
    ]
    for error_type, count in error_counter.most_common():
        lines.append(f"| {error_type} | {count} |")

    lines.extend([
        "",
        "## Mẫu lỗi đã sửa",
        "",
        "| STT | Nội dung lỗi | Hiện tại | Gợi ý sửa | Lý do |",
        "|---:|---|---|---|---|",
    ])
    for idx, row in enumerate(sample_rows, start=1):
        lines.append(
            "| {idx} | {error_type} | {current} | {suggestion} | {reason} |".format(
                idx=idx,
                error_type=row["type"].replace("|", "\\|"),
                current=row["current"].replace("|", "\\|"),
                suggestion=row["suggestion"].replace("|", "\\|"),
                reason=row["reason"].replace("|", "\\|"),
            )
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    total_records = 0
    records_with_errors = 0
    error_counter: Counter[str] = Counter()
    sample_rows: list[dict[str, Any]] = []

    with open(args.input, encoding="utf-8") as src, open(args.output, "w", encoding="utf-8") as out, open(args.errors, "w", encoding="utf-8") as err_out:
        for line_no, line in enumerate(src, start=1):
            line = line.strip()
            if not line:
                continue
            total_records += 1
            record = json.loads(line)
            fixed_triplets = []
            record_errors = []
            for triplet_idx, triplet in enumerate(record.get("triplets", [])):
                fixed_triplet, triplet_errors = audit_triplet(record["text"], triplet)
                fixed_triplets.append(fixed_triplet)
                for error in triplet_errors:
                    error["triplet_idx"] = triplet_idx
                    record_errors.append(error)
                    error_counter[error["type"]] += 1
                    if len(sample_rows) < 50:
                        sample_rows.append({
                            "type": error["type"],
                            "current": error["current"],
                            "suggestion": error["suggestion"],
                            "reason": error["reason"],
                        })

            fixed_record = {"text": record["text"], "triplets": fixed_triplets}
            out.write(json.dumps(fixed_record, ensure_ascii=False) + "\n")

            if record_errors:
                records_with_errors += 1
                err_out.write(
                    json.dumps(
                        {
                            "line_no": line_no,
                            "text": record["text"],
                            "errors": record_errors,
                            "fixed_triplets": fixed_triplets,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )

    summary_text = render_summary(args.input, args.output, total_records, records_with_errors, error_counter, sample_rows)
    with open(args.summary, "w", encoding="utf-8") as handle:
        handle.write(summary_text)

    print(
        json.dumps(
            {
                "input": str(args.input),
                "output": str(args.output),
                "errors": str(args.errors),
                "summary": str(args.summary),
                "total_records": total_records,
                "records_with_errors": records_with_errors,
                "error_breakdown": dict(error_counter),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()