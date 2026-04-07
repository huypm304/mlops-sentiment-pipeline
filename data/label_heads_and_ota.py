#!/usr/bin/env python3
"""Label JSONL dataset with 4 heads:
- aspect_detection: subset of [Product, Price, Ship, Service, App]
- aspect_sentiment: per detected aspect (0 neg, 1 pos, 2 neu)
- global_sentiment: kept as-is
- ota_tags: BIO tags for target noun/noun-phrases; length must match token count

This is a rule-based labeler intended for Vietnamese e-commerce review text.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Sequence


ASPECT_ORDER: list[str] = ["Product", "Price", "Ship", "Service", "App"]

# Keyword lexicon (lowercased). Keep it conservative: exact-token matches.
ASPECT_KEYWORDS: dict[str, set[str]] = {
    "Product": {
        "hàng",
        "hàng_hóa",
        "mặt_hàng",
        "sản_phẩm",
        "sp",
        "chất_lượng",
        "đóng_gói",
        "hộp",
        "bể",
        "hư",
        "hỏng",
        "lỗi",
        "móp",
        "fake",
        "giả",
        "hàng_giả",
        "hàng_nhái",
        "nhái",
        "dỏm",
        "kém_chất_lượng",
        "mỏng",
    },
    "Price": {
        "giá",
        "rẻ",
        "mắc",
        "đắt",
        "cao",
        "phí",
        "síp",
        "ship",
        "freeship",
        "voucher",
        "khuyến_mại",
        "giảm_giá",
        "mã",
        "xu",
        "lazrewards",
        "tikinow",
    },
    "Ship": {
        "giao",
        "giao_hàng",
        "vận_chuyển",
        "shipper",
        "ship",
        "síp",
        "đơn_hàng",
        "đơn",
        "ghn",
        "spx",
        "nhận",
        "trễ",
        "chậm",
        "delay",
        "hẹn",
        "hoàn_đơn",
        "hoàn",
        "trả",
        "kho",
        "bàn_giao",
    },
    "Service": {
        "cskh",
        "chăm_sóc",
        "khách_hàng",
        "tổng_đài",
        "hỗ_trợ",
        "khiếu_nại",
        "phản_hồi",
        "giải_quyết",
        "tư_vấn",
        "nhân_viên",
        "thái_độ",
        "đổi_trả",
        "hoàn_tiền",
        "trả_hàng",
        "bảo_hành",
        "bảo_vệ",
        "từ_chối",
    },
    "App": {
        "app",
        "ứng_dụng",
        "giao_diện",
        "lag",
        "đơ",
        "lỗi",
        "đăng_nhập",
        "đăng_kí",
        "đăng_ký",
        "tài_khoản",
        "tk",
        "khóa",
        "ram",
        "update",
        "cập_nhật",
        "game",
        "bot",
        "robot",
    },
}

PLATFORM_TOKENS: set[str] = {
    "tiki",
    "lazada",
    "shopee",
    "shoppe",
    "lzd",
    "lzđ",
    "tik",
    "laz",
    "sope",
    "shoppee",
    "ladaza",
    "lazada_cút",
}

POS_WORDS: set[str] = {
    "tốt",
    "ok",
    "oki",
    "ổn",
    "ổn_áp",
    "tuyệt_vời",
    "tuyet",
    "tuyet_voi",
    "hài_lòng",
    "ưng_ý",
    "uy_tín",
    "xứng_đáng",
    "nhanh",
    "tiện",
    "tiện_lợi",
    "hữu_ích",
    "đẹp",
    "chuyên_nghiệp",
    "yên_tâm",
    "mượt",
    "giá_rẻ",
}

NEG_WORDS: set[str] = {
    "tệ",
    "kém",
    "chán",
    "bực",
    "bực_mình",
    "ức_chế",
    "thất_vọng",
    "vô_trách_nhiệm",
    "lừa",
    "lừa_đảo",
    "dối_trá",
    "giả",
    "hàng_giả",
    "khóa",
    "lỗi",
    "lag",
    "đơ",
    "khó",
    "khó_khăn",
    "rắc_rối",
    "chậm",
    "trễ",
    "lâu",
    "từ_chối",
    "không",
    "hủy",
    "hoàn",
    "không_được",
    "phiền",
    "phiền_phức",
    "vô_dụng",
    "ngu",
    "bịp",
}

# Single-token targets that can be tagged as OTA.
TARGET_SINGLE: set[str] = {
    # Platforms / apps
    *PLATFORM_TOKENS,
    "app",
    "ứng_dụng",
    "giao_diện",
    "hệ_thống",
    "bot",
    "robot",
    # Logistics / shipment
    "shipper",
    "ship",
    "síp",
    "vận_chuyển",
    "đơn_vị",
    "đơn_vị_vận_chuyển",
    "đơn_hàng",
    "đơn",
    "kho",
    "tài_xế",
    # Commerce entities
    "shop",
    "cửa_hàng",
    "người_bán",
    "nhà_bán",
    "khách_hàng",
    "người_mua",
    # Product / order
    "sản_phẩm",
    "hàng",
    "hàng_hóa",
    "mặt_hàng",
    "quà",
    "đồ",
    # Service
    "tổng_đài",
    "cskh",
    "nhân_viên",
    "tư_vấn",
    "thái_độ",
    "dịch_vụ",
    "khiếu_nại",
    "hỗ_trợ",
    "đổi_trả",
    "hoàn_tiền",
    "trả_hàng",
    # Money / promotions
    "giá",
    "phí",
    "voucher",
    "mã",
    "mã_giảm_giá",
    "giảm_giá",
    "khuyến_mại",
    "xu",
    "freeship",
    "lazrewards",
    # Account
    "tài_khoản",
    "đăng_nhập",
    "đăng_kí",
    "đăng_ký",
    "sdt",
    "gmail",
}

# Multi-token target phrases (tokenized by whitespace). Longest-first matching.
TARGET_PATTERNS: list[tuple[str, ...]] = [
    ("đơn_vị", "vận_chuyển"),
    ("chăm_sóc", "khách_hàng"),
    ("nhân_viên", "tư_vấn"),
    ("mã", "giảm_giá"),
    ("mã", "giảm_giá", "freeship"),
    ("phí", "ship"),
    ("phí", "síp"),
    ("phí", "vận_chuyển"),
    ("mã", "freeship"),
]
TARGET_PATTERNS.sort(key=len, reverse=True)


def _norm(tok: str) -> str:
    return tok.strip().lower()


def tokenize(text: str) -> list[str]:
    # Whitespace tokenization (matches `text.split()` constraint).
    return text.split()


def detect_aspects(tokens: Sequence[str]) -> list[str]:
    tset = {_norm(t) for t in tokens}
    detected: set[str] = set()

    for aspect, kws in ASPECT_KEYWORDS.items():
        if tset & kws:
            detected.add(aspect)

    # If only platform is mentioned, treat as Service unless App explicitly present.
    if not detected:
        if tset & PLATFORM_TOKENS:
            detected.add("Service")

    # Canonical order
    return [a for a in ASPECT_ORDER if a in detected]


def sentiment_for_aspect(tokens: Sequence[str], aspect: str, global_sentiment: int) -> int:
    toks = [_norm(t) for t in tokens]
    kws = ASPECT_KEYWORDS.get(aspect, set())

    # Find keyword positions.
    positions = [i for i, t in enumerate(toks) if t in kws]
    if not positions:
        # For platform-only Service fallback
        if aspect == "Service" and (set(toks) & PLATFORM_TOKENS):
            positions = [i for i, t in enumerate(toks) if t in PLATFORM_TOKENS]

    pos = 0
    neg = 0
    if positions:
        for i in positions:
            lo = max(0, i - 4)
            hi = min(len(toks), i + 5)
            window = toks[lo:hi]
            pos += sum(1 for w in window if w in POS_WORDS)
            neg += sum(1 for w in window if w in NEG_WORDS)

    # Fallback: use full-text cues if aspect is present.
    if pos == 0 and neg == 0 and (positions or any(t in kws for t in toks)):
        pos = sum(1 for w in toks if w in POS_WORDS)
        neg = sum(1 for w in toks if w in NEG_WORDS)

    if pos > neg and pos > 0:
        return 1
    if neg > pos and neg > 0:
        return 0

    # Neutral/mixed fallback.
    if global_sentiment == 2:
        return 2
    return int(global_sentiment)


def label_ota(tokens: Sequence[str]) -> list[str]:
    toks = [_norm(t) for t in tokens]
    tags = ["O"] * len(tokens)

    # Phrase matching first (longest-first)
    i = 0
    while i < len(tokens):
        matched = False
        for pat in TARGET_PATTERNS:
            n = len(pat)
            if i + n <= len(tokens) and tuple(toks[i : i + n]) == pat:
                tags[i] = "B-OTA"
                for j in range(1, n):
                    tags[i + j] = "I-OTA"
                i += n
                matched = True
                break
        if not matched:
            i += 1

    # Single-token targets
    for i, t in enumerate(toks):
        if tags[i] != "O":
            continue
        if t in TARGET_SINGLE:
            tags[i] = "B-OTA"

    return tags


def iter_jsonl(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            obj = json.loads(line)
            if "text" not in obj or "heads" not in obj:
                raise ValueError(f"Missing keys at line {line_no}")
            if not isinstance(obj["heads"], dict):
                raise ValueError(f"heads must be dict at line {line_no}")
            yield obj


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inplace", action="store_true", help="Rewrite input file in place")
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path, nargs="?")
    args = ap.parse_args()

    inp: Path = args.input
    out: Path
    if args.inplace:
        out = inp
    else:
        if args.output is None:
            raise SystemExit("output is required unless --inplace")
        out = args.output

    new_lines: list[str] = []
    for obj in iter_jsonl(inp):
        text = obj["text"]
        heads = obj["heads"]

        tokens = tokenize(text)
        aspects = detect_aspects(tokens)
        aspect_sent: dict[str, int] = {}
        global_sent = heads.get("global_sentiment")
        if global_sent not in (0, 1, 2):
            raise ValueError(f"Invalid global_sentiment: {global_sent!r} for text={text!r}")

        for a in aspects:
            aspect_sent[a] = sentiment_for_aspect(tokens, a, int(global_sent))

        ota = label_ota(tokens)
        if len(ota) != len(tokens):
            raise AssertionError("ota_tags length mismatch")

        obj["heads"] = {
            "aspect_detection": aspects,
            "aspect_sentiment": aspect_sent,
            "global_sentiment": global_sent,
            "ota_tags": ota,
        }

        new_lines.append(json.dumps(obj, ensure_ascii=False) + "\n")

    tmp_path = out
    if args.inplace:
        tmp_path = out.with_suffix(out.suffix + ".tmp")

    tmp_path.write_text("".join(new_lines), encoding="utf-8")

    if args.inplace:
        tmp_path.replace(out)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
