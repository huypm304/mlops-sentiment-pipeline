#!/usr/bin/env python3
import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Set


VALID_ASPECTS = {
    "Fashion",
    "Electronics",
    "General",
    "Service",
    "Ship",
    "Price",
    "App",
}

ASPECT_KEYWORDS = {
    "Fashion": [
        "ao",
        "quan",
        "vay",
        "size",
        "form",
        "vai",
        "duong may",
        "mau",
        "chat vai",
        "hoa tiet",
    ],
    "Electronics": [
        "pin",
        "camera",
        "man hinh",
        "wifi",
        "loa",
        "chip",
        "ram",
        "sac",
        "nong",
        "nhiet do",
    ],
    "Service": [
        "shop",
        "nhan vien",
        "tu van",
        "cham soc",
        "phan hoi",
        "rep",
        "tra loi",
    ],
    "Ship": [
        "ship",
        "shipper",
        "giao hang",
        "van chuyen",
        "van don",
        "dong goi",
        "tre",
        "dung hen",
    ],
    "Price": [
        "gia",
        "re",
        "dat",
        "chi phi",
        "tam gia",
        "sale",
        "voucher",
        "tien",
    ],
    "App": [
        "app",
        "ung dung",
        "giao dien",
        "lag",
        "load",
        "gio hang",
        "thanh toan",
    ],
}

POS_WORDS = {
    "tot",
    "dep",
    "on",
    "muot",
    "nhanh",
    "hai long",
    "ung",
    "re",
    "hop ly",
    "de dung",
    "than thien",
    "nhiet tinh",
    "dung hen",
}

NEG_WORDS = {
    "te",
    "xau",
    "chan",
    "lag",
    "cham",
    "loi",
    "nong",
    "hut",
    "tut",
    "chua",
    "dat",
    "khong phan hoi",
    "tre",
    "mop",
    "vo",
}

NEU_WORDS = {
    "tam duoc",
    "binh thuong",
    "khong te",
    "khong tot",
    "vua",
    "dung duoc",
    "khong co gi dac biet",
}

CONTRAST_MARKERS = ["nhung", "tuy", "du", "song", "the nhung", "chi la"]


def pct(n: int, d: int) -> float:
    return 0.0 if d == 0 else round(n * 100.0 / d, 4)


def normalize_text(s: str) -> str:
    s = s.lower().strip()
    s = "".join(ch for ch in unicodedata.normalize("NFD", s) if unicodedata.category(ch) != "Mn")
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def keyword_aspects(text: str) -> Set[str]:
    out: Set[str] = set()
    for aspect, kws in ASPECT_KEYWORDS.items():
        for kw in kws:
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, text):
                out.add(aspect)
                break
    return out


def infer_local_sentiment(context: str) -> Dict[str, int]:
    pos = sum(1 for w in POS_WORDS if w in context)
    neg = sum(1 for w in NEG_WORDS if w in context)
    neu = sum(1 for w in NEU_WORDS if w in context)

    strong_neg_phrases = ["khong", "qua cham", "that vong", "te", "loi", "khong duoc"]
    strong_pos_phrases = ["rat tot", "qua on", "hai long", "ung", "tot"]

    if any(p in context for p in strong_neg_phrases):
        neg += 1
    if any(p in context for p in strong_pos_phrases):
        pos += 1

    margin = abs(pos - neg)
    confidence = 0
    if margin >= 2:
        confidence = 2
    elif margin == 1 and (pos >= 2 or neg >= 2):
        confidence = 1

    if neu > 0 and pos == 0 and neg == 0:
        return {"label": 2, "confidence": 1}
    if pos > neg:
        return {"label": 1, "confidence": confidence}
    if neg > pos:
        return {"label": 0, "confidence": confidence}
    return {"label": 2, "confidence": 0}


def snippet_around(text: str, target: str, start: Any, end: Any, radius: int = 45) -> str:
    if isinstance(start, int) and isinstance(end, int) and 0 <= start < end <= len(text):
        l = max(0, start - radius)
        r = min(len(text), end + radius)
        return text[l:r]

    low = text.lower()
    t = target.lower() if isinstance(target, str) else ""
    idx = low.find(t) if t else -1
    if idx == -1:
        return text[: min(len(text), radius * 2)]
    l = max(0, idx - radius)
    r = min(len(text), idx + len(t) + radius)
    return text[l:r]


