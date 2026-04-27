import argparse
import json
import re
from collections import Counter
from pathlib import Path


DEFAULT_INPUT = Path("data/processed/data_train_v6.jsonl")
DEFAULT_E5_QUEUE = Path("data/processed/data_train_v6.e5_review_queue.jsonl")
DEFAULT_E5_MANUAL_TSV = Path("data/processed/data_train_v6.e5_manual_edit.tsv")
DEFAULT_E6_QUEUE = Path("data/processed/data_train_v6.e6_review_queue.jsonl")
DEFAULT_E6_MANUAL_TSV = Path("data/processed/data_train_v6.e6_manual_edit.tsv")
DEFAULT_E6_OPINION_MANUAL_TSV = Path("data/processed/data_train_v6.e6_opinion_manual_edit.tsv")
DEFAULT_OUTPUT = Path("data/processed/data_train_v6_1.jsonl")
DEFAULT_REPORT = Path("data/processed/data_train_v6_1.build_report.json")


def normalize_text(text):
    return re.sub(r"\s+", " ", str(text)).strip()


def load_jsonl_as_list(path):
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            rows.append(json.loads(line))
    return rows


def iter_tsv_records(path, expected_columns):
    buffer = []
    start_row_no = None
    expected_tabs = expected_columns - 1

    with path.open(encoding="utf-8") as handle:
        for row_no, line in enumerate(handle, 1):
            line = line.rstrip("\n")
            if not buffer and not line:
                continue
            if start_row_no is None:
                start_row_no = row_no
            buffer.append(line)
            joined = "\n".join(buffer)
            if joined.count("\t") < expected_tabs:
                continue

            parts = joined.split("\t")
            if len(parts) != expected_columns:
                raise ValueError(
                    f"Invalid TSV row {start_row_no}: expected {expected_columns} columns, got {len(parts)}"
                )
            yield start_row_no, parts
            buffer = []
            start_row_no = None

    if buffer:
        raise ValueError(f"Dangling TSV row starting at line {start_row_no}")


def parse_e5_tsv(path):
    rows = []
    for row_no, parts in iter_tsv_records(path, 4):
            text, aspect, current_sentiment, reviewed_sentiment = parts
            current_sentiment = int(current_sentiment)
            reviewed_sentiment = int(reviewed_sentiment)
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


def parse_e6_tsv(path):
    rows = []
    for row_no, parts in iter_tsv_records(path, 5):
            text, current_global, reviewed_global, suggested_global, aspect_sentiments = parts
            current_global = int(current_global)
            reviewed_global = int(reviewed_global)
            suggested_global = int(suggested_global)
            rows.append(
                {
                    "row_no": row_no,
                    "text": text,
                    "current_global": current_global,
                    "reviewed_global": reviewed_global,
                    "suggested_global": suggested_global,
                    "aspect_sentiments": aspect_sentiments,
                }
            )
    return rows


def parse_e6_opinion_tsv(path):
    if not path.exists():
        return []

    rows = []
    for row_no, parts in iter_tsv_records(path, 6):
        text, line_no, opinion_idx, aspect, current_sentiment, reviewed_sentiment = parts
        rows.append(
            {
                "row_no": row_no,
                "text": text,
                "line_no": int(line_no),
                "opinion_idx": int(opinion_idx),
                "aspect": aspect,
                "current_sentiment": int(current_sentiment),
                "reviewed_sentiment": int(reviewed_sentiment),
            }
        )
    return rows


def flatten_e5_queue(queue_rows):
    flattened = []
    for queue_idx, queue_row in enumerate(queue_rows, 1):
        for flagged_idx, flagged in enumerate(queue_row.get("flagged_opinions", []), 1):
            flattened.append(
                {
                    "queue_idx": queue_idx,
                    "flagged_idx": flagged_idx,
                    "line_no": queue_row["line_no"],
                    "text": queue_row["text"],
                    "aspect": flagged.get("aspect") or "",
                    "current_sentiment": flagged["current_sentiment"],
                    "opinion_idx": flagged["opinion_idx"],
                }
            )
    return flattened


