import argparse
import json
import re
from collections import Counter
from pathlib import Path


DEFAULT_INPUT = Path("data/processed/data_train_v5.autofixed.jsonl")
DEFAULT_QUEUE = Path("data/processed/data_train_v5.e5_review_queue.jsonl")
DEFAULT_MANUAL_TSV = Path("data/processed/data_train_v5.e5_manual_edit.tsv")
DEFAULT_OUTPUT = Path("data/processed/data_train_v6.jsonl")
DEFAULT_REPORT = Path("data/processed/data_train_v6.build_report.json")


def normalize_text(text):
    return re.sub(r"\s+", " ", str(text)).strip()


def load_jsonl_as_list(path):
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.rstrip("\n")
            if not line.strip():
                continue
            rows.append(json.loads(line))
    return rows


def parse_tsv(path):
    rows = []
    with path.open(encoding="utf-8") as handle:
        for row_no, line in enumerate(handle, 1):
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) != 4:
                raise ValueError(f"Invalid TSV row {row_no}: expected 4 columns, got {len(parts)}")
            text, aspect, current_sentiment, reviewed_sentiment = parts
            try:
                current_sentiment = int(current_sentiment)
                reviewed_sentiment = int(reviewed_sentiment)
            except ValueError as exc:
                raise ValueError(f"Invalid sentiment value on TSV row {row_no}") from exc
            if current_sentiment not in {0, 1, 2} or reviewed_sentiment not in {0, 1, 2}:
                raise ValueError(f"Out-of-range sentiment on TSV row {row_no}")
            rows.append(
                {
                    "row_no": row_no,
                    "text": text,
                    "aspect": aspect,
                    "current_sentiment": current_sentiment,
                    "reviewed_sentiment": reviewed_sentiment,
                }
            )
    return rows


def flatten_queue(queue_rows):
    flattened = []
    for queue_idx, queue_row in enumerate(queue_rows, 1):
        line_no = queue_row["line_no"]
        text = queue_row["text"]
        for flagged_idx, flagged in enumerate(queue_row.get("flagged_opinions", []), 1):
            opinion_idx = flagged["opinion_idx"]
            aspect = flagged.get("aspect")
            current_sentiment = flagged["current_sentiment"]
            flattened.append(
                {
                    "queue_idx": queue_idx,
                    "flagged_idx": flagged_idx,
                    "line_no": line_no,
                    "text": text,
                    "aspect": aspect,
                    "current_sentiment": current_sentiment,
                    "opinion_idx": opinion_idx,
                }
            )
    return flattened


def validate_alignment(tsv_rows, queue_items):
    if len(tsv_rows) != len(queue_items):
        raise ValueError(
            f"TSV row count ({len(tsv_rows)}) does not match flattened queue count ({len(queue_items)})"
        )

    for index, (tsv_row, queue_item) in enumerate(zip(tsv_rows, queue_items), 1):
        problems = []
        if normalize_text(tsv_row["text"]) != normalize_text(queue_item["text"]):
            problems.append("text")
        if tsv_row["aspect"] != (queue_item["aspect"] or ""):
            problems.append("aspect")
        if tsv_row["current_sentiment"] != queue_item["current_sentiment"]:
            problems.append("current_sentiment")
        if problems:
            raise ValueError(
                "TSV/queue mismatch at item "
                f"{index}: line_no={queue_item['line_no']} opinion_idx={queue_item['opinion_idx']} "
                f"fields={','.join(problems)}"
            )


def apply_reviews(base_records, tsv_rows, queue_items):
    updated_records = [dict(record) for record in base_records]
    changed_counter = Counter()
    changed_items = 0
    unchanged_items = 0

    for tsv_row, queue_item in zip(tsv_rows, queue_items):
        record_idx = queue_item["line_no"] - 1
        opinion_idx = queue_item["opinion_idx"]
        record = updated_records[record_idx]
        opinions = list(record.get("opinions", []))
        if not (0 <= opinion_idx < len(opinions)):
            raise IndexError(
                f"Opinion index out of range for line {queue_item['line_no']}: {opinion_idx} not in {len(opinions)}"
            )

        opinion = dict(opinions[opinion_idx])
        actual_current = opinion.get("sentiment")
        if actual_current != tsv_row["current_sentiment"]:
            raise ValueError(
                f"Base data drift at line {queue_item['line_no']} opinion {opinion_idx}: "
                f"expected current sentiment {tsv_row['current_sentiment']}, got {actual_current}"
            )

        reviewed = tsv_row["reviewed_sentiment"]
        if reviewed == actual_current:
            unchanged_items += 1
            continue

        opinion["sentiment"] = reviewed
        opinions[opinion_idx] = opinion
        record["opinions"] = opinions
        updated_records[record_idx] = record

        changed_items += 1
        changed_counter[f"{actual_current}->{reviewed}"] += 1

    return updated_records, changed_items, unchanged_items, changed_counter


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Build final data_train_v6.jsonl from reviewed E5 TSV")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Base autofixed dataset")
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE, help="Flattening source for TSV alignment")
    parser.add_argument("--manual-tsv", type=Path, default=DEFAULT_MANUAL_TSV, help="Reviewed TSV file")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Final v6 JSONL output")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT, help="Build report JSON path")
    args = parser.parse_args()

    base_records = load_jsonl_as_list(args.input)
    queue_rows = load_jsonl_as_list(args.queue)
    tsv_rows = parse_tsv(args.manual_tsv)
    queue_items = flatten_queue(queue_rows)

    validate_alignment(tsv_rows, queue_items)
    updated_records, changed_items, unchanged_items, changed_counter = apply_reviews(
        base_records, tsv_rows, queue_items
    )

    write_jsonl(args.output, updated_records)

    report = {
        "input": str(args.input),
        "queue": str(args.queue),
        "manual_tsv": str(args.manual_tsv),
        "output": str(args.output),
        "total_records": len(base_records),
        "queue_records": len(queue_rows),
        "reviewed_items": len(tsv_rows),
        "changed_items": changed_items,
        "unchanged_items": unchanged_items,
        "changed_transitions": dict(changed_counter),
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()