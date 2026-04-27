import json
import re
import unicodedata
from collections import Counter
from pathlib import Path


INPUT_FILE = Path("data/processed/data_train_v5.jsonl")
OUTPUT_FILE = Path("data/processed/data_train_v5.autofixed.jsonl")
REPORT_FILE = Path("data/processed/data_train_v5.autofix_report.json")
REVIEW_FILE = Path("data/processed/data_train_v5.autofix_review.jsonl")

OPINION_WORDS = {
    "tệ", "xấu", "kém", "chậm", "đắt", "tồi", "dở", "lỗi", "mỏng", "rộng", "nhỏ",
    "to", "bẩn", "hôi", "nhạt", "cứng", "nặng", "sai", "thiếu", "trễ", "lâu",
    "đẹp", "tốt", "nhanh", "rẻ", "mượt", "mịn", "chắc", "chuẩn", "ổn", "xinh",
    "ngon", "hay", "tuyệt", "ok", "oke", "bình_thường", "tạm", "được", "thôi", "bình thường",
}


def nfc(text):
    return unicodedata.normalize("NFC", text)


def strip_accents(text):
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return stripped.replace("đ", "d").replace("Đ", "D")


def normalize_surface(text):
    text = nfc(text).replace("_", " ").strip().lower()
    text = strip_accents(text)
    return re.sub(r"\s+", " ", text)


NORMALIZED_OPINION_WORDS = {normalize_surface(word) for word in OPINION_WORDS}


def unanimous_polar_conflict(opinions, global_sentiment):
    sentiments = [op.get("sentiment") for op in opinions if op.get("sentiment") in {0, 1, 2}]
    if not sentiments or global_sentiment not in {0, 1, 2}:
        return False
    if all(sentiment == 0 for sentiment in sentiments) and global_sentiment == 1:
        return True
    if all(sentiment == 1 for sentiment in sentiments) and global_sentiment == 0:
        return True
    return False


def safe_fix_opinion(text, opinion):
    updated = dict(opinion)
    reasons = []

    target = updated.get("target", "")
    start = updated.get("start", -1)
    end = updated.get("end", -1)

    if not isinstance(target, str):
        return None, ["invalid_target_type"]
    if not isinstance(start, int) or not isinstance(end, int):
        return None, ["invalid_offsets_type"]
    if not (0 <= start <= end <= len(text)):
        return None, ["offset_out_of_bounds"]

    extracted = text[start:end]
    if extracted != target:
        if normalize_surface(extracted) == normalize_surface(target):
            updated["target"] = extracted
            reasons.append("fixed_surface_form_target")
        else:
            return None, ["unsafe_offset_mismatch"]

    cleaned_target = updated["target"].strip()
    if cleaned_target != updated["target"]:
        left_trim = len(updated["target"]) - len(updated["target"].lstrip())
        right_trim = len(updated["target"]) - len(updated["target"].rstrip())
        new_start = start + left_trim
        new_end = end - right_trim
        if 0 <= new_start <= new_end <= len(text) and text[new_start:new_end] == cleaned_target:
            updated["target"] = cleaned_target
            updated["start"] = new_start
            updated["end"] = new_end
            reasons.append("trimmed_target_spaces")
        else:
            return None, ["unsafe_target_spaces"]

    return updated, reasons


def main():
    stats = Counter()
    review_reasons = Counter()
    sample_reviews = {}

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with INPUT_FILE.open(encoding="utf-8") as source, OUTPUT_FILE.open("w", encoding="utf-8") as cleaned_out, REVIEW_FILE.open("w", encoding="utf-8") as review_out:
        for line_no, raw_line in enumerate(source, 1):
            line = raw_line.strip()
            if not line:
                continue
            stats["total_records"] += 1
            record = json.loads(line)
            text = nfc(record.get("text", ""))
            opinions = record.get("opinions", [])

            updated_record = dict(record)
            updated_record["text"] = text
            fixed_opinions = []
            row_review_reasons = []

            for opinion in opinions:
                target = str(opinion.get("target", ""))
                if normalize_surface(target) in NORMALIZED_OPINION_WORDS:
                    stats["removed_opinion_word"] += 1
                    continue

                fixed_opinion, reasons = safe_fix_opinion(text, opinion)
                if fixed_opinion is None:
                    row_review_reasons.extend(reasons)
                    continue

                fixed_opinions.append(fixed_opinion)
                for reason in reasons:
                    stats[reason] += 1

            if not fixed_opinions:
                row_review_reasons.append("empty_after_safe_fix")

            if unanimous_polar_conflict(fixed_opinions, updated_record.get("global_sentiment", -1)):
                row_review_reasons.append("unanimous_global_conflict")

            if row_review_reasons:
                stats["review_records"] += 1
                for reason in sorted(set(row_review_reasons)):
                    review_reasons[reason] += 1
                    sample_reviews.setdefault(reason, []).append(line_no)
                review_out.write(
                    json.dumps(
                        {
                            "line_no": line_no,
                            "review_reasons": sorted(set(row_review_reasons)),
                            "row": record,
                            "candidate": {**updated_record, "opinions": fixed_opinions},
                        },
                        ensure_ascii=False,
                    ) + "\n"
                )
                continue

            updated_record["opinions"] = fixed_opinions
            cleaned_out.write(json.dumps(updated_record, ensure_ascii=False) + "\n")
            stats["clean_records"] += 1

    report = {
        "input_file": str(INPUT_FILE),
        "output_file": str(OUTPUT_FILE),
        "review_file": str(REVIEW_FILE),
        "total_records": stats["total_records"],
        "clean_records": stats["clean_records"],
        "review_records": stats["review_records"],
        "fixed_surface_form_target": stats["fixed_surface_form_target"],
        "trimmed_target_spaces": stats["trimmed_target_spaces"],
        "removed_opinion_word": stats["removed_opinion_word"],
        "review_reason_counts": dict(review_reasons),
        "sample_review_lines": {reason: lines[:10] for reason, lines in sample_reviews.items()},
    }
    REPORT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()