def validate_e5_alignment(tsv_rows, queue_items):
    if len(tsv_rows) != len(queue_items):
        raise ValueError(
            f"E5 TSV row count ({len(tsv_rows)}) does not match flattened queue count ({len(queue_items)})"
        )

    for index, (tsv_row, queue_item) in enumerate(zip(tsv_rows, queue_items), 1):
        problems = []
        if normalize_text(tsv_row["text"]) != normalize_text(queue_item["text"]):
            problems.append("text")
        if tsv_row["aspect"] != queue_item["aspect"]:
            problems.append("aspect")
        if tsv_row["current_sentiment"] != queue_item["current_sentiment"]:
            problems.append("current_sentiment")
        if problems:
            raise ValueError(
                "E5 TSV/queue mismatch at item "
                f"{index}: line_no={queue_item['line_no']} opinion_idx={queue_item['opinion_idx']} "
                f"fields={','.join(problems)}"
            )


def validate_e6_alignment(tsv_rows, queue_rows):
    if len(tsv_rows) != len(queue_rows):
        raise ValueError(f"E6 TSV row count ({len(tsv_rows)}) does not match queue count ({len(queue_rows)})")

    for index, (tsv_row, queue_row) in enumerate(zip(tsv_rows, queue_rows), 1):
        problems = []
        if normalize_text(tsv_row["text"]) != normalize_text(queue_row["text"]):
            problems.append("text")
        if tsv_row["current_global"] != queue_row["global_sentiment"]:
            problems.append("current_global")
        if tsv_row["suggested_global"] != queue_row["suggested_global_sentiment"]:
            problems.append("suggested_global")
        if problems:
            raise ValueError(
                f"E6 TSV/queue mismatch at item {index}: line_no={queue_row['line_no']} fields={','.join(problems)}"
            )


