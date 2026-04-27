import json
import re
from collections import Counter
from pathlib import Path


DATA_FILE = Path("data/processed/data_train_v6.jsonl")
AUDIT_FILE = Path("data/processed/data_train_v6.audit_errors.jsonl")

E5_QUEUE_FILE = Path("data/processed/data_train_v6.e5_review_queue.jsonl")
E5_MANUAL_TSV = Path("data/processed/data_train_v6.e5_manual_edit.tsv")
E5_SUMMARY_FILE = Path("data/processed/data_train_v6.e5_review_groups.md")

E6_QUEUE_FILE = Path("data/processed/data_train_v6.e6_review_queue.jsonl")
E6_MANUAL_TSV = Path("data/processed/data_train_v6.e6_manual_edit.tsv")

SENTIMENT_NAME = {0: "NEG", 1: "POS", 2: "NEU"}
DETAIL_RE = re.compile(
    r'target="(?P<target>.*?)" \| context="(?P<context>.*?)" \| predict=(?P<predict>-?\d+) \| nen la (?P<suggested>-?\d+)'
)


def load_jsonl(path):
    rows = {}
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            rows[line_no] = json.loads(line)
    return rows


def parse_detail(detail):
    match = DETAIL_RE.search(detail or "")
    if not match:
        return {"target": None, "context": None, "predict": None, "suggested": None}
    payload = match.groupdict()
    payload["predict"] = int(payload["predict"])
    payload["suggested"] = int(payload["suggested"])
    return payload


def format_e5_summary(total_records, target_counts, aspect_counts, transition_counts, examples):
    lines = [
        "# V6 Remaining E5 Review Queue",
        "**Source**: data_train_v6.jsonl",
        f"**Total E5 records**: {total_records}",
        "",
        "## Top Target Errors",
    ]
    if target_counts:
        for target, count in target_counts.most_common(20):
            lines.append(f'- "{target}": {count} lần')
    else:
        lines.append("- Không có target nào.")

    lines.extend(["", "## Top Aspect Errors"])
    if aspect_counts:
        for aspect, count in aspect_counts.most_common():
            lines.append(f"- {aspect}: {count} lần")
    else:
        lines.append("- Không có aspect nào.")

    lines.extend(["", "## Sentiment Transitions"])
    if transition_counts:
        for transition, count in transition_counts.most_common():
            lines.append(f"- {transition}: {count} lần")
    else:
        lines.append("- Không có transition nào.")

    lines.extend(["", "## Sample Cases"])
    if not examples:
        lines.append("- Không có ví dụ.")
    else:
        for item in examples[:20]:
            lines.append(
                f'- line {item["line_no"]}: aspect={item["aspect"]} | target="{item["target"]}" | current={item["current"]} | suggested={item["suggested"]}'
            )
            lines.append(f'  text: "{item["text"]}"')
            lines.append(f'  context: "{item["context"]}"')
    return "\n".join(lines) + "\n"


def main():
    records_by_line = load_jsonl(DATA_FILE)
    target_counts = Counter()
    aspect_counts = Counter()
    transition_counts = Counter()
    sample_examples = []
    e5_record_count = 0
    e6_record_count = 0

    E5_QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with (
        AUDIT_FILE.open(encoding="utf-8") as audit_in,
        E5_QUEUE_FILE.open("w", encoding="utf-8") as e5_queue_out,
        E5_MANUAL_TSV.open("w", encoding="utf-8") as e5_tsv_out,
        E6_QUEUE_FILE.open("w", encoding="utf-8") as e6_queue_out,
        E6_MANUAL_TSV.open("w", encoding="utf-8") as e6_tsv_out,
    ):
        for line in audit_in:
            line = line.strip()
            if not line:
                continue
            audit_record = json.loads(line)
            line_no = audit_record["line_no"]
            source_record = records_by_line.get(line_no)
            if source_record is None:
                raise RuntimeError(f"Missing source record for line {line_no}")

            e5_errors = [error for error in audit_record.get("errors", []) if error.get("type") == "E5"]
            e6_errors = [error for error in audit_record.get("errors", []) if error.get("type") == "E6"]

            if e5_errors:
                flagged = []
                for error in e5_errors:
                    parsed = parse_detail(error.get("detail", ""))
                    opinion_idx = error.get("opinion_idx", -1)
                    opinion = None
                    if 0 <= opinion_idx < len(source_record.get("opinions", [])):
                        opinion = source_record["opinions"][opinion_idx]

                    aspect = opinion.get("aspect") if opinion else None
                    current = parsed["predict"]
                    suggested = parsed["suggested"]
                    target = parsed["target"] or (opinion.get("target") if opinion else None) or "<unknown>"
                    context = parsed["context"] or ""
                    current_name = SENTIMENT_NAME.get(current, str(current))
                    suggested_name = SENTIMENT_NAME.get(suggested, str(suggested))

                    target_counts[target] += 1
                    if aspect:
                        aspect_counts[aspect] += 1
                    transition_counts[f"{current_name}->{suggested_name}"] += 1
                    sample_examples.append(
                        {
                            "line_no": line_no,
                            "text": source_record.get("text", ""),
                            "target": target,
                            "aspect": aspect or "Unknown",
                            "current": current_name,
                            "suggested": suggested_name,
                            "context": context,
                        }
                    )

                    flagged.append(
                        {
                            "opinion_idx": opinion_idx,
                            "target": target,
                            "aspect": aspect,
                            "current_sentiment": current,
                            "suggested_sentiment": suggested,
                            "context": context,
                            "detail": error.get("detail"),
                            "opinion": opinion,
                        }
                    )
                    e5_tsv_out.write(
                        f'{normalize_text(source_record.get("text", ""))}\t{aspect or ""}\t{current}\t{current}\n'
                    )

                e5_queue_out.write(
                    json.dumps(
                        {
                            "line_no": line_no,
                            "text": source_record.get("text", ""),
                            "global_sentiment": source_record.get("global_sentiment"),
                            "opinions": source_record.get("opinions", []),
                            "flagged_opinions": flagged,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                e5_record_count += 1

            if e6_errors:
                opinion_sentiments = [op.get("sentiment") for op in source_record.get("opinions", [])]
                unanimous_sentiment = opinion_sentiments[0] if opinion_sentiments else source_record.get("global_sentiment")
                aspects_repr = ",".join(str(sentiment) for sentiment in opinion_sentiments)
                e6_queue_out.write(
                    json.dumps(
                        {
                            "line_no": line_no,
                            "text": source_record.get("text", ""),
                            "global_sentiment": source_record.get("global_sentiment"),
                            "opinions": source_record.get("opinions", []),
                            "suggested_global_sentiment": unanimous_sentiment,
                            "errors": e6_errors,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                e6_tsv_out.write(
                    f'{normalize_text(source_record.get("text", ""))}\t{source_record.get("global_sentiment")}\t{source_record.get("global_sentiment")}\t{unanimous_sentiment}\t{aspects_repr}\n'
                )
                e6_record_count += 1

    E5_SUMMARY_FILE.write_text(
        format_e5_summary(e5_record_count, target_counts, aspect_counts, transition_counts, sample_examples),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "e5_queue_file": str(E5_QUEUE_FILE),
                "e5_manual_tsv": str(E5_MANUAL_TSV),
                "e5_summary_file": str(E5_SUMMARY_FILE),
                "e6_queue_file": str(E6_QUEUE_FILE),
                "e6_manual_tsv": str(E6_MANUAL_TSV),
                "e5_record_count": e5_record_count,
                "e6_record_count": e6_record_count,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()