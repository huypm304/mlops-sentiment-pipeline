import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


DEFAULT_INPUT = Path("data/processed/data_train_v5.jsonl")
ERROR_TYPES = {
    "E1": "Offset sai",
    "E2": "Target co space thua",
    "E3": "Target la opinion word",
    "E4": "Duplicate aspect",
    "E5": "Sentiment sai ro rang",
    "E6": "Global conflict aspect",
    "E7": "Khong co opinions",
    "E8": "Text qua ngan",
}
SENTIMENT_NAME = {0: "NEG", 1: "POS", 2: "NEU"}

NEG_WORDS = {
    "te", "xau", "kem", "cham", "dat", "toi", "do", "loi", "mong", "rong", "nho",
    "to", "ban", "hoi", "nhat", "cung", "nang", "sai", "thieu", "tre", "lau",
}
POS_WORDS = {
    "dep", "tot", "nhanh", "re", "muot", "min", "chac", "chuan", "on", "xinh",
    "ngon", "hay", "tuyet", "ok", "oke",
}
NEU_WORDS = {"binh thuong", "tam", "duoc", "thoi", "binh_thuong"}

NEG_KEYWORDS = [
    "khong giong", "khong dung", "khong dep", "that vong",
    "te hai", "te_hai", "te", "xau", "kem", "cham", "dat", "toi", "do",
    "loi", "mong", "thieu", "sai", "tre", "lau", "hong", "rach", "ban", "hoi", "buc",
]
POS_KEYWORDS = [
    "nhiet tinh", "tan tinh", "than thien", "de thuong", "hai long", "hoan hao", "xuat sac",
    "dep", "tot", "nhanh", "re", "muot", "tuyet", "xinh", "ngon", "chat", "ung",
    "thich", "chuan", "ok", "oke",
]
NEU_KEYWORDS = [
    "binh thuong thoi", "khac phuc duoc", "tam duoc", "cung duoc", "tam on", "cung ok",
    "binh thuong", "on",
]


def nfc(text):
    return unicodedata.normalize("NFC", text)


def deaccent(text):
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    return stripped.replace("đ", "d").replace("Đ", "D")


