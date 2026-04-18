import argparse
import json
from pathlib import Path
from collections import Counter

import pandas as pd

ASPECTS = ["Fashion", "Electronics", "General", "Service", "Ship", "Price", "App"]
SENTIMENT_NAMES = {0: "Negative", 1: "Positive", 2: "Neutral"}


# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
def load_records(file_path: Path):
    records = []
    with file_path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


# ─────────────────────────────────────────────
# BUILD CORE METRICS (ONLY 3 THINGS)
# ─────────────────────────────────────────────
def build_eda(records):
    aspect_counter = Counter()
    sentiment_counter = Counter()
    text_lengths = []

    for record in records:
        # Global sentiment
        sentiment = record.get("global_sentiment", -1)
        sentiment_counter[sentiment] += 1

        # Text length
        text = record.get("text", "")
        text_lengths.append(len(text.split()))

        # Aspect count
        for op in record.get("opinions", []):
            aspect = op.get("aspect", "")
            aspect_counter[aspect] += 1

    # Convert to dataframe
    aspect_df = pd.DataFrame([
        {"aspect": a, "count": aspect_counter.get(a, 0)}
        for a in ASPECTS
    ])

    sentiment_df = pd.DataFrame([
        {
            "sentiment": SENTIMENT_NAMES.get(s, str(s)),
            "count": sentiment_counter.get(s, 0)
        }
        for s in [0, 1, 2]
    ])

    return {
        "aspect": aspect_df,
        "sentiment": sentiment_df,
        "text_length": text_lengths
    }


# ─────────────────────────────────────────────
# EXPORT JSON (FOR DASHBOARD)
# ─────────────────────────────────────────────
def export_json(eda_data, output_dir: Path):
    eda_json = {
        "aspect_distribution": eda_data["aspect"].to_dict(orient="records"),
        "sentiment_distribution": eda_data["sentiment"].to_dict(orient="records"),
        "text_length": eda_data["text_length"],
    }

    with open(output_dir / "eda.json", "w", encoding="utf-8") as f:
        json.dump(eda_json, f, indent=2, ensure_ascii=False)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/processed/data_train_v5.jsonl")
    parser.add_argument("--output", default="data/processed/eda_clean")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading data...")
    records = load_records(input_path)

    print("Building EDA...")
    eda_data = build_eda(records)

    print("Exporting JSON...")
    export_json(eda_data, output_dir)

    print(f"✅ Done. Saved to: {output_dir / 'eda.json'}")


if __name__ == "__main__":
    main()