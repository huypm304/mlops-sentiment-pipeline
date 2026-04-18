import json
from collections import Counter, defaultdict
import pandas as pd
from tqdm import tqdm

# Load data
with open('data/processed/train_data.jsonl', 'r', encoding='utf-8') as f:
    lines = [json.loads(line) for line in f]

# Aspect and sentiment statistics
aspect_counter = Counter()
sentiment_counter = Counter()
aspect_sentiment_counter = defaultdict(Counter)

for item in lines:
    for op in item.get('opinions', []):
        aspect = op.get('aspect', 'Unknown')
        sentiment = op.get('sentiment', 'Unknown')
        aspect_counter[aspect] += 1
        sentiment_counter[sentiment] += 1
        aspect_sentiment_counter[aspect][sentiment] += 1

# Print aspect statistics
print('--- Aspect Statistics ---')
for aspect, count in aspect_counter.most_common():
    print(f'{aspect}: {count}')

# Print sentiment statistics
print('\n--- Sentiment Statistics ---')
for sentiment, count in sentiment_counter.most_common():
    label = {0: 'Negative', 1: 'Positive', 2: 'Neutral'}.get(sentiment, sentiment)
    print(f'{label} ({sentiment}): {count}')

# Print aspect-sentiment matrix
print('\n--- Aspect-Sentiment Matrix ---')
aspect_list = list(aspect_counter.keys())
sentiment_labels = [0, 1, 2]
data = []
for aspect in aspect_list:
    row = [aspect_sentiment_counter[aspect][s] for s in sentiment_labels]
    data.append(row)
df = pd.DataFrame(data, columns=['Negative', 'Positive', 'Neutral'], index=aspect_list)
print(df)

# Check for possible annotation issues
print('\n--- Possible Annotation Issues ---')
short_texts = [item for item in lines if len(item['text']) < 10]
if short_texts:
    print(f'Found {len(short_texts)} samples with very short text (<10 chars). Example:')
    print(short_texts[0])
else:
    print('No very short texts found.')

# Check for unknown or inconsistent aspects
unknown_aspects = [op for item in lines for op in item.get('opinions', []) if op.get('aspect') not in aspect_counter]
if unknown_aspects:
    print(f'Found {len(unknown_aspects)} opinions with unknown aspects.')
else:
    print('No unknown aspects found.')

# Check for missing sentiment
missing_sentiment = [op for item in lines for op in item.get('opinions', []) if 'sentiment' not in op]
if missing_sentiment:
    print(f'Found {len(missing_sentiment)} opinions missing sentiment.')
else:
    print('No opinions missing sentiment.')