def normalize_text(text):
    text = nfc(text).lower().replace("_", " ")
    text = deaccent(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize_with_offsets(text):
    return [(match.group(0), match.start(), match.end()) for match in re.finditer(r"\S+", text)]


def find_token_window(tokens, start, end, radius=5):
    token_indexes = []
    for idx, (_, token_start, token_end) in enumerate(tokens):
        if max(token_start, start) < min(token_end, end):
            token_indexes.append(idx)
    if not token_indexes:
        return None, None, []
    lo = max(0, token_indexes[0] - radius)
    hi = min(len(tokens) - 1, token_indexes[-1] + radius)
    window_tokens = [token for token, _, _ in tokens[lo : hi + 1]]
    return lo, hi, window_tokens


def keyword_flags(context):
    normalized = normalize_text(context)
    neg = any(keyword in normalized for keyword in NEG_KEYWORDS)
    pos = any(keyword in normalized for keyword in POS_KEYWORDS)
    neu = any(keyword in normalized for keyword in NEU_KEYWORDS)
    return neg, pos, neu


def recommend_sentiment(neg, pos, neu, current_sentiment):
    active = int(neg) + int(pos) + int(neu)
    if active != 1:
        return None
    if neg and current_sentiment == 1:
        return 0
    if pos and current_sentiment == 0:
        return 1
    if neu and current_sentiment == 1:
        return 2
    return None


def format_percent(part, total):
    if total == 0:
        return "0.00"
    return f"{(part / total) * 100:.2f}"


def default_outputs(input_path):
    stem = input_path.stem
    return (
        input_path.with_name(f"{stem}.audit_summary.md"),
        input_path.with_name(f"{stem}.audit_errors.jsonl"),
    )


def append_error(record_errors, error_type, detail, opinion_idx):
    record_errors.append({"type": error_type, "detail": detail, "opinion_idx": opinion_idx})


def top_examples(items, limit):
    return items[:limit] if items else []


def build_summary(input_name, total_records, records_with_errors, counts, detail_store):
    lines = [
        "# Data Quality Audit Report",
        f"**File**: {input_name}",
        f"**Total records**: {total_records}",
        f"**Records co loi**: {records_with_errors} ({format_percent(records_with_errors, total_records)}%)",
        "",
        "---",
        "",
        "## Tong hop theo loai loi",
        "",
        "| Ma | Mo ta | So records | % |",
        "|----|-------|------------|---|",
    ]
    for error_type in ["E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8"]:
        lines.append(
            f"| {error_type} | {ERROR_TYPES[error_type]} | {counts[error_type]} | {format_percent(counts[error_type], total_records)}% |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## Phan tich chi tiet",
        "",
        "### E1 - Offset sai",
    ])
    e1_examples = top_examples(detail_store["E1_examples"], 5)
    if e1_examples:
        for line_no, text, target, extracted in e1_examples:
            lines.append(f'- line {line_no}: text="{text}" | target="{target}" | extracted="{extracted}"')
    else:
        lines.append("- Khong phat hien vi du.")

    lines.extend(["", "### E2 - Target co space thua"])
    e2_examples = top_examples(detail_store["E2_examples"], 5)
    if e2_examples:
        for line_no, target, stripped in e2_examples:
            lines.append(f'- line {line_no}: target="{target}" -> nen la "{stripped}"')
    else:
        lines.append("- Khong phat hien vi du.")

    lines.extend(["", "### E3 - Target la opinion word"])
    if detail_store["E3_targets"]:
        for target, count in detail_store["E3_targets"].most_common(10):
            lines.append(f'- "{target}": {count} lan')
    else:
        lines.append("- Khong phat hien vi du.")

    lines.extend(["", "### E4 - Duplicate aspect"])
    e4_examples = top_examples(detail_store["E4_examples"], 5)
    if e4_examples:
        for line_no, text, aspect, repeats in e4_examples:
            lines.append(f'- line {line_no}: "{text}" -> aspect {aspect} xuat hien {repeats} lan')
    else:
        lines.append("- Khong phat hien vi du.")

    lines.extend(["", "### E5 - Sentiment sai ro rang"])
    e5_examples = top_examples(detail_store["E5_examples"], 10)
    if e5_examples:
        for line_no, target, context, predicted, suggested in e5_examples:
            lines.append(
                f'- line {line_no}: target="{target}" | context="{context}" | predict={predicted} | nen la {suggested}'
            )
    else:
        lines.append("- Khong phat hien vi du.")

    lines.extend(["", "### E6 - Global conflict"])
    e6_examples = top_examples(detail_store["E6_examples"], 5)
    if e6_examples:
        for line_no, sentiments, global_sentiment in e6_examples:
            lines.append(f"- line {line_no}: aspects={sentiments} | global={global_sentiment}")
    else:
        lines.append("- Khong phat hien vi du.")

    lines.extend([
        "",
        "---",
        "",
        "## Uoc tinh tac dong den training",
        "",
        "- E1 + E5 la nghiem trong nhat -> anh huong truc tiep den Span F1 (E1) va Sentiment F1 (E5)",
        "- E2 + E3 anh huong nhe hon, fix bang post-processing",
        "- E4 + E6 gay confusion cho model khi hoc",
        "",
        "---",
        "",
        "## Khuyen nghi uu tien",
        "",
    ])

    ranked = sorted(
        ((error_type, counts[error_type], ERROR_TYPES[error_type]) for error_type in ERROR_TYPES),
        key=lambda item: item[1],
        reverse=True,
    )
    recommendations = []
    for error_type, count, description in ranked:
        if count == 0:
            continue
        if error_type == "E1":
            recommendations.append(f"Uu tien xu ly {description} ({count} records) vi day la loi supervision span truc tiep.")
        elif error_type == "E5":
            recommendations.append(f"Ra soat {description} ({count} records) truoc khi train lai vi no lam lech sentiment head.")
        elif error_type == "E6":
            recommendations.append(f"Can tach va kiem tra {description} ({count} records) vi global head dang hoc tu nhan mau thuan.")
        elif error_type == "E8":
            recommendations.append(f"Can nhac loai rieng {description} ({count} records) vi context qua it de hoc on dinh.")
        else:
            recommendations.append(f"Lam sach {description} ({count} records) de giam noise annotation.")
        if len(recommendations) == 4:
            break
    if not recommendations:
        recommendations.append("Khong phat hien loi dang ke.")
    for idx, rec in enumerate(recommendations, 1):
        lines.append(f"{idx}. {rec}")
    lines.append("")
    return "\n".join(lines)


