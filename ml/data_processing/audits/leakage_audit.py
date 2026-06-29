#!/usr/bin/env python3
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple


def pct(n: int, d: int) -> float:
    return 0.0 if d == 0 else round(n * 100.0 / d, 4)


def normalize_text(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^\w\s]", "", s)
    return s


def tokenize(s: str) -> List[str]:
    return [x for x in re.split(r"\s+", s) if x]


def token_jaccard(a: str, b: str) -> float:
    sa = set(tokenize(a))
    sb = set(tokenize(b))
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def canonical_label_signature(obj: Dict[str, Any]) -> str:
    opinions = obj.get("opinions", [])
    tuples = []
    for op in opinions:
        tuples.append(
            (
                str(op.get("target", "")).strip().lower(),
                op.get("aspect"),
                op.get("sentiment"),
            )
        )
    tuples = sorted(tuples)
    payload = {"opinions": tuples, "global": obj.get("global_sentiment")}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def load_records(path: Path) -> List[Dict[str, Any]]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            obj = json.loads(line)
            text = obj.get("text", "")
            rows.append(
                {
                    "line": line_no,
                    "text": text,
                    "text_norm": normalize_text(text),
                    "label_sig": canonical_label_signature(obj),
                    "obj": obj,
                }
            )
    return rows


def find_near_duplicates(
    train_rows: List[Dict[str, Any]],
    dev_rows: List[Dict[str, Any]],
    threshold: float,
    max_samples: int,
) -> Tuple[int, List[Dict[str, Any]]]:
    # Length + leading token blocking to keep comparison tractable.
    buckets: Dict[Tuple[str, int], List[Dict[str, Any]]] = defaultdict(list)
    for row in train_rows:
        toks = tokenize(row["text_norm"])
        first = toks[0] if toks else ""
        key = (first, len(toks) // 4)
        buckets[key].append(row)

    near_count = 0
    samples: List[Dict[str, Any]] = []

    for drow in dev_rows:
        toks = tokenize(drow["text_norm"])
        first = toks[0] if toks else ""
        key = (first, len(toks) // 4)
        cands = buckets.get(key, [])

        best_sim = 0.0
        best_match = None
        for trow in cands:
            sim = token_jaccard(drow["text_norm"], trow["text_norm"])
            if sim > best_sim:
                best_sim = sim
                best_match = trow

        if best_sim >= threshold and best_match is not None:
            near_count += 1
            if len(samples) < max_samples:
                samples.append(
                    {
                        "dev_line": drow["line"],
                        "train_line": best_match["line"],
                        "similarity": round(best_sim, 4),
                        "dev_text": drow["text"][:180],
                        "train_text": best_match["text"][:180],
                    }
                )

    return near_count, samples


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--dev", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--near-threshold", type=float, default=0.9)
    parser.add_argument("--max-samples", type=int, default=30)
    args = parser.parse_args()

    train_rows = load_records(args.train)
    dev_rows = load_records(args.dev)

    train_by_text = defaultdict(list)
    dev_by_text = defaultdict(list)
    train_by_norm = defaultdict(list)
    dev_by_norm = defaultdict(list)

    for row in train_rows:
        train_by_text[row["text"]].append(row)
        train_by_norm[row["text_norm"]].append(row)
    for row in dev_rows:
        dev_by_text[row["text"]].append(row)
        dev_by_norm[row["text_norm"]].append(row)

    exact_overlap_keys = set(train_by_text.keys()) & set(dev_by_text.keys())
    norm_overlap_keys = set(train_by_norm.keys()) & set(dev_by_norm.keys())

    exact_overlap_pairs = 0
    norm_overlap_pairs = 0
    same_text_diff_label = 0

    exact_samples = []
    diff_label_samples = []

    for key in exact_overlap_keys:
        t_list = train_by_text[key]
        d_list = dev_by_text[key]
        exact_overlap_pairs += len(t_list) * len(d_list)

        for t in t_list:
            for d in d_list:
                if t["label_sig"] != d["label_sig"]:
                    same_text_diff_label += 1
                    if len(diff_label_samples) < args.max_samples:
                        diff_label_samples.append(
                            {
                                "text": key[:180],
                                "train_line": t["line"],
                                "dev_line": d["line"],
                            }
                        )

        if len(exact_samples) < args.max_samples:
            exact_samples.append(
                {
                    "text": key[:180],
                    "train_lines": [x["line"] for x in t_list[:5]],
                    "dev_lines": [x["line"] for x in d_list[:5]],
                }
            )

    for key in norm_overlap_keys:
        norm_overlap_pairs += len(train_by_norm[key]) * len(dev_by_norm[key])

    near_count, near_samples = find_near_duplicates(
        train_rows,
        dev_rows,
        threshold=args.near_threshold,
        max_samples=args.max_samples,
    )

    report = {
        "train": {"rows": len(train_rows)},
        "dev": {"rows": len(dev_rows)},
        "metrics": {
            "exact_duplicate_train_dev_pairs": exact_overlap_pairs,
            "exact_duplicate_train_dev_ratio_over_dev_pct": pct(exact_overlap_pairs, len(dev_rows)),
            "normalized_duplicate_train_dev_pairs": norm_overlap_pairs,
            "normalized_duplicate_train_dev_ratio_over_dev_pct": pct(norm_overlap_pairs, len(dev_rows)),
            "near_duplicate_dev_rows_count": near_count,
            "near_duplicate_dev_rows_ratio_pct": pct(near_count, len(dev_rows)),
            "same_text_different_labels_pairs": same_text_diff_label,
            "same_text_different_labels_ratio_over_exact_pairs_pct": pct(
                same_text_diff_label, exact_overlap_pairs
            ),
        },
        "thresholds": {
            "exact_leakage_best_pct": 0.0,
            "exact_leakage_warning_over_pct": 1.0,
            "near_duplicate_target_lt_pct": 2.0,
            "pass_exact_leakage": pct(exact_overlap_pairs, len(dev_rows)) == 0.0,
            "warn_exact_leakage": pct(exact_overlap_pairs, len(dev_rows)) > 1.0,
            "pass_near_duplicate": pct(near_count, len(dev_rows)) < 2.0,
            "near_threshold": args.near_threshold,
        },
        "samples": {
            "exact_duplicates": exact_samples,
            "same_text_different_labels": diff_label_samples,
            "near_duplicates": near_samples,
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(
        json.dumps(
            {
                "saved": str(args.output),
                "exact_ratio_pct": report["metrics"]["exact_duplicate_train_dev_ratio_over_dev_pct"],
                "near_ratio_pct": report["metrics"]["near_duplicate_dev_rows_ratio_pct"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