def audit_file(path: Path) -> Dict[str, Any]:
    total_rows = 0
    total_ops = 0

    suspicious_aspect = 0
    suspicious_sentiment = 0
    general_overuse = 0
    price_general_confusion = 0
    service_ship_confusion = 0

    contrast_rows = 0
    contrast_rows_without_polarity_split = 0

    samples = {
        "aspect_suspicious": [],
        "sentiment_suspicious": [],
        "general_overuse": [],
        "price_general_confusion": [],
        "service_ship_confusion": [],
        "contrast_without_split": [],
    }

    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue

            total_rows += 1
            obj = json.loads(line)
            text = normalize_text(obj.get("text", ""))
            opinions = obj.get("opinions", [])

            row_sentiments = []
            has_contrast = any(marker in text for marker in CONTRAST_MARKERS)
            if has_contrast:
                contrast_rows += 1

            for op in opinions:
                total_ops += 1
                aspect = op.get("aspect")
                sentiment = op.get("sentiment")
                target = normalize_text(op.get("target", ""))
                start = op.get("start")
                end = op.get("end")

                row_sentiments.append(sentiment)

                cand_aspects = keyword_aspects(target)

                if cand_aspects and aspect not in cand_aspects and aspect in VALID_ASPECTS:
                    suspicious_aspect += 1
                    if len(samples["aspect_suspicious"]) < 25:
                        samples["aspect_suspicious"].append(
                            {
                                "line": line_no,
                                "target": target,
                                "aspect": aspect,
                                "expected_candidates": sorted(cand_aspects),
                            }
                        )

                # General overuse: clear non-General keyword but labeled General.
                if aspect == "General":
                    strong_aspects = keyword_aspects(target) - {"General"}
                    if strong_aspects:
                        general_overuse += 1
                        if len(samples["general_overuse"]) < 25:
                            samples["general_overuse"].append(
                                {
                                    "line": line_no,
                                    "target": target,
                                    "expected": sorted(strong_aspects),
                                }
                            )

                if aspect == "General" and any(k in target for k in ["gia", "tien", "re", "dat"]):
                    price_general_confusion += 1
                    if len(samples["price_general_confusion"]) < 25:
                        samples["price_general_confusion"].append(
                            {"line": line_no, "target": target, "aspect": aspect}
                        )

                if aspect == "Service" and any(k in target for k in ["ship", "giao", "shipper", "van chuyen"]):
                    service_ship_confusion += 1
                    if len(samples["service_ship_confusion"]) < 25:
                        samples["service_ship_confusion"].append(
                            {"line": line_no, "target": target, "aspect": aspect}
                        )

                if aspect == "Ship" and any(k in target for k in ["nhan vien", "tu van", "cham soc", "shop"]):
                    service_ship_confusion += 1
                    if len(samples["service_ship_confusion"]) < 25:
                        samples["service_ship_confusion"].append(
                            {"line": line_no, "target": target, "aspect": aspect}
                        )

                ctx = normalize_text(snippet_around(obj.get("text", ""), op.get("target", ""), start, end))
                inferred = infer_local_sentiment(ctx)
                if sentiment in {0, 1, 2} and inferred["confidence"] >= 2 and inferred["label"] != sentiment:
                    suspicious_sentiment += 1
                    if len(samples["sentiment_suspicious"]) < 25:
                        samples["sentiment_suspicious"].append(
                            {
                                "line": line_no,
                                "target": target,
                                "sentiment": sentiment,
                                "inferred": inferred["label"],
                                "confidence": inferred["confidence"],
                                "context": ctx,
                            }
                        )

            if has_contrast and row_sentiments:
                if len(row_sentiments) >= 2 and not (0 in row_sentiments and 1 in row_sentiments):
                    contrast_rows_without_polarity_split += 1
                    if len(samples["contrast_without_split"]) < 25:
                        samples["contrast_without_split"].append(
                            {
                                "line": line_no,
                                "sentiments": row_sentiments,
                                "text": obj.get("text", "")[:180],
                            }
                        )

    aspect_suspicious_rate = pct(suspicious_aspect, total_ops)
    sentiment_suspicious_rate = pct(suspicious_sentiment, total_ops)

    return {
        "file": str(path),
        "rows": total_rows,
        "opinions": total_ops,
        "metrics": {
            "aspect_suspicious_count": suspicious_aspect,
            "aspect_suspicious_rate_pct": aspect_suspicious_rate,
            "sentiment_suspicious_count": suspicious_sentiment,
            "sentiment_suspicious_rate_pct": sentiment_suspicious_rate,
            "general_overuse_count": general_overuse,
            "general_overuse_rate_pct": pct(general_overuse, total_ops),
            "price_general_confusion_count": price_general_confusion,
            "price_general_confusion_rate_pct": pct(price_general_confusion, total_ops),
            "service_ship_confusion_count": service_ship_confusion,
            "service_ship_confusion_rate_pct": pct(service_ship_confusion, total_ops),
            "contrast_rows_count": contrast_rows,
            "contrast_rows_without_polarity_split_count": contrast_rows_without_polarity_split,
            "contrast_rows_without_polarity_split_pct": pct(contrast_rows_without_polarity_split, contrast_rows),
        },
        "thresholds": {
            "aspect_suspicious_good_lt_pct": 3.0,
            "aspect_suspicious_review_3_to_7_pct": [3.0, 7.0],
            "sentiment_suspicious_good_lt_pct": 5.0,
            "sentiment_suspicious_review_5_to_10_pct": [5.0, 10.0],
            "aspect_quality_band": (
                "good"
                if aspect_suspicious_rate < 3.0
                else ("review" if aspect_suspicious_rate <= 7.0 else "high-risk")
            ),
            "sentiment_quality_band": (
                "good"
                if sentiment_suspicious_rate < 5.0
                else ("review" if sentiment_suspicious_rate <= 10.0 else "high-risk")
            ),
        },
        "samples": samples,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--dev", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    train_report = audit_file(args.train)
    dev_report = audit_file(args.dev)
    combined = {
        "rows": train_report["rows"] + dev_report["rows"],
        "opinions": train_report["opinions"] + dev_report["opinions"],
    }

    out = {"train": train_report, "dev": dev_report, "combined": combined}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(json.dumps({"saved": str(args.output), "combined": combined}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