def audit_file(input_path, summary_path, errors_path):
    opinion_words = {normalize_text(word) for word in NEG_WORDS | POS_WORDS | NEU_WORDS}
    counts = Counter({error_type: 0 for error_type in ERROR_TYPES})
    detail_store = {
        "E1_examples": [],
        "E2_examples": [],
        "E3_targets": Counter(),
        "E4_examples": [],
        "E5_examples": [],
        "E6_examples": [],
    }
    total_records = 0
    records_with_errors = 0

    with input_path.open(encoding="utf-8") as source, errors_path.open("w", encoding="utf-8") as error_out:
        for line_no, line in enumerate(source, 1):
            line = line.strip()
            if not line:
                continue
            total_records += 1
            if total_records % 1000 == 0:
                print(f"Processed {total_records} records...")
            record = json.loads(line)
            text = nfc(record["text"])
            opinions = record.get("opinions", [])
            record_errors = []
            record_error_types = set()
            tokens = tokenize_with_offsets(text)

            if len(tokens) <= 2:
                append_error(record_errors, "E8", f"Text chi co {len(tokens)} tokens", -1)
                record_error_types.add("E8")

            if not opinions:
                append_error(record_errors, "E7", "Record khong co opinions", -1)
                record_error_types.add("E7")

            aspect_counter = Counter(op.get("aspect", "") for op in opinions if op.get("aspect"))
            for aspect, repeats in aspect_counter.items():
                if repeats >= 2:
                    append_error(record_errors, "E4", f'Aspect "{aspect}" xuat hien {repeats} lan', -1)
                    record_error_types.add("E4")
                    if len(detail_store["E4_examples"]) < 5:
                        detail_store["E4_examples"].append((line_no, text, aspect, repeats))

            aspect_sentiments = []
            for opinion_idx, op in enumerate(opinions):
                target = op.get("target", "")
                start = op.get("start", -1)
                end = op.get("end", -1)
                sentiment = op.get("sentiment", -1)
                normalized_target = normalize_text(target)

                if 0 <= start <= end <= len(text):
                    extracted = text[start:end]
                else:
                    extracted = "<oob>"
                if extracted != target:
                    append_error(record_errors, "E1", f'target="{target}" nhung text[{start}:{end}]="{extracted}"', opinion_idx)
                    record_error_types.add("E1")
                    if len(detail_store["E1_examples"]) < 5:
                        detail_store["E1_examples"].append((line_no, text, target, extracted))

                stripped = target.strip()
                if target != stripped:
                    append_error(record_errors, "E2", f'target="{target}" co space thua', opinion_idx)
                    record_error_types.add("E2")
                    if len(detail_store["E2_examples"]) < 5:
                        detail_store["E2_examples"].append((line_no, target, stripped))

                if normalized_target in opinion_words:
                    append_error(record_errors, "E3", f'target="{target}" la opinion word', opinion_idx)
                    record_error_types.add("E3")
                    detail_store["E3_targets"][target] += 1

                if sentiment in {0, 1, 2}:
                    aspect_sentiments.append(sentiment)

                if sentiment in {0, 1, 2} and extracted != "<oob>":
                    _, _, window_tokens = find_token_window(tokens, start, end)
                    if window_tokens:
                        context = " ".join(window_tokens)
                        neg, pos, neu = keyword_flags(context)
                        suggested = recommend_sentiment(neg, pos, neu, sentiment)
                        if suggested is not None:
                            append_error(
                                record_errors,
                                "E5",
                                f'target="{target}" | context="{context}" | predict={sentiment} | nen la {suggested}',
                                opinion_idx,
                            )
                            record_error_types.add("E5")
                            if len(detail_store["E5_examples"]) < 10:
                                detail_store["E5_examples"].append(
                                    (line_no, target, context, sentiment, suggested)
                                )

            global_sentiment = record.get("global_sentiment", -1)
            if aspect_sentiments:
                if all(sent == 0 for sent in aspect_sentiments) and global_sentiment == 1:
                    append_error(record_errors, "E6", "Tat ca aspects la NEG nhung global la POS", -1)
                    record_error_types.add("E6")
                    if len(detail_store["E6_examples"]) < 5:
                        detail_store["E6_examples"].append((line_no, aspect_sentiments, global_sentiment))
                elif all(sent == 1 for sent in aspect_sentiments) and global_sentiment == 0:
                    append_error(record_errors, "E6", "Tat ca aspects la POS nhung global la NEG", -1)
                    record_error_types.add("E6")
                    if len(detail_store["E6_examples"]) < 5:
                        detail_store["E6_examples"].append((line_no, aspect_sentiments, global_sentiment))

            if record_errors:
                records_with_errors += 1
                for error_type in record_error_types:
                    counts[error_type] += 1
                error_out.write(
                    json.dumps(
                        {
                            "line_no": line_no,
                            "text": text,
                            "errors": record_errors,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )

    summary_text = build_summary(input_path.name, total_records, records_with_errors, counts, detail_store)
    summary_path.write_text(summary_text, encoding="utf-8")
    print(f"Audit complete: {total_records} records, {records_with_errors} records with errors")
    print(f"Summary: {summary_path}")
    print(f"Errors : {errors_path}")


def main():
    parser = argparse.ArgumentParser(description="Audit data_train_v5.jsonl and export a dedicated report")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Input JSONL file")
    parser.add_argument("--summary-output", type=Path, help="Output Markdown summary path")
    parser.add_argument("--errors-output", type=Path, help="Output JSONL errors path")
    args = parser.parse_args()

    summary_output, errors_output = default_outputs(args.input)
    if args.summary_output is not None:
        summary_output = args.summary_output
    if args.errors_output is not None:
        errors_output = args.errors_output

    summary_output.parent.mkdir(parents=True, exist_ok=True)
    errors_output.parent.mkdir(parents=True, exist_ok=True)
    audit_file(args.input, summary_output, errors_output)


if __name__ == "__main__":
    main()