def apply_e5_reviews(base_records, tsv_rows, queue_items):
    updated_records = [dict(record) for record in base_records]
    changed_counter = Counter()
    changed_items = 0
    unchanged_items = 0

    for tsv_row, queue_item in zip(tsv_rows, queue_items):
        record_idx = queue_item["line_no"] - 1
        opinion_idx = queue_item["opinion_idx"]
        record = updated_records[record_idx]
        opinions = list(record.get("opinions", []))
        opinion = dict(opinions[opinion_idx])
        actual_current = opinion.get("sentiment")
        if actual_current != tsv_row["current_sentiment"]:
            raise ValueError(
                f"Base data drift at line {queue_item['line_no']} opinion {opinion_idx}: "
                f"expected {tsv_row['current_sentiment']}, got {actual_current}"
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


def apply_e6_reviews(base_records, tsv_rows, queue_rows):
    updated_records = [dict(record) for record in base_records]
    changed_counter = Counter()
    changed_items = 0
    unchanged_items = 0

    for tsv_row, queue_row in zip(tsv_rows, queue_rows):
        record_idx = queue_row["line_no"] - 1
        record = dict(updated_records[record_idx])
        actual_current = record.get("global_sentiment")
        if actual_current != tsv_row["current_global"]:
            raise ValueError(
                f"Base data drift at line {queue_row['line_no']}: expected global {tsv_row['current_global']}, got {actual_current}"
            )

        reviewed = tsv_row["reviewed_global"]
        if reviewed == actual_current:
            unchanged_items += 1
            continue

        record["global_sentiment"] = reviewed
        updated_records[record_idx] = record
        changed_items += 1
        changed_counter[f"{actual_current}->{reviewed}"] += 1

    return updated_records, changed_items, unchanged_items, changed_counter


def apply_e6_opinion_reviews(base_records, opinion_rows):
    updated_records = [dict(record) for record in base_records]
    changed_counter = Counter()
    changed_items = 0
    unchanged_items = 0

    for row in opinion_rows:
        record_idx = row["line_no"] - 1
        record = dict(updated_records[record_idx])
        if normalize_text(record.get("text", "")) != normalize_text(row["text"]):
            raise ValueError(f"E6 opinion TSV text mismatch at line {row['line_no']}")

        opinions = list(record.get("opinions", []))
        if not (0 <= row["opinion_idx"] < len(opinions)):
            raise IndexError(
                f"Opinion index out of range for line {row['line_no']}: {row['opinion_idx']} not in {len(opinions)}"
            )

        opinion = dict(opinions[row["opinion_idx"]])
        if str(opinion.get("aspect", "")) != row["aspect"]:
            raise ValueError(
                f"E6 opinion TSV aspect mismatch at line {row['line_no']} opinion {row['opinion_idx']}"
            )

        actual_current = opinion.get("sentiment")
        if actual_current != row["current_sentiment"]:
            raise ValueError(
                f"E6 opinion drift at line {row['line_no']} opinion {row['opinion_idx']}: expected {row['current_sentiment']}, got {actual_current}"
            )

        reviewed = row["reviewed_sentiment"]
        if reviewed == actual_current:
            unchanged_items += 1
            continue

        opinion["sentiment"] = reviewed
        opinions[row["opinion_idx"]] = opinion
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
    parser = argparse.ArgumentParser(description="Build data_train_v6_1.jsonl from reviewed E5 and E6 TSV files")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--e5-queue", type=Path, default=DEFAULT_E5_QUEUE)
    parser.add_argument("--e5-manual-tsv", type=Path, default=DEFAULT_E5_MANUAL_TSV)
    parser.add_argument("--e6-queue", type=Path, default=DEFAULT_E6_QUEUE)
    parser.add_argument("--e6-manual-tsv", type=Path, default=DEFAULT_E6_MANUAL_TSV)
    parser.add_argument("--e6-opinion-manual-tsv", type=Path, default=DEFAULT_E6_OPINION_MANUAL_TSV)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    base_records = load_jsonl_as_list(args.input)

    e5_queue_rows = load_jsonl_as_list(args.e5_queue)
    e5_tsv_rows = parse_e5_tsv(args.e5_manual_tsv)
    e5_queue_items = flatten_e5_queue(e5_queue_rows)
    validate_e5_alignment(e5_tsv_rows, e5_queue_items)
    updated_records, e5_changed, e5_unchanged, e5_counter = apply_e5_reviews(
        base_records, e5_tsv_rows, e5_queue_items
    )

    e6_queue_rows = load_jsonl_as_list(args.e6_queue)
    e6_tsv_rows = parse_e6_tsv(args.e6_manual_tsv)
    validate_e6_alignment(e6_tsv_rows, e6_queue_rows)
    updated_records, e6_changed, e6_unchanged, e6_counter = apply_e6_reviews(
        updated_records, e6_tsv_rows, e6_queue_rows
    )

    e6_opinion_rows = parse_e6_opinion_tsv(args.e6_opinion_manual_tsv)
    updated_records, e6_op_changed, e6_op_unchanged, e6_op_counter = apply_e6_opinion_reviews(
        updated_records, e6_opinion_rows
    )

    write_jsonl(args.output, updated_records)

    report = {
        "input": str(args.input),
        "e5_queue": str(args.e5_queue),
        "e5_manual_tsv": str(args.e5_manual_tsv),
        "e6_queue": str(args.e6_queue),
        "e6_manual_tsv": str(args.e6_manual_tsv),
        "e6_opinion_manual_tsv": str(args.e6_opinion_manual_tsv),
        "output": str(args.output),
        "total_records": len(base_records),
        "e5_queue_records": len(e5_queue_rows),
        "e5_reviewed_items": len(e5_tsv_rows),
        "e5_changed_items": e5_changed,
        "e5_unchanged_items": e5_unchanged,
        "e5_changed_transitions": dict(e5_counter),
        "e6_queue_records": len(e6_queue_rows),
        "e6_reviewed_items": len(e6_tsv_rows),
        "e6_changed_items": e6_changed,
        "e6_unchanged_items": e6_unchanged,
        "e6_changed_transitions": dict(e6_counter),
        "e6_opinion_reviewed_items": len(e6_opinion_rows),
        "e6_opinion_changed_items": e6_op_changed,
        "e6_opinion_unchanged_items": e6_op_unchanged,
        "e6_opinion_changed_transitions": dict(e6_op_counter),
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()