#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


STRIP_CHARS = " \t\r\n.,;:!?()[]{}\"'“”‘’👍🙂☺️"
CLAUSE_BOUNDARY = re.compile(r"[,.;!?\n]|\b(?:nhưng|tuy_nhiên|bù_lại|song|cơ_mà|trái_lại)\b", re.IGNORECASE)
BLOCKER_PATTERN = re.compile(r"\b(?:nhưng|mà|do|thì|nên|tôi|shop|và|trong_khi|trong|lúc|khi|cứ|rồi|nhé|để|cho|với|còn|nếu|so|giúp|tục)\b", re.IGNORECASE)

NEG_PATTERNS = [
    re.compile(r"\bbị\s+\S+(?:\s+\S+){0,4}", re.IGNORECASE),
    re.compile(r"\blỗi(?:\s+\S+){0,4}", re.IGNORECASE),
    re.compile(r"\b(?:lag|giật|đơ|reset|gãy|rách|tróc|tụt(?:\s+\d+%)?|nóng|chậm|trễ|khó|chật|bé|rộng|ố\s+vàng|óng\s+vàng|bật\s+chỉ|vết\s+dơ|dính\s+mực|cẩu_thả|nực_cười|bị\s+gạt|lâu)(?:\s+\S+){0,4}", re.IGNORECASE),
    re.compile(r"\b(?:không\s+ổn|không\s+được|không\s+vừa|không\s+đẹp|quá\s+tệ|quá\s+chán|rất\s+rất\s+lâu)(?:\s+\S+){0,3}", re.IGNORECASE),
]
POS_PATTERNS = [
    re.compile(r"\b(?:đẹp|ưng|ổn|mượt|nhanh|nhiệt\s+tình|hài\s+lòng|khá\s+mềm|đáng\s+tiền|được\s+bảo_vệ|cẩn\s+thận|đúng\s+hẹn|vừa\s+tay)(?:\s+\S+){0,3}", re.IGNORECASE),
]
NEU_PATTERNS = [
    re.compile(r"\b(?:bình\s+thường|không\s+vấn\s+đề\s+gì|không\s+sao|được|tạm\s+ổn|tiền\s+nào\s+của\s+đó)(?:\s+\S+){0,3}", re.IGNORECASE),
]

FAMILY_EXTRA_PATTERNS = {
    "fashion_color_size": [
        re.compile(r"\b(?:đẹp|xấu|chật|rộng|bé|to|vừa|mỏng|dày|dơ|bật\s+chỉ|như\s+hình|giống\s+nhau)(?:\s+\S+){0,3}", re.IGNORECASE),
    ],
    "service_shop_support": [
        re.compile(r"\b(?:nhiệt\s+tình|cẩu_thả|hỗ\s+trợ|tư\s+vấn|khiếu\s+nai|giải\s+quyết|bảo\s+vệ|bình\s+thường|lâu)(?:\s+\S+){0,3}", re.IGNORECASE),
    ],
    "ship_delivery_packaging": [
        re.compile(r"\b(?:nhanh|chậm|trễ|đúng\s+hẹn|cẩn\s+thận|giống\s+nhau|lằng\s+nhằng)(?:\s+\S+){0,3}", re.IGNORECASE),
    ],
    "price_value": [
        re.compile(r"\b(?:đắt|rẻ|mềm|cao|hợp\s+lý|đáng\s+tiền|phí\s+tiền|tiền\s+nào\s+của\s+đó)(?:\s+\S+){0,3}", re.IGNORECASE),
    ],
    "electronics_device": [
        re.compile(r"\b(?:lag|đơ|nóng|tụt(?:\s+\d+%)?|bình\s+thường|mượt|trâu|vàng|ố\s+vàng|reset)(?:\s+\S+){0,3}", re.IGNORECASE),
    ],
    "app_platform": [
        re.compile(r"\b(?:lag|đơ|lỗi|mượt|ổn|chậm|khó\s+dùng|cập\s+nhật)(?:\s+\S+){0,3}", re.IGNORECASE),
    ],
    "general_product": [
        re.compile(r"\b(?:tốt|kém|đẹp|xấu|ổn|bình\s+thường|như\s+hình|đúng\s+mẫu)(?:\s+\S+){0,3}", re.IGNORECASE),
    ],
}

