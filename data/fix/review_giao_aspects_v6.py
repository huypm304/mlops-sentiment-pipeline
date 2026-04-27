#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from pathlib import Path


DEFAULT_QUEUE = Path("data/processed/data_train_v6_final.train_feedback_review.jsonl")
DEFAULT_BASE = Path("data/processed/data_train_v6_final.train_feedback_fixed.jsonl")
DEFAULT_DECISIONS = Path("data/processed/data_train_v6_final.giao_review_decisions.jsonl")
DEFAULT_OUTPUT = Path("data/processed/data_train_v6_final.giao_review_fixed.jsonl")
DEFAULT_REPORT = Path("data/processed/data_train_v6_final.giao_review_report.json")

LOGISTICS_PATTERNS = [
    r"(?:shipper|bưu_tá|bưu tá|anh_giao_hàng|anh giao hàng|đơn_vị_vận_chuyển|đơn vị vận chuyển|ghn|giao_hàng_tiết_kiệm|bưu_cục_phát|khâu_phát_hàng)",
    r"(?:nhanh|chậm|lâu|trễ|đúng_hẹn|đúng hẹn|tiến_độ|tiến độ).{0,10}(?:giao|ship|gửi)",
    r"(?:giao|ship|gửi).{0,12}(?:nhanh|chậm|lâu|trễ|đúng_hẹn|đúng hẹn|tới|đến)",
    r"(?:vận_đơn|vận đơn|vận_chuyển|vận chuyển|chặng_giao|lịch_giao|freeship|phí_ship|phí ship|đóng_gói để gửi|đóng gói để gửi)",
    r"(?:không_giao|không giao|chưa_giao|chưa giao|ngừng_giao|không_thèm_giao|không thèm giao)",
]

GENERAL_PATTERNS = [
    r"(?:đúng_mẫu|đúng mẫu|đúng_hàng|đúng hàng|đúng_màu|đúng màu|đúng_size|đúng size)",
    r"(?:mẫu|shop đăng|shop dang|mô_tả|mô tả).{0,20}(?:giao|gửi)|(?:giao|gửi).{0,24}(?:mẫu|shop đăng|shop dang|mô_tả|mô tả)",
    r"(?:nhầm_size|nhầm size|sai_size|sai size|nhầm_màu|nhầm màu|sai_màu|sai màu)",
    r"(?:đủ_số_lượng|đủ số lượng|thiếu_hàng|thiếu hàng|thiếu nhiều thứ|giao thiếu|đầy_đủ|đầy đủ|day du|đay đủ)",
    r"(?:hàng|áo|giày|ổ_cứng|sản_phẩm|sản phẩm).{0,12}(?:giao).{0,12}(?:đẹp|đúng|nhầm|sai|thiếu|móp_méo|móp méo|lỗi)",
    r"(?:giao).{0,14}(?:cho khách|cho người mua|đúng như shop đăng|đúng như mô_tả|đúng như mô tả)",
]

APP_PATTERNS = [
    r"giao_diện",
    r"giao diện",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review ambiguous giao/ship/general cases for v6 data")
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            raw_line = raw_line.strip()
            if raw_line:
                rows.append(json.loads(raw_line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def local_window(text: str, start: int, end: int, radius: int = 6) -> str:
    spans = [match.span() for match in re.finditer(r"\S+", text)]
    token_ids = []
    for idx, (tok_start, tok_end) in enumerate(spans):
        if max(tok_start, start) < min(tok_end, end):
            token_ids.append(idx)
    if not token_ids:
        return text.lower()
    low = max(0, token_ids[0] - radius)
    high = min(len(spans) - 1, token_ids[-1] + radius)
    return " ".join(text[s:e].lower() for s, e in spans[low : high + 1])


def has_any(patterns: list[str], text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def decide_label(text: str, opinion: dict) -> tuple[str, str]:
    target = opinion.get("target", "")
    window = local_window(text, opinion.get("start", 0), opinion.get("end", 0), radius=7)
    lowered_text = text.lower()

    if has_any(APP_PATTERNS, target.lower()) or has_any(APP_PATTERNS, window) or has_any(APP_PATTERNS, lowered_text):
        return "App", "Co cum 'giao diện' nen day la ngon ngu UI cua app."

    if has_any(GENERAL_PATTERNS, window):
        return "General", "Ngu canh noi ve viec shop giao dung/sai mau, size, so luong hoac chat luong don hang."

    if has_any(LOGISTICS_PATTERNS, window):
        return "Ship", "Ngu canh noi ve toc do giao, shipper hoac qua trinh van chuyen."

    normalized_target = target.lower().strip()
    if re.search(r"(?:mẫu|shop đăng|shop dang|mô_tả|mô tả|màu|size|kích_cỡ|kích cỡ|đầy_đủ|đầy đủ|day du|đay đủ)", window, flags=re.IGNORECASE):
        return "General", "Ngu canh gan voi mau ma, kich co hoac mo ta san pham nen day la loi thuc hien don hang."

    if normalized_target in {"giao", "gửi", "giao_hàng", "giao hàng"}:
        # Default unresolved generic delivery verbs to Ship because they refer to the delivery act itself.
        return "Ship", "Target la dong tu giao/gui va khong co dau hieu loi thuc hien mau ma cua shop."

    if "gói" in window or "đóng_gói" in window or "đóng gói" in window:
        return "Ship", "Ngu canh gan voi dong goi/gui di nen nghieng ve van chuyen."

    return "General", "Khong thay tin hieu van chuyen ro rang; uu tien xem day la loi thuc hien don hang."


def main() -> int:
    args = parse_args()
    queue_rows = read_jsonl(args.queue)
    base_rows = read_jsonl(args.base)

    decisions: list[dict] = []
    line_to_updates: dict[int, list[dict]] = {}
    stats = {"Ship": 0, "General": 0, "App": 0, "records": 0}

    for queue_row in queue_rows:
        line_no = queue_row["line_no"]
        text = queue_row["record"]["text"]
        updates = []
        for reason in queue_row["reasons"]:
            opinion_idx = reason["opinion_idx"]
            opinion = queue_row["record"]["opinions"][opinion_idx]
            new_aspect, rationale = decide_label(text, opinion)
            updates.append(
                {
                    "opinion_idx": opinion_idx,
                    "target": opinion.get("target", ""),
                    "old_aspect": opinion.get("aspect"),
                    "new_aspect": new_aspect,
                    "rationale": rationale,
                }
            )
            stats[new_aspect] += 1

        decisions.append(
            {
                "line_no": line_no,
                "text": text,
                "updates": updates,
            }
        )
        line_to_updates[line_no] = updates
        stats["records"] += 1

    merged_rows = []
    for idx, record in enumerate(base_rows, start=1):
        updated = deepcopy(record)
        for update in line_to_updates.get(idx, []):
            updated["opinions"][update["opinion_idx"]]["aspect"] = update["new_aspect"]
        merged_rows.append(updated)

    write_jsonl(args.decisions, decisions)
    write_jsonl(args.output, merged_rows)

    report = {
        "queue_file": str(args.queue),
        "base_file": str(args.base),
        "decisions_file": str(args.decisions),
        "output_file": str(args.output),
        "records_reviewed": stats["records"],
        "label_counts": {key: stats[key] for key in ["Ship", "General", "App"]},
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())