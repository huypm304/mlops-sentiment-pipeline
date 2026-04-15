"""
merge_final.py
───────────────
Gộp 2 file sau khi fix xong:
  train_auto_fixed.jsonl  (clean, không cần agent)
  train_e5_fixed.jsonl    (đã được agent fix E5)

→ train_final_v2.jsonl   (file train cuối cùng)

Chạy: python merge_final.py
"""

import json
import random
from pathlib import Path

INPUT_CLEAN = "data/processed/train_auto_fixed.jsonl"
INPUT_E5    = "data/processed/train_e5_fixed.jsonl"
OUTPUT      = "data/processed/train_final_v2.jsonl"
SEED        = 42


def load_jsonl(path):
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def main():
    clean = load_jsonl(INPUT_CLEAN)
    e5    = load_jsonl(INPUT_E5)

    print(f"Clean records : {len(clean):,}")
    print(f"E5 fixed      : {len(e5):,}")

    merged = clean + e5
    random.seed(SEED)
    random.shuffle(merged)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        for r in merged:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Phân phối global sentiment sau merge
    from collections import Counter
    gs = Counter(r.get("global_sentiment") for r in merged)
    labels = {0: "NEG", 1: "POS", 2: "NEU"}

    print(f"\n{'='*40}")
    print(f"  FINAL: {len(merged):,} records → {OUTPUT}")
    print(f"{'='*40}")
    for sid in [0, 1, 2]:
        cnt = gs[sid]
        print(f"  {labels[sid]} ({sid}): {cnt:,} ({cnt/len(merged)*100:.1f}%)")
    print(f"{'='*40}")


if __name__ == "__main__":
    main()