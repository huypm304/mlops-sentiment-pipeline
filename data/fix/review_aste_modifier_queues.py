#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ASTE_FILE = Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/data_train_v8_aste.jsonl")
HOI_QUEUE = Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/data_train_v8_aste.review.hoi_adj.jsonl")
QUA_QUEUE = Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/data_train_v8_aste.review.qua_adj.jsonl")
DECISIONS_FILE = Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/data_train_v8_aste.modifier_review.jsonl")
MERGED_FILE = Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/data_train_v8_aste.modifier_merged.jsonl")
REPORT_FILE = Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/data_train_v8_aste.modifier_review.report.json")
AUTO_DECISIONS_FILE = Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/data_train_v8_aste.modifier_auto_review.jsonl")
AUTO_MERGED_FILE = Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/data_train_v8_aste.modifier_auto_merged.jsonl")
AUTO_REPORT_FILE = Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/data_train_v8_aste.modifier_auto_review.report.json")
FORCE_AUTO_DECISIONS_FILE = Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/data_train_v8_aste.modifier_force_auto_review.jsonl")
FORCE_AUTO_MERGED_FILE = Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/data_train_v8_aste.modifier_force_auto_merged.jsonl")
FORCE_AUTO_REPORT_FILE = Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/data_train_v8_aste.modifier_force_auto_review.report.json")

BOUNDARY_PATTERN = re.compile(
    r"[,.;!?\n]|\b(?:nhưng|tuy_nhiên|tuy|bù_lại|trái_lại|song|cơ_mà|còn)\b",
    re.IGNORECASE,
)
TOKEN_PATTERN = re.compile(r"\S+")
STRIP_CHARS = " \t\r\n.,;:!?()[]{}\"'“”‘’👍🙂☺️"

