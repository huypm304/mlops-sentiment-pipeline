#!/usr/bin/env python3
"""Generate dataset analysis reports from train/dev/test JSONL files.

Usage:
    python scripts/make_data_reports.py \\
        --train-file /path/to/train.jsonl \\
        --dev-file   /path/to/dev_clean.jsonl \\
        --output-dir artifacts/data
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

ASPECTS = ["Fashion", "Electronics", "General", "Service", "Ship", "Price", "App"]
SENT_ID2LABEL = {0: "NEG", 1: "POS", 2: "NEU"}


def _load_jsonl(path: Path) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"  WARNING: JSON parse error at line {i+1}: {e}")
    return records


def _md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _analyze_split(records: list[dict], split_name: str) -> dict:
    n_rows = len(records)
    all_opinions = [op for r in records for op in r.get("opinions", [])]
    n_opinions = len(all_opinions)

    aspect_counts: Counter = Counter()
    sent_counts: Counter = Counter()
    global_counts: Counter = Counter()
    ops_per_row = []
    empty_targets = 0
    oob_offsets = 0
    multi_aspect_rows = 0
    mixed_sent_rows = 0

    for record in records:
        text = record.get("text", "")
        opinions = record.get("opinions", [])
        ops_per_row.append(len(opinions))

        aspects_in_row = set()
        sents_in_row = set()

        for op in opinions:
            asp = op.get("aspect", "")
            sent = op.get("sentiment", -1)
            start = op.get("start", -1)
            end = op.get("end", -1)
            target = op.get("target", "")

            if asp in ASPECTS:
                aspect_counts[asp] += 1
            if isinstance(sent, int) and sent in SENT_ID2LABEL:
                sent_counts[SENT_ID2LABEL[sent]] += 1
                sents_in_row.add(sent)
            if not target.strip():
                empty_targets += 1
            if start < 0 or end < 0 or end > len(text):
                oob_offsets += 1

            aspects_in_row.add(asp)

        if len(aspects_in_row) >= 2:
            multi_aspect_rows += 1
        if len(sents_in_row) >= 2:
            mixed_sent_rows += 1

        g_sent = record.get("global_sentiment")
        if isinstance(g_sent, int) and g_sent in SENT_ID2LABEL:
            global_counts[SENT_ID2LABEL[g_sent]] += 1
        elif isinstance(g_sent, str) and g_sent in {"NEG", "POS", "NEU"}:
            global_counts[g_sent] += 1

    return {
        "split": split_name,
        "n_rows": n_rows,
        "n_opinions": n_opinions,
        "mean_opinions_per_row": round(n_opinions / max(n_rows, 1), 3),
        "max_opinions_per_row": max(ops_per_row, default=0),
        "multi_aspect_rows": multi_aspect_rows,
        "multi_aspect_rate": round(multi_aspect_rows / max(n_rows, 1), 4),
        "mixed_sentiment_rows": mixed_sent_rows,
        "mixed_sentiment_rate": round(mixed_sent_rows / max(n_rows, 1), 4),
        "empty_target_count": empty_targets,
        "out_of_bound_offset_count": oob_offsets,
        "aspect_distribution": dict(aspect_counts),
        "sentiment_distribution": dict(sent_counts),
        "global_distribution": dict(global_counts),
    }


def _leakage_report(splits: dict[str, list[dict]]) -> dict:
    exact: dict[str, set] = {name: set(r.get("text", "") for r in recs) for name, recs in splits.items()}
    report = {}
    names = list(exact.keys())
    for i, a in enumerate(names):
        for b in names[i+1:]:
            overlap = exact[a] & exact[b]
            report[f"{a}_vs_{b}"] = {
                "exact_duplicates": len(overlap),
                "samples": sorted(overlap)[:5],
            }
    return report


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate dataset analysis reports")
    p.add_argument("--train-file", type=Path, default=None)
    p.add_argument("--dev-file",   type=Path, default=None)
    p.add_argument("--test-file",  type=Path, default=None)
    p.add_argument("--output-dir", type=Path, default=Path("artifacts/data"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    file_map: dict[str, Path] = {}
    for name, path in [("train", args.train_file), ("dev", args.dev_file), ("test", args.test_file)]:
        if path is not None and path.is_file():
            file_map[name] = path
        elif path is not None:
            print(f"WARNING: {name} file not found: {path}")

    if not file_map:
        print("ERROR: no valid files provided. Use --train-file / --dev-file / --test-file")
        sys.exit(1)

    splits: dict[str, list[dict]] = {}
    manifest_files = []
    for name, path in file_map.items():
        records = _load_jsonl(path)
        splits[name] = records
        manifest_files.append({
            "split": name,
            "path": str(path.resolve()),
            "md5": _md5(path),
            "n_rows": len(records),
        })
        print(f"Loaded {len(records)} rows from {path}")

    # dataset_manifest.json
    manifest = {
        "files": manifest_files,
        "aspects": ASPECTS,
        "sentiment_labels": SENT_ID2LABEL,
    }
    with open(args.output_dir / "dataset_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print("  Saved: dataset_manifest.json")

    # Per-split summaries
    summaries = [_analyze_split(recs, name) for name, recs in splits.items()]
    with open(args.output_dir / "data_summary.json", "w", encoding="utf-8") as f:
        json.dump(summaries, f, ensure_ascii=False, indent=2)
    print("  Saved: data_summary.json")

    # split_distribution.csv
    with open(args.output_dir / "split_distribution.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["split", "n_rows", "n_opinions", "mean_ops_per_row",
                    "multi_aspect_rate", "mixed_sentiment_rate",
                    "empty_target_count", "oob_offset_count"])
        for s in summaries:
            w.writerow([
                s["split"], s["n_rows"], s["n_opinions"],
                s["mean_opinions_per_row"], s["multi_aspect_rate"],
                s["mixed_sentiment_rate"], s["empty_target_count"],
                s["out_of_bound_offset_count"],
            ])
    print("  Saved: split_distribution.csv")

    # aspect_distribution.csv
    with open(args.output_dir / "aspect_distribution.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["split"] + ASPECTS + ["total"])
        for s in summaries:
            asp_dist = s["aspect_distribution"]
            row = [s["split"]] + [asp_dist.get(a, 0) for a in ASPECTS] + [sum(asp_dist.values())]
            w.writerow(row)
    print("  Saved: aspect_distribution.csv")

    # sentiment_distribution.csv
    with open(args.output_dir / "sentiment_distribution.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["split", "NEG", "POS", "NEU", "total"])
        for s in summaries:
            sd = s["sentiment_distribution"]
            total = sum(sd.values())
            w.writerow([s["split"], sd.get("NEG", 0), sd.get("POS", 0), sd.get("NEU", 0), total])
    print("  Saved: sentiment_distribution.csv")

    # global_distribution.csv
    with open(args.output_dir / "global_distribution.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["split", "NEG", "POS", "NEU", "total", "missing"])
        for s in summaries:
            gd = s["global_distribution"]
            total = sum(gd.values())
            w.writerow([s["split"], gd.get("NEG", 0), gd.get("POS", 0), gd.get("NEU", 0),
                        total, s["n_rows"] - total])
    print("  Saved: global_distribution.csv")

    # data_quality_check.json
    quality = {}
    for s in summaries:
        n = max(s["n_rows"], 1)
        quality[s["split"]] = {
            "offset_validation_rate": round(1.0 - s["out_of_bound_offset_count"] / max(s["n_opinions"], 1), 4),
            "empty_target_rate": round(s["empty_target_count"] / max(s["n_opinions"], 1), 4),
            "multi_aspect_rate": s["multi_aspect_rate"],
            "mixed_sentiment_rate": s["mixed_sentiment_rate"],
        }
    with open(args.output_dir / "data_quality_check.json", "w", encoding="utf-8") as f:
        json.dump(quality, f, ensure_ascii=False, indent=2)
    print("  Saved: data_quality_check.json")

    # leakage_report.json
    if len(splits) >= 2:
        leakage = _leakage_report(splits)
        with open(args.output_dir / "leakage_report.json", "w", encoding="utf-8") as f:
            json.dump(leakage, f, ensure_ascii=False, indent=2)
        print("  Saved: leakage_report.json")

    print(f"\nAll data reports saved to: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
