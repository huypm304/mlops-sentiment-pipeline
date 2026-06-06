#!/usr/bin/env python3
import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional


SEVERE_NEG_PATTERNS = [
    "hang gia",
    "man hinh vo",
    "mat tien",
    "lua dao",
    "hong nang",
    "vo ngay",
    "khong dung duoc",
]


def pct(n: int, d: int) -> float:
    return 0.0 if d == 0 else round(n * 100.0 / d, 4)


def normalize(s: str) -> str:
    return " ".join(str(s).lower().split())


def detect_severe_neg(text: str) -> bool:
    t = normalize(text)
    return any(p in t for p in SEVERE_NEG_PATTERNS)


def classify_case(pos: int, neg: int, neu: int) -> str:
    if pos > 0 and neg == 0 and neu == 0:
        return "all_pos"
    if neg > 0 and pos == 0 and neu == 0:
        return "all_neg"
    if neu > 0 and pos == 0 and neg == 0:
        return "all_neu"
    if pos > 0 and neg > 0:
        return "pos_neg"
    if pos > 0 and neu > 0 and neg == 0:
        return "pos_neu"
    if neg > 0 and neu > 0 and pos == 0:
        return "neg_neu"
    return "other"


def expected_global(pos: int, neg: int, neu: int, severe_neg: bool) -> Optional[int]:
    # Severity override.
    if severe_neg and (neg > 0 or pos > 0):
        return 0

    # Rule 4 hard logic.
    if neg >= 2 and pos == 0:
        return 0
    if neg >= 2 and pos == 1:
        return 0
    if pos >= 2 and neg == 0:
        return 1
    if pos >= 2 and neg == 1:
        return 1
    if pos == neg and pos > 0:
        return 2
    if neu > 0 and pos == 0 and neg == 0:
        return 2
    return None


def audit_file(path: Path) -> Dict[str, Any]:
    rows = 0
    decided_rows = 0
    consistent_rows = 0

    case_counter = Counter()
    case_consistent = Counter()
    rule_violations = Counter()

    mismatch_samples: List[Dict[str, Any]] = []

    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            rows += 1
            obj = json.loads(line)
            opinions = obj.get("opinions", [])
            text = obj.get("text", "")
            g = obj.get("global_sentiment")

            sent = [op.get("sentiment") for op in opinions if op.get("sentiment") in {0, 1, 2}]
            pos = sum(1 for x in sent if x == 1)
            neg = sum(1 for x in sent if x == 0)
            neu = sum(1 for x in sent if x == 2)

            ctype = classify_case(pos, neg, neu)
            case_counter[ctype] += 1

            severe = detect_severe_neg(text)
            exp = expected_global(pos, neg, neu, severe)
            if exp is None:
                continue

            decided_rows += 1
            if g == exp:
                consistent_rows += 1
                case_consistent[ctype] += 1
            else:
                rule_key = f"expected_{exp}_got_{g}"
                rule_violations[rule_key] += 1
                if len(mismatch_samples) < 40:
                    mismatch_samples.append(
                        {
                            "line": line_no,
                            "case_type": ctype,
                            "pos": pos,
                            "neg": neg,
                            "neu": neu,
                            "severe_neg": severe,
                            "expected_global": exp,
                            "actual_global": g,
                            "text": text[:200],
                        }
                    )

    case_table = {}
    for ctype, cnt in case_counter.items():
        case_table[ctype] = {
            "count": cnt,
            "ratio_pct": pct(cnt, rows),
            "consistent_count": case_consistent.get(ctype, 0),
            "consistent_pct_within_case": pct(case_consistent.get(ctype, 0), cnt),
        }

    consistency_pct = pct(consistent_rows, decided_rows)

    return {
        "file": str(path),
        "rows": rows,
        "decidable_rows": decided_rows,
        "global_rule_consistency_pct": consistency_pct,
        "thresholds": {
            "good_ge_pct": 95.0,
            "acceptable_90_95_pct": [90.0, 95.0],
            "quality_band": (
                "good" if consistency_pct >= 95.0 else ("acceptable" if consistency_pct >= 90.0 else "high-risk")
            ),
        },
        "case_type_table": case_table,
        "rule_violations": dict(rule_violations),
        "samples": {"mismatch": mismatch_samples},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--dev", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    train_report = audit_file(args.train)
    dev_report = audit_file(args.dev)
    combined_decidable = train_report["decidable_rows"] + dev_report["decidable_rows"]

    out = {
        "train": train_report,
        "dev": dev_report,
        "combined": {
            "rows": train_report["rows"] + dev_report["rows"],
            "decidable_rows": combined_decidable,
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(
        json.dumps(
            {
                "saved": str(args.output),
                "train_consistency_pct": train_report["global_rule_consistency_pct"],
                "dev_consistency_pct": dev_report["global_rule_consistency_pct"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