PATTERN_EXTRA_PATTERNS = {
    "negation": [re.compile(r"\b(?:không|ko|k|đéo)\s+\S+(?:\s+\S+){0,4}", re.IGNORECASE)],
    "modifier": [re.compile(r"\b(?:hơi|quá|rất|khá|cũng|vẫn)\s+\S+(?:\s+\S+){0,4}", re.IGNORECASE)],
    "comparison": [re.compile(r"\b(?:như\s+hình|y\s+hình|đúng\s+mẫu|so\s+với\s+\S+(?:\s+\S+){0,3}|hơn\s+\S+|kém\s+\S+|giống\s+nhau)(?:\s+\S+){0,3}", re.IGNORECASE)],
    "error_defect": [re.compile(r"\b(?:bị\s+\S+(?:\s+\S+){0,4}|lỗi(?:\s+\S+){0,4}|gãy|rách|dơ|bật\s+chỉ|reset|lag|đơ|ố\s+vàng|óng\s+vàng|tụt(?:\s+\d+%)?)(?:\s+\S+){0,3}", re.IGNORECASE)],
    "plain": [],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fix one ASTE mini-batch manifest and apply it to an input JSONL file")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args()


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower().replace("_", " ")).strip(STRIP_CHARS)


def overlaps(span_a: tuple[int, int], span_b: tuple[int, int]) -> bool:
    return max(span_a[0], span_b[0]) < min(span_a[1], span_b[1])


def find_clause_bounds(text: str, start: int, end: int) -> tuple[int, int]:
    prev_boundary = -1
    next_boundary = len(text)
    for match in CLAUSE_BOUNDARY.finditer(text):
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


