import json
from collections import Counter, defaultdict

file_path = "data/processed/balanced_train_v3.jsonl"

aspect_counter = Counter()
sentiment_counter = Counter()
aspect_sentiment_counter = defaultdict(Counter)
co_occurrence = Counter()

multi_aspect_opposite = 0
multi_aspect_total = 0

with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        rec = json.loads(line)
        opinions = rec.get("opinions", [])
        aspects = [op["aspect"] for op in opinions]
        sentiments = [op["sentiment"] for op in opinions]
        for op in opinions:
            aspect = op.get("aspect", "Unknown")
            sentiment = op.get("sentiment", "Unknown")
            aspect_counter[aspect] += 1
            sentiment_counter[sentiment] += 1
            aspect_sentiment_counter[aspect][sentiment] += 1
        # Check for opposite sentiment in multi-aspect
        if len(opinions) > 1:
            multi_aspect_total += 1
            # Nếu có ít nhất 2 aspect sentiment khác nhau
            if len(set(sentiments)) > 1:
                multi_aspect_opposite += 1
            # Đếm co-occurrence
            for i in range(len(aspects)):
                for j in range(i+1, len(aspects)):
                    pair = tuple(sorted([aspects[i], aspects[j]]))
                    co_occurrence[pair] += 1

print("=== Aspect statistics ===")
for aspect, count in aspect_counter.most_common():
    print(f"{aspect}: {count}")

print("\n=== Aspect-Sentiment matrix ===")
for aspect, sents in aspect_sentiment_counter.items():
    print(f"{aspect}: ", dict(sents))

print("\n=== Tổng số câu có nhiều aspect: ", multi_aspect_total)
print("Số câu có aspect đối lập sentiment: ", multi_aspect_opposite, f"({multi_aspect_opposite/multi_aspect_total*100:.1f}%)")

print("\n=== Top aspect co-occurrence pairs ===")
for pair, cnt in co_occurrence.most_common(10):
    print(f"{pair}: {cnt}")
