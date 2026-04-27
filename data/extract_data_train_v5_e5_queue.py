import json
import re
from collections import Counter, defaultdict
from pathlib import Path


DATA_FILE = Path("data/processed/data_train_v5.autofixed.jsonl")
AUDIT_FILE = Path("data/processed/data_train_v5.autofixed.audit_errors.jsonl")
QUEUE_FILE = Path("data/processed/data_train_v5.e5_review_queue.jsonl")
SUMMARY_FILE = Path("data/processed/data_train_v5.e5_review_groups.md")

SENTIMENT_NAME = {0: "NEG", 1: "POS", 2: "NEU"}
DETAIL_RE = re.compile(
    r'target="(?P<target>.*?)" \| context="(?P<context>.*?)" \| predict=(?P<predict>-?\d+) \| nen la (?P<suggested>-?\d+)'
)


def load_jsonl(path):
    records = {}
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            records[line_no] = json.loads(line)
    return records


def parse_detail(detail):
    match = DETAIL_RE.search(detail)
    if not match:
        return {
            "target": None,
            "context": None,
            "predict": None,
            "suggested": None,
        }
    data = match.groupdict()
    data["predict"] = int(data["predict"])
    data["suggested"] = int(data["suggested"])
    return data


def format_summary(total_records, grouped_counts, grouped_examples, target_counts, aspect_counts, transition_counts):
    lines = [
        "# E5 Review Queue",
        "**Source**: data_train_v5.autofixed.jsonl",
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

    lines.extend(["", "## Review Groups"])
    if not grouped_counts:
        lines.append("- Không có nhóm nào.")
        return "\n".join(lines) + "\n"

    for group_key, count in grouped_counts.most_common():
        lines.append("")
        lines.append(f"### {group_key} ({count})")
        for item in grouped_examples[group_key][:5]:
            lines.append(
                f'- line {item["line_no"]}: target="{item["target"]}" | aspect={item["aspect"]} | current={item["current"]} | suggested={item["suggested"]}'
            )
            lines.append(f'  text: "{item["text"]}"')
            lines.append(f'  context: "{item["context"]}"')

    return "\n".join(lines) + "\n"


def main():
    records_by_line = load_jsonl(DATA_FILE)
    grouped_counts = Counter()
    target_counts = Counter()
    aspect_counts = Counter()
    transition_counts = Counter()
    grouped_examples = defaultdict(list)
    total_records = 0

    with AUDIT_FILE.open(encoding="utf-8") as audit_in, QUEUE_FILE.open("w", encoding="utf-8") as queue_out:
        for line in audit_in:
            line = line.strip()
            if not line:
                continue
            audit_record = json.loads(line)
            e5_errors = [error for error in audit_record.get("errors", []) if error.get("type") == "E5"]
            if not e5_errors:
                continue

            line_no = audit_record["line_no"]
            source_record = records_by_line.get(line_no)
            if source_record is None:
                raise RuntimeError(f"Missing source record for line {line_no}")

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
                current_name = SENTIMENT_NAME.get(current, str(current))
                suggested_name = SENTIMENT_NAME.get(suggested, str(suggested))
                target = parsed["target"] or (opinion.get("target") if opinion else None) or "<unknown>"
                context = parsed["context"] or ""

                group_key = f"{aspect or 'Unknown'} | {target} | {current_name}->{suggested_name}"
                grouped_counts[group_key] += 1
                target_counts[target] += 1
                if aspect:
                    aspect_counts[aspect] += 1
                transition_counts[f"{current_name}->{suggested_name}"] += 1
                grouped_examples[group_key].append(
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
                        "current_sentiment_name": current_name,
                        "suggested_sentiment": suggested,
                        "suggested_sentiment_name": suggested_name,
                        "context": context,
                        "detail": error.get("detail"),
                        "opinion": opinion,
                    }
                )

            queue_out.write(
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
            total_records += 1

    SUMMARY_FILE.write_text(
        format_summary(total_records, grouped_counts, grouped_examples, target_counts, aspect_counts, transition_counts),
        encoding="utf-8",
    )
    print(json.dumps({
        "queue_file": str(QUEUE_FILE),
        "summary_file": str(SUMMARY_FILE),
        "total_e5_records": total_records,
        "unique_groups": len(grouped_counts),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()