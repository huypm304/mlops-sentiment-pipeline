#!/usr/bin/env python3

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path


INPUT_FILE = Path("data/processed/train_final_v3.autofix_review.jsonl")
OUTPUT_JSON = Path("data/processed/train_final_v3.autofix_review_groups.json")
OUTPUT_MD = Path("data/processed/train_final_v3.autofix_review_groups.md")
MAX_EXAMPLES_PER_GROUP = 5


PATTERN_RULES = {
    "Product": [
        ("size_form_fit", [r"size", r"form", r"kích_cỡ", r"kích cỡ", r"rộng", r"chật", r"nhỏ", r"to"]),
        ("material_quality", [r"vải", r"chất_liệu", r"chất liệu", r"chất_lượng", r"chất lượng", r"mỏng", r"cứng", r"mịn", r"xấu"]),
        ("battery", [r"pin", r"tụt", r"trâu", r"sạc"]),
        ("display", [r"màn_hình", r"màn hình", r"độ sáng"]),
        ("camera", [r"camera", r"camara", r"chụp ảnh", r"quay"]),
        ("color_style", [r"màu", r"mẫu", r"kiểu", r"đẹp", r"xinh"]),
        ("build_finish", [r"đường may", r"khuy", r"lem", r"rách", r"lòi"]),
        ("generic_product_target", [r"áo", r"hàng", r"sản_phẩm", r"sản phẩm", r"mẫu", r"linh_kiện_điện_tử"]),
    ],
    "Service": [
        ("response_support", [r"trả_lời", r"trả lời", r"phản_hồi", r"phản hồi", r"hỗ_trợ", r"hỗ trợ"]),
        ("staff_attitude", [r"nhân_viên", r"nhân viên", r"tư_vấn", r"tư vấn", r"phục_vụ", r"phục vụ", r"nhiệt_tình", r"nhiệt tình"]),
        ("shop_reliability", [r"shop", r"có tâm", r"cẩu_thả", r"làm_ăn", r"dịch_vụ", r"dịch vụ"]),
    ],
    "Ship": [
        ("delivery_speed", [r"giao", r"ship", r"vận_chuyển", r"vận chuyển", r"chậm", r"lâu", r"trễ"]),
        ("delivery_correctness", [r"giao", r"không đúng", r"sai", r"thiếu", r"nhầm", r"đúng yêu_cầu", r"đúng yêu cầu"]),
        ("delivery_status", [r"đơn hàng", r"hoàn", r"hủy", r"ngâm", r"không gọi", r"không nhận"]),
    ],
    "App": [
        ("app_stability", [r"app", r"ứng_dụng", r"ứng dụng", r"phần_mềm", r"phần mềm", r"lỗi", r"lag", r"giật", r"đơ", r"văng"]),
        ("app_update_os", [r"cập_nhật", r"cập nhật", r"hệ điều hành", r"miui", r"android", r"ios"]),
        ("app_ux", [r"tiện_lợi", r"tiện lợi", r"hữu_ích", r"hữu ích", r"đăng_nhập", r"đăng nhập"]),
    ],
    "Price": [
        ("price_level", [r"giá", r"tầm giá", r"cao", r"đắt", r"rẻ", r"mắc"]),
        ("voucher_promo", [r"voucher", r"khuyến_mãi", r"khuyến mãi", r"sale", r"mã_ship", r"mã ship"]),
        ("money_value", [r"tiền", r"đáng tiền", r"đồng_tiền", r"phù_hợp", r"hợp_lý", r"hợp lý"]),
    ],
}


