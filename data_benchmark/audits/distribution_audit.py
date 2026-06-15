#!/usr/bin/env python3
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict


ASPECTS = ["Fashion", "Electronics", "General", "Service", "Ship", "Price", "App"]
SENTS = [0, 1, 2]


def pct(n: int, d: int) -> float:
    return 0.0 if d == 0 else round(n * 100.0 / d, 4)


def audit_file(path: Path) -> Dict[str, Any]:
    rows = 0
    opinions = 0

    aspect_counts = Counter({a: 0 for a in ASPECTS})
    aspect_sent = {a: Counter({0: 0, 1: 0, 2: 0}) for a in ASPECTS}

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rows += 1
            obj = json.loads(line)
            for op in obj.get("opinions", []):
                a = op.get("aspect")
                s = op.get("sentiment")
                if a in ASPECTS and s in SENTS:
                    opinions += 1
                    aspect_counts[a] += 1
                    aspect_sent[a][s] += 1

    aspect_distribution = []
    for a in ASPECTS:
        aspect_distribution.append(
            {
                "aspect": a,
                "opinions": aspect_counts[a],
                "ratio_pct": pct(aspect_counts[a], opinions),
                "low_resource_train_lt_300": aspect_counts[a] < 300,
            }
        )

    aspect_sent_matrix = []
    for a in ASPECTS:
        total = aspect_counts[a]
        row = {
            "aspect": a,
            "NEG": aspect_sent[a][0],
            "POS": aspect_sent[a][1],
            "NEU": aspect_sent[a][2],
            "Total": total,
            "NEU_pct": pct(aspect_sent[a][2], total),
            "cell_flags": {
                "min_cell_lt_30": min(aspect_sent[a][0], aspect_sent[a][1], aspect_sent[a][2]) < 30,
                "min_cell_lt_50": min(aspect_sent[a][0], aspect_sent[a][1], aspect_sent[a][2]) < 50,
                "min_cell_lt_100": min(aspect_sent[a][0], aspect_sent[a][1], aspect_sent[a][2]) < 100,
            },
        }
        aspect_sent_matrix.append(row)

    return {
        "file": str(path),
        "rows": rows,
        "opinions": opinions,
        "aspect_distribution": aspect_distribution,
        "aspect_sentiment_matrix": aspect_sent_matrix,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--dev", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    train_report = audit_file(args.train)
    dev_report = audit_file(args.dev)

    # Build compact comparison tables for train/dev.
    comp_aspect = []
    train_map = {x["aspect"]: x for x in train_report["aspect_distribution"]}
    dev_map = {x["aspect"]: x for x in dev_report["aspect_distribution"]}
    for a in ASPECTS:
        comp_aspect.append(
            {
                "aspect": a,
                "train_opinions": train_map[a]["opinions"],
                "dev_opinions": dev_map[a]["opinions"],
                "train_ratio_pct": train_map[a]["ratio_pct"],
                "dev_ratio_pct": dev_map[a]["ratio_pct"],
            }
        )

    out = {
        "train": train_report,
        "dev": dev_report,
        "comparison": {
            "aspect_distribution_table": comp_aspect,
            "thresholds": {
                "train_per_aspect_ge_300": True,
                "dev_per_aspect_ge_50": True,
                "cell_train_ge_30": True,
                "cell_train_ge_50": True,
                "cell_train_ge_100": True,
            },
        },
    }

    # Evaluate thresholds using train matrix.
    for row in train_report["aspect_distribution"]:
        if row["opinions"] < 300:
            out["comparison"]["thresholds"]["train_per_aspect_ge_300"] = False
            break

    for row in dev_report["aspect_distribution"]:
        if row["opinions"] < 50:
            out["comparison"]["thresholds"]["dev_per_aspect_ge_50"] = False
            break

    for row in train_report["aspect_sentiment_matrix"]:
        if row["cell_flags"]["min_cell_lt_30"]:
            out["comparison"]["thresholds"]["cell_train_ge_30"] = False
        if row["cell_flags"]["min_cell_lt_50"]:
            out["comparison"]["thresholds"]["cell_train_ge_50"] = False
        if row["cell_flags"]["min_cell_lt_100"]:
            out["comparison"]["thresholds"]["cell_train_ge_100"] = False

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(
        json.dumps(
            {
                "saved": str(args.output),
                "train_rows": train_report["rows"],
                "dev_rows": dev_report["rows"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
