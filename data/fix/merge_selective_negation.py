#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_BASE = Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/aste_force_auto_batches/batch05_mini_batches/applied_modifier_v2/step_7_ship_delivery_packaging__modifier.part_01.jsonl")
DEFAULT_NEGATION_DIR = Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/aste_force_auto_batches/batch05_mini_batches/applied_negation_v1")
DEFAULT_OUTPUT = Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/aste_force_auto_batches/selective_merged_error_defect_modifier_negation.jsonl")
DEFAULT_REPORT = Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/aste_force_auto_batches/selective_merged_error_defect_modifier_negation.report.json")
DEFAULT_DECISIONS = Path("/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/aste_force_auto_batches/selective_merged_error_defect_modifier_negation.decisions.jsonl")

SAFE_EXACT = {
    "phí tiền",
    "tiền nào của đó",
    "không gửi kịp",
    "không xài được",
    "không hỗ_trợ người mua",
    "không hỗ trợ người mua",
    "tụt pin",
    "đơ",
    "không báo",
    "không gọi điện_thoại báo",
    "không gọi điện thoại báo",
    "không giải_đáp thắc_mắc",
    "không giải đáp thắc mắc",
    "ko đáng giá",
    "ko đáng dùng",
    "không xứng đáng",
    "Không xứng đáng",
}

SAFE_PREFIXES = (
    "không gửi",
    "không xài",
    "không hỗ_trợ",
    "không hỗ trợ",
    "không báo",
    "không gọi",
    "không giải_đáp",
    "không giải đáp",
    "không sử_dụng",
    "không sử dụng",
    "ko đáng",
    "tụt pin",
)

ELECTRONICS_TARGETS = {"máy", "pin", "màn hình", "màn_hình", "loa", "chip", "sạc", "củ_sạc", "camera", "ứng dụng", "ứng_dụng", "app", "voucher"}
SHIP_SERVICE_TARGETS = {"giao hàng", "giao_hàng", "vận_chuyển", "vận chuyển", "ship", "khuyến_mãi", "khuyến mãi", "khách_hàng", "khách hàng", "size"}

BLOCKLIST_EXACT = {
    "không",
    "k",
    "ko",
    "tư vấn",
    "tư vấn ạ",
    "tư vấn nói",
    "vàng nhòe",
    "dày",
    "rộng",
    "bé",
    "mỏng",
    "giống nhau",
    "ko nổi bật",
    "không thấy",
    "không lại",
    "k nhạy",
    "k rõ lắm",
    "không dây không anh",
}

BLOCK_SUBSTRINGS = (
    "không biết",
    "không hiểu",
    "không lẽ",
    "không cần",
    "không bao",
    "không thik",
    "không thích",
    "không dây",
    "tư vấn",
    "cập nhật",
    "hơn",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge safer negation decisions onto the error_defect + modifier base output")
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--negation-dir", type=Path, default=DEFAULT_NEGATION_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    return parser.parse_args()


def normalize_text(value: str) -> str:
    value = value.replace("_", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value


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


def is_safe_negation(row: dict[str, Any]) -> bool:
    if row.get("decision") != "accept":
        return False
    opinion = normalize_text(row.get("selected_opinion", ""))
    if not opinion:
        return False
    if opinion in BLOCKLIST_EXACT:
        return False
    if any(part in opinion for part in BLOCK_SUBSTRINGS):
        return False
    if opinion in SAFE_EXACT:
        if opinion == "đơ":
            return normalize_text(row.get("target", "")) in ELECTRONICS_TARGETS
        return True
    if opinion.startswith(SAFE_PREFIXES):
        target = normalize_text(row.get("target", ""))
        if opinion.startswith("tụt pin"):
            return target == "pin"
        if opinion.startswith("không báo") or opinion.startswith("không gọi"):
            return target in SHIP_SERVICE_TARGETS
        if opinion.startswith("không xài") or opinion.startswith("không sử_dụng") or opinion.startswith("không sử dụng"):
            return target in ELECTRONICS_TARGETS
        return True
    if opinion == "đơ" and row.get("selected_sentiment") == 0:
        return normalize_text(row.get("target", "")) in ELECTRONICS_TARGETS
    if opinion == "tụt pin":
        return normalize_text(row.get("target", "")) == "pin"
    return False


def recalibrate_sentiment(opinion: str, current_sentiment: int) -> int:
    normalized = normalize_text(opinion).lower()
    if normalized in {"phí tiền", "không gửi kịp", "không xài được", "không xài", "không hỗ trợ người mua", "không hỗ_trợ người mua", "tụt pin", "đơ", "không báo", "không báo trc", "không gọi điện thoại báo", "không gọi điện_thoại báo", "không giải đáp thắc mắc", "không giải_đáp thắc_mắc", "ko đáng giá", "ko đáng dùng", "không xứng đáng", "không báo tự ý giao", "không báo tự_ý giao"}:
        return 0
    if normalized == "tiền nào của đó":
        return 2
    return current_sentiment


def main() -> None:
    args = parse_args()
    negation_decisions: list[dict[str, Any]] = []
    for path in sorted(args.negation_dir.glob("*.decisions.jsonl")):
        negation_decisions.extend(load_jsonl(path))

    safe_rows = []
    for row in negation_decisions:
        if not is_safe_negation(row):
            continue
        updated = dict(row)
        updated["selected_sentiment"] = recalibrate_sentiment(row["selected_opinion"], row["selected_sentiment"])
        safe_rows.append(updated)
    accepted = {
        (row["line_no"], row["target"], tuple(row["target_span"]), row["triplet_idx"]): row
        for row in safe_rows
    }

    base_rows = load_jsonl(args.base)
    applied_updates = 0
    for line_no, record in enumerate(base_rows, start=1):
        for triplet_idx, triplet in enumerate(record.get("triplets", [])):
            key = (line_no, triplet.get("target"), tuple(triplet.get("target_span", [-1, -1])), triplet_idx)
            if key not in accepted:
                continue
            decision = accepted[key]
            triplet["opinion"] = decision["selected_opinion"]
            triplet["opinion_span"] = decision["selected_opinion_span"]
            triplet["sentiment"] = recalibrate_sentiment(decision["selected_opinion"], decision["selected_sentiment"])
            triplet["aspect_opinion_pair"] = f"{triplet['target']} {decision['selected_opinion']}".strip()
            applied_updates += 1

    with open(args.output, "w", encoding="utf-8") as handle:
        for row in base_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    with open(args.decisions, "w", encoding="utf-8") as handle:
        for row in safe_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    report = {
        "base": str(args.base),
        "negation_dir": str(args.negation_dir),
        "output": str(args.output),
        "decisions": str(args.decisions),
        "safe_negation_decisions": len(safe_rows),
        "applied_updates": applied_updates,
    }
    with open(args.report, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()