def contains_any(patterns: list[str], text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def normalize_text(value: str | None) -> str:
    return (value or "").strip().lower()


def classify_pattern(entry: dict) -> str:
    reasons = entry.get("review_reasons", [])
    if "empty_after_cleaning" in reasons:
        return "empty_after_cleaning"

    opinion = entry.get("opinion") or {}
    aspect = opinion.get("aspect", "Unknown")
    target = normalize_text(opinion.get("target"))
    context = normalize_text(entry.get("context"))
    text = normalize_text(entry.get("text"))
    haystack = " ".join(part for part in [target, context, text] if part)

    for pattern_name, patterns in PATTERN_RULES.get(aspect, []):
        if contains_any(patterns, haystack):
            return pattern_name

    if target:
        safe_target = re.sub(r"\s+", "_", target)
        return f"target_{safe_target[:40]}"
    return "uncategorized"


def to_example(entry: dict) -> dict:
    opinion = entry.get("opinion") or {}
    row = entry.get("row") or {}
    return {
        "line_no": entry.get("line_no"),
        "reason": ", ".join(entry.get("review_reasons", [])),
        "aspect": opinion.get("aspect") or "<none>",
        "target": opinion.get("target") or "",
        "sentiment": opinion.get("sentiment"),
        "context": entry.get("context") or "",
        "text": entry.get("text") or row.get("text", ""),
    }


def md_cell(value: str) -> str:
    return value.replace("|", "\\|")


def main() -> int:
    group_counts = Counter()
    aspect_counts = Counter()
    reason_counts = Counter()
    unique_lines = set()
    conflict_lines = set()
    empty_lines = set()
    grouped_examples: dict[str, list[dict]] = defaultdict(list)

    with INPUT_FILE.open(encoding="utf-8") as handle:
        for raw_line in handle:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            entry = json.loads(raw_line)
            reasons = entry.get("review_reasons", [])
            opinion = entry.get("opinion") or {}
            aspect = opinion.get("aspect") or "<none>"
            reason = reasons[0] if reasons else "<none>"
            pattern = classify_pattern(entry)
            group_key = f"{aspect} | {reason} | {pattern}"
            line_no = entry.get("line_no")

            aspect_counts[aspect] += 1
            reason_counts[reason] += 1
            group_counts[group_key] += 1
            if line_no is not None:
                unique_lines.add(line_no)
                if reason == "empty_after_cleaning":
                    empty_lines.add(line_no)
                else:
                    conflict_lines.add(line_no)

            if len(grouped_examples[group_key]) < MAX_EXAMPLES_PER_GROUP:
                grouped_examples[group_key].append(to_example(entry))

    payload = {
        "input": str(INPUT_FILE),
        "total_cases": sum(group_counts.values()),
        "unique_lines": len(unique_lines),
        "conflict_lines": len(conflict_lines),
        "empty_after_cleaning_lines": len(empty_lines),
        "aspect_counts": dict(sorted(aspect_counts.items())),
        "reason_counts": dict(sorted(reason_counts.items())),
        "groups": [
            {
                "group": key,
                "count": count,
                "examples": grouped_examples[key],
            }
            for key, count in group_counts.most_common()
        ],
    }

    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Autofix Review Group Report",
        f"**Input**: {INPUT_FILE}",
        f"**Total cases**: {payload['total_cases']}",
        f"**Unique lines**: {payload['unique_lines']}",
        f"**Conflict lines**: {payload['conflict_lines']}",
        f"**Empty-after-cleaning lines**: {payload['empty_after_cleaning_lines']}",
        "",
        "## Counts By Aspect",
        "",
        "| Aspect | Count |",
        "|---|---:|",
    ]
    for aspect, count in aspect_counts.most_common():
        lines.append(f"| {md_cell(aspect)} | {count} |")

    lines.extend([
        "",
        "## Counts By Reason",
        "",
        "| Reason | Count |",
        "|---|---:|",
    ])
    for reason, count in reason_counts.most_common():
        lines.append(f"| {md_cell(reason)} | {count} |")

    lines.extend([
        "",
        "## Top Groups",
        "",
        "| Group | Count |",
        "|---|---:|",
    ])
    for key, count in group_counts.most_common(30):
        lines.append(f"| {md_cell(key)} | {count} |")

    lines.append("")
    lines.append("## Group Details")
    lines.append("")
    for key, count in group_counts.most_common():
        lines.append(f"### {key} ({count})")
        for example in grouped_examples[key]:
            lines.append(
                f"- line {example['line_no']} | target=\"{example['target']}\" | sentiment={example['sentiment']} | context=\"{example['context'][:120]}\""
            )
        lines.append("")

    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({
        "total_cases": payload["total_cases"],
        "unique_lines": payload["unique_lines"],
        "conflict_lines": payload["conflict_lines"],
        "empty_after_cleaning_lines": payload["empty_after_cleaning_lines"],
        "top_groups": payload["groups"][:10],
        "output_json": str(OUTPUT_JSON),
        "output_md": str(OUTPUT_MD),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())