QUEUE_PATTERNS = {
    "hoi_adj": [
        re.compile(r"\bhơi\s+\S+(?:\s+\S+){0,3}", re.IGNORECASE),
        re.compile(r"\bkhá\s+\S+(?:\s+\S+){0,3}", re.IGNORECASE),
    ],
    "qua_adj": [
        re.compile(r"\bquá\s+\S+(?:\s+\S+){0,3}", re.IGNORECASE),
        re.compile(r"\bkhông\s+quá\s+\S+(?:\s+\S+){0,3}", re.IGNORECASE),
        re.compile(r"\brất\s+\S+(?:\s+\S+){0,3}", re.IGNORECASE),
    ],
}
QUEUE_START_TOKENS = {
    "hoi_adj": {"hơi", "khá"},
    "qua_adj": {"quá", "rất", "không"},
}
BLOCKED_TOKENS = {"nhưng", "tuy_nhiên", "song", "cơ_mà", "bù_lại", "trái_lại"}
GENERIC_FORCE_PATTERNS = {
    0: [
        re.compile(r"\b(?:rất\s+|quá\s+|khá\s+|hơi\s+)?(?:tệ|xấu|kém|lag|giật|đơ|nóng|yếu|lỗi|trễ|chậm|khó|khó_chịu|khó_khăn|chán|buồn|tiếc|dỏm|tróc(?:\s+màu)?|tụt|khựng|dừng|thất_vọng|rắc_rối|lô\s+lắm|củ_xèm|quá\s+chán)(?:\s+\S+){0,3}", re.IGNORECASE),
        re.compile(r"\b(?:không\s+(?:được|ổn|vừa|như|đẹp|mượt|tốt)|tự_động\s+dừng|tự\s+động\s+dừng)(?:\s+\S+){0,3}", re.IGNORECASE),
    ],
    1: [
        re.compile(r"\b(?:rất\s+|quá\s+|khá\s+|hơi\s+)?(?:đẹp|tốt|mượt|nhanh|nét|trâu|khỏe|nhiệt_tình|thân_thiện|dễ_chịu|ổn|hữu_ích|hợp\s+l[ií]|hợp_l[ií]|hài\s+lòng|chất\s+lượng|khỏi\s+chê|vừa\s+tay|đầm\s+tay)(?:\s+\S+){0,3}", re.IGNORECASE),
    ],
    2: [
        re.compile(r"\b(?:tạm|ổn|ok|oke|được|đủ\s+dùng|không\s+quá\s+mượt|không\s+khó\s+chịu|nhìn\s+chung\s+đủ\s+dùng|hơi\s+tiếc|phí\s+tiền)(?:\s+\S+){0,3}", re.IGNORECASE),
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare and apply semi-automatic review decisions for hoi_adj and qua_adj queues.")
    parser.add_argument("mode", choices=["prepare", "apply", "auto"])
    parser.add_argument("--aste-file", type=Path, default=ASTE_FILE)
    parser.add_argument("--hoi-queue", type=Path, default=HOI_QUEUE)
    parser.add_argument("--qua-queue", type=Path, default=QUA_QUEUE)
    parser.add_argument("--decisions-file", type=Path, default=DECISIONS_FILE)
    parser.add_argument("--merged-file", type=Path, default=MERGED_FILE)
    parser.add_argument("--report-file", type=Path, default=REPORT_FILE)
    parser.add_argument("--auto-decisions-file", type=Path, default=AUTO_DECISIONS_FILE)
    parser.add_argument("--auto-merged-file", type=Path, default=AUTO_MERGED_FILE)
    parser.add_argument("--auto-report-file", type=Path, default=AUTO_REPORT_FILE)
    parser.add_argument("--force-decisions-file", type=Path, default=FORCE_AUTO_DECISIONS_FILE)
    parser.add_argument("--force-merged-file", type=Path, default=FORCE_AUTO_MERGED_FILE)
    parser.add_argument("--force-report-file", type=Path, default=FORCE_AUTO_REPORT_FILE)
    parser.add_argument("--force-fill", action="store_true")
    return parser.parse_args()


def normalize_text(value: str) -> str:
    value = value.lower().replace("_", " ")
    value = re.sub(r"\s+", " ", value).strip(STRIP_CHARS)
    return value


def token_spans(text: str) -> list[tuple[str, int, int]]:
    return [(m.group(0), m.start(), m.end()) for m in TOKEN_PATTERN.finditer(text)]


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


def overlaps(span_a: tuple[int, int], span_b: tuple[int, int]) -> bool:
    return max(span_a[0], span_b[0]) < min(span_a[1], span_b[1])


def locate_queue_name(path: Path) -> str:
    return "hoi_adj" if "hoi_adj" in path.name else "qua_adj"


def is_clean_modifier_phrase(opinion: str, queue_name: str) -> bool:
    normalized = normalize_text(opinion)
    if not normalized:
        return False
    tokens = normalized.split()
    if not tokens:
        return False
    if tokens[0] not in QUEUE_START_TOKENS[queue_name]:
        return False
    if any(token in BLOCKED_TOKENS for token in tokens[1:]):
        return False
    if len(tokens) > 4:
        return False
    return True


def collect_candidates(text: str, target_span: list[int], queue_name: str) -> list[dict]:
    start, end = target_span
    clause_start, clause_end = find_clause_bounds(text, start, end)
    search_start = max(0, clause_start - 40)
    search_end = min(len(text), clause_end + 60)
    clause_text = text[search_start:search_end]
    target = (start, end)
    candidates: list[dict] = []
    seen: set[tuple[int, int]] = set()

    for pattern in QUEUE_PATTERNS[queue_name]:
        for match in pattern.finditer(clause_text):
            span = (search_start + match.start(), search_start + match.end())
            if overlaps(span, target):
                continue
            if span in seen:
                continue
            seen.add(span)
            opinion = text[span[0]:span[1]].strip(STRIP_CHARS)
            if not is_clean_modifier_phrase(opinion, queue_name):
                continue
            distance = min(abs(span[0] - end), abs(start - span[1])) if span[1] <= start or span[0] >= end else 0
            score = 1000 - distance
            candidates.append(
                {
                    "opinion": opinion,
                    "opinion_span": [span[0], span[1]],
                    "source": f"regex:{pattern.pattern}",
                    "score": score,
                }
            )

    tokens = token_spans(text)
    overlapping = [idx for idx, (_, s, e) in enumerate(tokens) if overlaps((s, e), target)]
    if overlapping:
        left_idx = overlapping[0]
        right_idx = overlapping[-1]
        for width in range(1, 5):
            if right_idx + width < len(tokens):
                span = (tokens[right_idx + 1][1], tokens[min(len(tokens) - 1, right_idx + width)][2])
                clean_span = (tokens[right_idx + 1][1], tokens[min(len(tokens) - 1, right_idx + width)][2])
                phrase = text[clean_span[0]:clean_span[1]].strip(STRIP_CHARS)
                if phrase and clean_span not in seen and any(p.search(phrase) for p in QUEUE_PATTERNS[queue_name]) and is_clean_modifier_phrase(phrase, queue_name):
                    seen.add(clean_span)
                    candidates.append(
                        {
                            "opinion": phrase,
                            "opinion_span": [clean_span[0], clean_span[1]],
                            "source": f"adjacent:{queue_name}",
                            "score": 100 - width,
                        }
                    )

    candidates.sort(key=lambda item: (-item["score"], item["opinion_span"][0], item["opinion_span"][1]))
    return candidates


def collect_relaxed_candidates(text: str, target_span: list[int], queue_name: str) -> list[dict]:
    start, end = target_span
    search_start = max(0, start - 60)
    search_end = min(len(text), end + 100)
    search_text = text[search_start:search_end]
    target = (start, end)
    candidates: list[dict] = []
    seen: set[tuple[int, int]] = set()

    for pattern in QUEUE_PATTERNS[queue_name]:
        for match in pattern.finditer(search_text):
            span = (search_start + match.start(), search_start + match.end())
            if overlaps(span, target):
                continue
            if span in seen:
                continue
            seen.add(span)
            opinion = text[span[0]:span[1]].strip(STRIP_CHARS)
            if not opinion:
                continue
            distance = min(abs(span[0] - end), abs(start - span[1])) if span[1] <= start or span[0] >= end else 0
            token_len = len(normalize_text(opinion).split())
            score = 800 - distance - max(0, token_len - 3) * 3
            candidates.append(
                {
                    "opinion": opinion,
                    "opinion_span": [span[0], span[1]],
                    "source": f"relaxed:{pattern.pattern}",
                    "score": score,
                }
            )

    candidates.sort(key=lambda item: (-item["score"], item["opinion_span"][0], item["opinion_span"][1]))
    return candidates


def collect_force_candidates(text: str, target_span: list[int], sentiment: int) -> list[dict]:
    start, end = target_span
    target = (start, end)
    candidates: list[dict] = []
    seen: set[tuple[int, int]] = set()

    for pattern in GENERIC_FORCE_PATTERNS.get(sentiment, []):
        for match in pattern.finditer(text):
            span = (match.start(), match.end())
            contains_target = span[0] <= start and span[1] >= end and span != target
            if overlaps(span, target) and not contains_target:
                continue
            if span in seen:
                continue
            seen.add(span)
            opinion = text[span[0]:span[1]].strip(STRIP_CHARS)
            if not opinion:
                continue
            distance = min(abs(span[0] - end), abs(start - span[1])) if span[1] <= start or span[0] >= end else 0
            score = 600 - distance - max(0, len(normalize_text(opinion).split()) - 4) * 4
            candidates.append(
                {
                    "opinion": opinion,
                    "opinion_span": [span[0], span[1]],
                    "source": f"force-regex:{pattern.pattern}",
                    "score": score,
                }
            )

    if candidates:
        candidates.sort(key=lambda item: (-item["score"], item["opinion_span"][0], item["opinion_span"][1]))
        return candidates

    # Last-resort fallback: pick the nearest short clause fragment after target, else before target.
    clause_start, clause_end = find_clause_bounds(text, start, end)
    tokens = token_spans(text)
    overlaps_idx = [i for i, (_, s, e) in enumerate(tokens) if overlaps((s, e), target)]
    if not overlaps_idx:
        return []
    left_idx = overlaps_idx[0]
    right_idx = overlaps_idx[-1]
    for direction in ("right", "left"):
        for width in range(1, 4):
            if direction == "right" and right_idx + width < len(tokens):
                span = (tokens[right_idx + 1][1], tokens[min(len(tokens) - 1, right_idx + width)][2])
            elif direction == "left" and left_idx - width >= 0:
                span = (tokens[left_idx - width][1], tokens[left_idx - 1][2])
            else:
                continue
            if span[0] < clause_start or span[1] > clause_end:
                continue
            phrase = text[span[0]:span[1]].strip(STRIP_CHARS)
            if not phrase:
                continue
            return [{"opinion": phrase, "opinion_span": [span[0], span[1]], "source": f"force-nearest:{direction}", "score": 100 - width}]
    return []


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def prepare(args: argparse.Namespace) -> None:
    decisions = []
    total_items = 0
    auto_accept = 0

    for queue_path in [args.hoi_queue, args.qua_queue]:
        queue_name = locate_queue_name(queue_path)
        for record in load_jsonl(queue_path):
            for triplet_idx, triplet in enumerate(record["triplets"]):
                if triplet["opinion_span"] != [-1, -1]:
                    continue
                suggestions = collect_candidates(record["text"], triplet["target_span"], queue_name)
                selected = suggestions[0] if suggestions else {"opinion": "", "opinion_span": [-1, -1], "source": "none", "score": -1}
                decision = "accept" if suggestions and selected["source"].startswith("regex:") and is_clean_modifier_phrase(selected["opinion"], queue_name) else "skip"
                if decision == "accept":
                    auto_accept += 1
                total_items += 1
                decisions.append(
                    {
                        "review_id": f"{record['line_no']}:{queue_name}:{triplet_idx}",
                        "line_no": record["line_no"],
                        "queue": queue_name,
                        "text": record["text"],
                        "aspect": triplet["aspect"],
                        "target": triplet["target"],
                        "target_span": triplet["target_span"],
                        "sentiment": triplet["sentiment"],
                        "current_opinion": triplet["opinion"],
                        "current_opinion_span": triplet["opinion_span"],
                        "selected_opinion": selected["opinion"],
                        "selected_opinion_span": selected["opinion_span"],
                        "selected_source": selected["source"],
                        "decision": decision,
                        "suggestions": suggestions[:5],
                        "notes": "",
                    }
                )

    with open(args.decisions_file, "w", encoding="utf-8") as handle:
        for row in decisions:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    report = {
        "mode": "prepare",
        "decisions_file": str(args.decisions_file),
        "total_review_items": total_items,
        "auto_accept_items": auto_accept,
        "skip_items": total_items - auto_accept,
    }
    with open(args.report_file, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def auto_review(args: argparse.Namespace) -> None:
    decisions = []
    total_items = 0
    auto_accept = 0
    unresolved = 0

    for queue_path in [args.hoi_queue, args.qua_queue]:
        queue_name = locate_queue_name(queue_path)
        for record in load_jsonl(queue_path):
            for triplet_idx, triplet in enumerate(record["triplets"]):
                if triplet["opinion_span"] != [-1, -1]:
                    continue
                suggestions = collect_candidates(record["text"], triplet["target_span"], queue_name)
                if not suggestions:
                    suggestions = collect_relaxed_candidates(record["text"], triplet["target_span"], queue_name)
                if args.force_fill and not suggestions:
                    suggestions = collect_force_candidates(record["text"], triplet["target_span"], triplet["sentiment"])
                selected = suggestions[0] if suggestions else {"opinion": "", "opinion_span": [-1, -1], "source": "none", "score": -1}
                decision = "accept" if suggestions else "skip"
                if decision == "accept":
                    auto_accept += 1
                else:
                    unresolved += 1
                total_items += 1
                decisions.append(
                    {
                        "review_id": f"{record['line_no']}:{queue_name}:{triplet_idx}",
                        "line_no": record["line_no"],
                        "queue": queue_name,
                        "text": record["text"],
                        "aspect": triplet["aspect"],
                        "target": triplet["target"],
                        "target_span": triplet["target_span"],
                        "sentiment": triplet["sentiment"],
                        "current_opinion": triplet["opinion"],
                        "current_opinion_span": triplet["opinion_span"],
                        "selected_opinion": selected["opinion"],
                        "selected_opinion_span": selected["opinion_span"],
                        "selected_source": selected["source"],
                        "decision": decision,
                        "suggestions": suggestions[:5],
                        "notes": "auto-generated",
                    }
                )

    decisions_path = args.force_decisions_file if args.force_fill else args.auto_decisions_file
    merged_path = args.force_merged_file if args.force_fill else args.auto_merged_file
    report_path = args.force_report_file if args.force_fill else args.auto_report_file

    with open(decisions_path, "w", encoding="utf-8") as handle:
        for row in decisions:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    accepted = {
        (
            row["line_no"],
            row["aspect"],
            row["target"],
            tuple(row["target_span"]),
            row["sentiment"],
        ): row
        for row in decisions
        if row["decision"] == "accept" and row["selected_opinion_span"] != [-1, -1]
    }

    applied_count = 0
    with open(args.aste_file, encoding="utf-8") as src, open(merged_path, "w", encoding="utf-8") as out:
        for line_no, line in enumerate(src, start=1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            for triplet in record["triplets"]:
                key = make_key(line_no, triplet)
                if key not in accepted:
                    continue
                decision = accepted[key]
                triplet["opinion"] = decision["selected_opinion"]
                triplet["opinion_span"] = decision["selected_opinion_span"]
                triplet["aspect_opinion_pair"] = f"{triplet['target']} {decision['selected_opinion']}".strip()
                applied_count += 1
            out.write(json.dumps(record, ensure_ascii=False) + "\n")

    report = {
        "mode": "force-auto" if args.force_fill else "auto",
        "auto_decisions_file": str(decisions_path),
        "auto_merged_file": str(merged_path),
        "total_review_items": total_items,
        "auto_accept_items": auto_accept,
        "auto_skip_items": unresolved,
        "applied_updates": applied_count,
    }
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def make_key(line_no: int, triplet: dict) -> tuple:
    return (
        line_no,
        triplet["aspect"],
        triplet["target"],
        tuple(triplet["target_span"]),
        triplet["sentiment"],
    )


def apply(args: argparse.Namespace) -> None:
    decisions = load_jsonl(args.decisions_file)
    accepted = {
        (
            row["line_no"],
            row["aspect"],
            row["target"],
            tuple(row["target_span"]),
            row["sentiment"],
        ): row
        for row in decisions
        if row["decision"] in {"accept", "manual"} and row["selected_opinion_span"] != [-1, -1]
    }

    applied_count = 0
    with open(args.aste_file, encoding="utf-8") as src, open(args.merged_file, "w", encoding="utf-8") as out:
        for line_no, line in enumerate(src, start=1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            for triplet in record["triplets"]:
                key = make_key(line_no, triplet)
                if key not in accepted:
                    continue
                decision = accepted[key]
                triplet["opinion"] = decision["selected_opinion"]
                triplet["opinion_span"] = decision["selected_opinion_span"]
                triplet["aspect_opinion_pair"] = f"{triplet['target']} {decision['selected_opinion']}".strip()
                applied_count += 1
            out.write(json.dumps(record, ensure_ascii=False) + "\n")

    report = {
        "mode": "apply",
        "aste_file": str(args.aste_file),
        "decisions_file": str(args.decisions_file),
        "merged_file": str(args.merged_file),
        "accepted_decisions": len(accepted),
        "applied_updates": applied_count,
    }
    with open(args.report_file, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def main() -> None:
    args = parse_args()
    if args.mode == "prepare":
        prepare(args)
    elif args.mode == "apply":
        apply(args)
    else:
        auto_review(args)


if __name__ == "__main__":
    main()