"""
auto_fix.py
────────────
Tự động fix các lỗi không cần LLM:
  E3 — Target là opinion word → xóa opinion đó
  E8 — Text quá ngắn (≤2 tokens) → drop record

Input : train_final.jsonl
Output: train_auto_fixed.jsonl  (sạch E3 + E8)
        train_e5_queue.jsonl    (576 records E5, đưa vào agent fix)

Chạy: python auto_fix.py
"""

import json
from pathlib import Path
from collections import Counter

# ── Config ────────────────────────────────────────────────────────────────────

INPUT_FILE   = "data/processed/train_final.jsonl"
OUTPUT_CLEAN = "data/processed/train_auto_fixed.jsonl"    # records sạch, không cần agent
OUTPUT_E5    = "data/processed/train_e5_queue.jsonl"      # records E5, đưa vào agent

MIN_TOKENS   = 3   # drop nếu số token < MIN_TOKENS (E8)

# E3: target chính xác khớp opinion word (không phải substring)
OPINION_WORDS = {
    # Negative
    "tệ", "xấu", "kém", "chậm", "đắt", "tồi", "dở", "lỗi",
    "mỏng", "rộng", "nhỏ", "to", "bẩn", "hôi", "nhạt", "cứng",
    "nặng", "sai", "thiếu", "trễ", "lâu", "hỏng", "rách", "tệ_hại",
    # Positive
    "đẹp", "tốt", "nhanh", "rẻ", "mượt", "mịn", "chắc", "chuẩn",
    "xinh", "ngon", "hay", "tuyệt", "ổn",
    # Neutral
    "bình_thường", "tạm", "được", "thôi", "bình thường",
}

# E5 keywords để detect (dùng để flag record vào queue, không fix ở đây)
NEG_KEYWORDS = [
    "không", "tệ", "xấu", "kém", "chậm", "đắt", "tồi", "dở", "lỗi",
    "mỏng", "thiếu", "sai", "trễ", "lâu", "hỏng", "rách", "bẩn", "hôi",
    "tệ_hại", "không giống", "không đúng", "không đẹp",
    "thất vọng", "bực", "tức", "chán", "ghét",
]
POS_KEYWORDS = [
    "đẹp", "tốt", "nhanh", "rẻ", "mượt", "tuyệt", "xinh", "ngon",
    "thích", "hài lòng", "xuất sắc", "hoàn hảo", "chuẩn", "ưng",
    "chất lượng", "ổn lắm", "rất tốt", "rất đẹp", "siêu",
]
NEU_KEYWORDS = [
    "bình thường", "tạm được", "cũng được", "tạm ổn",
    "bình thường thôi", "khắc phục được", "cũng ok", "ổn",
    "tạm", "được thôi", "cũng được", "không tệ", "không tồi",
]

WINDOW = 5   # số token mỗi bên để lấy context


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_context(text, char_s, char_e, window=WINDOW):
    tokens  = text.split()
    n       = len(tokens)
    # Tìm token index gần nhất với char offset
    pos = 0
    tok_idx = 0
    for i, tok in enumerate(tokens):
        if pos >= char_s:
            tok_idx = i
            break
        pos += len(tok) + 1
    lo = max(0, tok_idx - window)
    hi = min(n, tok_idx + window + 1)
    return " ".join(tokens[lo:hi]).lower()


def has_neg_context(context):
    return any(kw in context for kw in NEG_KEYWORDS)


def has_pos_context(context):
    return any(kw in context for kw in POS_KEYWORDS)


def has_neu_context(context):
    return any(kw in context for kw in NEU_KEYWORDS)


def is_e5_suspicious(op, text):
    """
    Flag opinion là E5 nếu:
    - sentiment=POS nhưng context có NEG keyword rõ ràng
    - sentiment=NEG nhưng context có POS keyword rõ ràng
    - sentiment=POS nhưng context có NEU keyword (không có POS keyword)
    """
    sent    = op.get("sentiment", -1)
    char_s  = op.get("start", 0)
    char_e  = op.get("end", 0)
    context = get_context(text, char_s, char_e)

    if sent == 1:   # predict POS
        if has_neg_context(context):
            return True
        if has_neu_context(context) and not has_pos_context(context):
            return True
    elif sent == 0:  # predict NEG
        if has_pos_context(context) and not has_neg_context(context):
            return True

    return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    records = []
    with open(INPUT_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    print(f"📥 Loaded {len(records):,} records")

    stats = dict(
        total=len(records),
        dropped_e8=0,
        fixed_e3_opinions=0,
        dropped_empty_after_e3=0,
        e5_flagged=0,
        clean=0,
    )

    clean_records = []
    e5_records    = []

    for rec in records:
        text     = rec.get("text", "")
        opinions = rec.get("opinions", [])

        # ── E8: Drop text quá ngắn ──────────────────────────────
        if len(text.split()) < MIN_TOKENS:
            stats["dropped_e8"] += 1
            continue

        # ── E3: Xóa opinion có target là opinion word ───────────
        filtered_opinions = []
        for op in opinions:
            target = op.get("target", "").strip().lower()
            if target in OPINION_WORDS:
                stats["fixed_e3_opinions"] += 1
            else:
                filtered_opinions.append(op)

        # Drop record nếu sau E3 fix không còn opinion
        if not filtered_opinions:
            stats["dropped_empty_after_e3"] += 1
            continue

        rec = dict(rec)
        rec["opinions"] = filtered_opinions

        # ── E5: Flag record nếu có opinion nghi ngờ sai sentiment
        has_e5 = any(is_e5_suspicious(op, text) for op in filtered_opinions)

        if has_e5:
            stats["e5_flagged"] += 1
            e5_records.append(rec)
        else:
            stats["clean"] += 1
            clean_records.append(rec)

    # Save
    with open(OUTPUT_CLEAN, "w", encoding="utf-8") as f:
        for r in clean_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(OUTPUT_E5, "w", encoding="utf-8") as f:
        for r in e5_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Report
    print(f"\n{'='*54}")
    print(f"  AUTO FIX REPORT")
    print(f"{'='*54}")
    print(f"  Total input          : {stats['total']:,}")
    print(f"  {'─'*48}")
    print(f"  Dropped E8 (ngắn)    : {stats['dropped_e8']:,}")
    print(f"  Fixed E3 opinions    : {stats['fixed_e3_opinions']:,}")
    print(f"  Dropped (rỗng sau E3): {stats['dropped_empty_after_e3']:,}")
    print(f"  {'─'*48}")
    print(f"  → Clean (không E5)   : {stats['clean']:,}  →  {OUTPUT_CLEAN}")
    print(f"  → E5 queue (agent)   : {stats['e5_flagged']:,}  →  {OUTPUT_E5}")
    print(f"{'='*54}\n")


if __name__ == "__main__":
    main()