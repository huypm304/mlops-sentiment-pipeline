import json
from collections import Counter

# Phân tích target "áo"
target_name = "áo"
sentiments = []
examples = {0: [], 1: [], 2: []}  # Negative, Positive, Neutral

with open("data/processed/train_data.jsonl") as f:
    for line in f:
        try:
            rec = json.loads(line)
            for op in rec.get("opinions", []):
                if op.get("target", "").lower() == target_name.lower():
                    sent = op.get("sentiment")
                    sentiments.append(sent)
                    if len(examples[sent]) < 5:
                        examples[sent].append(rec["text"])
        except:
            pass

# Count
c = Counter(sentiments)
total = sum(c.values())

print("=" * 80)
print(f"Phân tích target: '{target_name}'")
print("=" * 80)
print(f"\nTổng cộng {total} lần xuất hiện")
print(f"\nPhân bố sentiment:")
print(f"  Negative (0): {c[0]:4d} ({c[0]/total*100:5.1f}%)")
print(f"  Positive (1): {c[1]:4d} ({c[1]/total*100:5.1f}%)")
print(f"  Neutral  (2): {c[2]:4d} ({c[2]/total*100:5.1f}%)")

print("\n" + "=" * 80)
print("Ví dụ câu (tối đa 5 câu/sentiment):")
print("=" * 80)

sentiment_labels = {0: "NEGATIVE", 1: "POSITIVE", 2: "NEUTRAL"}
for sent in [0, 1, 2]:
    print(f"\n{sentiment_labels[sent]} ({c[sent]} lần):")
    print("-" * 80)
    for i, text in enumerate(examples[sent], 1):
        print(f"{i}. {text[:100]}...")

print("\n" + "=" * 80)