def make_key(line_no: int, triplet: dict[str, Any]) -> tuple[Any, ...]:
    return (line_no, triplet.get("aspect"), triplet.get("target"), tuple(triplet.get("target_span", [-1, -1])), triplet.get("sentiment"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def family_and_pattern_from_manifest(path: Path) -> tuple[str, str]:
    stem = path.name
    if ".part_" in stem:
        stem = stem.split(".part_", 1)[0]
    family, pattern = stem.split("__", 1)
    return family, pattern


def sentiment_patterns(sentiment: int) -> list[re.Pattern[str]]:
    if sentiment == 0:
        return NEG_PATTERNS
    if sentiment == 1:
        return POS_PATTERNS
    return NEU_PATTERNS


def collect_candidates(text: str, target_span: list[int], target: str, sentiment: int, family: str, pattern: str) -> list[dict[str, Any]]:
    start, end = target_span
    target_tuple = (start, end)
    clause_start, clause_end = find_clause_bounds(text, start, end)
    patterns = []
    patterns.extend(PATTERN_EXTRA_PATTERNS.get(pattern, []))
    patterns.extend(FAMILY_EXTRA_PATTERNS.get(family, []))
    patterns.extend(sentiment_patterns(sentiment))
    target_norm = normalize_text(target)

    candidates: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = set()
    for pattern_obj in patterns:
        for match in pattern_obj.finditer(text[clause_start:clause_end]):
            span = (clause_start + match.start(), clause_start + match.end())
            contains_target = span[0] <= start and span[1] >= end and span != target_tuple
            if overlaps(span, target_tuple) and not contains_target:
                continue
            cleaned = clean_candidate(text, span)
            if cleaned is None:
                continue
            opinion, cleaned_span = cleaned
            span_key = tuple(cleaned_span)
            if span_key in seen:
                continue
            seen.add(span_key)
            if not opinion:
                continue
            opinion_norm = normalize_text(opinion)
            if pattern == "modifier":
                tokens = opinion_norm.split()
                if len(tokens) < 2 or tokens[0] not in {"hơi", "quá", "rất", "khá", "cũng", "vẫn", "không"}:
                    continue
            distance = min(abs(cleaned_span[0] - end), abs(start - cleaned_span[1])) if cleaned_span[1] <= start or cleaned_span[0] >= end else 0
            contains_target_text = target_norm and target_norm in opinion_norm
            score = 1000 - distance - max(0, len(opinion_norm.split()) - 4) * 4
            if contains_target_text:
                score -= 25
            if pattern != "plain" and opinion_norm.startswith(("hơi", "quá", "rất", "khá", "không")):
                score += 10
            candidates.append({
                "opinion": opinion,
                "opinion_span": cleaned_span,
                "source": pattern_obj.pattern,
                "score": score,
            })

    candidates.sort(key=lambda item: (-item["score"], item["opinion_span"][0], item["opinion_span"][1]))
    return candidates


def clean_candidate(text: str, span: tuple[int, int]) -> tuple[str, list[int]] | None:
    raw = text[span[0]:span[1]].strip(STRIP_CHARS)
    if not raw:
        return None
    raw = re.split(r"[,.;!?]", raw, maxsplit=1)[0].strip(STRIP_CHARS)
    raw = BLOCKER_PATTERN.split(raw, maxsplit=1)[0].strip(STRIP_CHARS)
    if not raw:
        return None
    tokens = raw.split()
    if len(tokens) > 4:
        raw = " ".join(tokens[:4])
    if len(raw.split()) == 0:
        return None
    local = text.find(raw, max(0, span[0] - 5), min(len(text), span[1] + 5))
    if local < 0:
        local = text.find(raw)
    if local < 0:
        return None
    return raw, [local, local + len(raw)]


def classify_sentiment(opinion: str, current_sentiment: int) -> int:
    norm = normalize_text(opinion)
    if norm.startswith(("rất đáng", "khá xứng", "rất cạnh", "khá mềm", "rất chất", "khá chỉn", "rất dày")):
        return 1
    if re.search(r"\b(?:lag|đơ|lỗi|gãy|rách|dơ|tụt|không|tệ|xấu|kém|chậm|trễ|nóng|chật|bé|rộng|vàng|cẩu thả|nực cười|bị gạt|lâu)\b", norm):
        if norm.startswith("không tệ") or norm.startswith("không quá") or "không sao" in norm:
            return 2
        return 0
    if re.search(r"\b(?:đẹp|ưng|mượt|nhanh|nhiệt tình|hài lòng|mềm|đáng tiền|cẩn thận|đúng hẹn|vừa tay|trâu)\b", norm):
        return 1
    if re.search(r"\b(?:bình thường|không vấn đề gì|không sao|được|tạm ổn|tiền nào của đó)\b", norm):
        return 2
    return current_sentiment


def update_record_triplet(triplet: dict[str, Any], decision: dict[str, Any]) -> None:
    triplet["opinion"] = decision["selected_opinion"]
    triplet["opinion_span"] = decision["selected_opinion_span"]
    triplet["aspect_opinion_pair"] = f"{triplet['target']} {decision['selected_opinion']}".strip()
    triplet["sentiment"] = decision["selected_sentiment"]


def main() -> None:
    args = parse_args()
    family, pattern = family_and_pattern_from_manifest(args.manifest)
    manifest_rows = load_jsonl(args.manifest)
    records = load_jsonl(args.input)

    decisions: list[dict[str, Any]] = []
    accepted: dict[tuple[Any, ...], dict[str, Any]] = {}

    for row in manifest_rows:
        for error in row.get("errors", []):
            if error.get("type") != "Span lệch" or error.get("reason") != "Span nằm ngoài độ dài text và không có cách sửa chắc chắn.":
                continue
            triplet_idx = error["triplet_idx"]
            triplet = row["fixed_triplets"][triplet_idx]
            if triplet.get("opinion"):
                continue
            candidates = collect_candidates(row["text"], triplet["target_span"], triplet["target"], triplet["sentiment"], family, pattern)
            if not candidates:
                decisions.append({
                    "review_id": f"{row['line_no']}:{triplet_idx}",
                    "line_no": row["line_no"],
                    "triplet_idx": triplet_idx,
                    "family": family,
                    "pattern": pattern,
                    "target": triplet["target"],
                    "target_span": triplet["target_span"],
                    "current_sentiment": triplet["sentiment"],
                    "selected_opinion": "",
                    "selected_opinion_span": [-1, -1],
                    "selected_sentiment": triplet["sentiment"],
                    "decision": "skip",
                    "suggestions": [],
                })
                continue
            selected = candidates[0]
            selected_sentiment = classify_sentiment(selected["opinion"], triplet["sentiment"])
            decision = {
                "review_id": f"{row['line_no']}:{triplet_idx}",
                "line_no": row["line_no"],
                "triplet_idx": triplet_idx,
                "family": family,
                "pattern": pattern,
                "target": triplet["target"],
                "target_span": triplet["target_span"],
                "current_sentiment": triplet["sentiment"],
                "selected_opinion": selected["opinion"],
                "selected_opinion_span": selected["opinion_span"],
                "selected_sentiment": selected_sentiment,
                "selected_source": selected["source"],
                "decision": "accept",
                "suggestions": candidates[:5],
            }
            decisions.append(decision)
            accepted[make_key(row["line_no"], triplet)] = decision

    applied_updates = 0
    output_rows: list[dict[str, Any]] = []
    for line_no, record in enumerate(records, start=1):
        row = {"text": record["text"], "triplets": [dict(triplet) for triplet in record.get("triplets", [])]}
        for triplet in row["triplets"]:
            key = make_key(line_no, triplet)
            if key in accepted:
                update_record_triplet(triplet, accepted[key])
                applied_updates += 1
        output_rows.append(row)

    with open(args.output, "w", encoding="utf-8") as handle:
        for row in output_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    with open(args.decisions, "w", encoding="utf-8") as handle:
        for row in decisions:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    report = {
        "manifest": str(args.manifest),
        "family": family,
        "pattern": pattern,
        "input": str(args.input),
        "output": str(args.output),
        "decisions": str(args.decisions),
        "total_rows": len(manifest_rows),
        "accepted": sum(1 for row in decisions if row["decision"] == "accept"),
        "skipped": sum(1 for row in decisions if row["decision"] == "skip"),
        "applied_updates": applied_updates,
    }
    with open(args.report, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()