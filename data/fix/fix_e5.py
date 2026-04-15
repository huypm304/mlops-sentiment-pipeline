import json
from collections import Counter

targets = []
with open("data/processed/train_final_v3_HEALED.jsonl") as f:
    for line in f:
        rec = json.loads(line)
        for op in rec.get("opinions", []):
            targets.append(op.get("target", "").strip().lower())

counter = Counter(targets)
print(f"Unique targets: {len(counter)}")
print("\nTop 50:")
for t, c in counter.most_common(50):
    print(f"  {c:5}  {t}")