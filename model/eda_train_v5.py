import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

try:
    import matplotlib.pyplot as plt
except ImportError as exc:
    raise SystemExit(
        "matplotlib is required to generate charts. Install it with `pip install matplotlib`."
    ) from exc


ASPECTS = ["Fashion", "Electronics", "General", "Service", "Ship", "Price", "App"]
SENTIMENT_NAMES = {0: "Neg", 1: "Pos", 2: "Neu"}


def load_records(file_path: Path):
    records = []
    with file_path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def build_frames(records):
    aspect_counter = Counter()
    global_counter = Counter()
    opinions_per_record = Counter()
    text_lengths = []
    target_counter = Counter()
    aspect_sentiment = defaultdict(lambda: Counter())

    total_opinions = 0
    contrast_records = 0

    for record in records:
        opinions = record.get("opinions", [])
        sentiments = []

        opinions_per_record[len(opinions)] += 1
        global_counter[record.get("global_sentiment", -1)] += 1
        text_lengths.append(len(record.get("text", "").split()))

        for opinion in opinions:
            aspect = opinion.get("aspect", "")
            sentiment = opinion.get("sentiment", -1)
            target = opinion.get("target", "")

            total_opinions += 1
            sentiments.append(sentiment)
            aspect_counter[aspect] += 1
            aspect_sentiment[aspect][sentiment] += 1
            target_counter[target] += 1

        if len(set(sentiments)) > 1:
            contrast_records += 1

    overview_df = pd.DataFrame(
        [
            {
                "total_records": len(records),
                "total_opinions": total_opinions,
                "avg_opinions_per_record": round(total_opinions / max(len(records), 1), 4),
                "contrast_records": contrast_records,
                "contrast_ratio": round(contrast_records / max(len(records), 1), 4),
                "avg_text_len": round(sum(text_lengths) / max(len(text_lengths), 1), 4),
                "max_text_len": max(text_lengths) if text_lengths else 0,
            }
        ]
    )

    aspect_df = pd.DataFrame(
        [{"aspect": aspect, "count": aspect_counter.get(aspect, 0)} for aspect in ASPECTS]
    )

    global_df = pd.DataFrame(
        [
            {
                "global_sentiment": SENTIMENT_NAMES.get(sentiment, str(sentiment)),
                "count": global_counter.get(sentiment, 0),
            }
            for sentiment in [0, 1, 2]
        ]
    )

    aspect_sentiment_df = pd.DataFrame(
        [
            {
                "aspect": aspect,
                "Neg": aspect_sentiment[aspect].get(0, 0),
                "Pos": aspect_sentiment[aspect].get(1, 0),
                "Neu": aspect_sentiment[aspect].get(2, 0),
                "total": sum(aspect_sentiment[aspect].values()),
            }
            for aspect in ASPECTS
        ]
    )

    opinions_df = pd.DataFrame(
        [
            {"opinions_per_record": count, "records": opinions_per_record[count]}
            for count in sorted(opinions_per_record)
        ]
    )

    text_len_df = pd.DataFrame({"text_len_tokens": text_lengths})

    top_targets_df = pd.DataFrame(
        [{"target": target, "count": count} for target, count in target_counter.most_common(30)]
    )

    return {
        "overview": overview_df,
        "aspect": aspect_df,
        "global": global_df,
        "aspect_sentiment": aspect_sentiment_df,
        "opinions": opinions_df,
        "text_len": text_len_df,
        "top_targets": top_targets_df,
    }


def save_csvs(frames, output_dir: Path):
    for name, frame in frames.items():
        frame.to_csv(output_dir / f"{name}.csv", index=False)


def plot_bar(frame, x_col, y_col, title, output_path, color="#2E5BFF", rotation=0):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(frame[x_col], frame[y_col], color=color)
    ax.set_title(title)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    plt.xticks(rotation=rotation)
    plt.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def plot_stacked_aspect_sentiment(frame, output_path):
    fig, ax = plt.subplots(figsize=(11, 6))
    bottom = [0] * len(frame)
    colors = {"Neg": "#D9534F", "Pos": "#2E8B57", "Neu": "#F0AD4E"}
    for column in ["Neg", "Pos", "Neu"]:
        ax.bar(frame["aspect"], frame[column], bottom=bottom, label=column, color=colors[column])
        bottom = [a + b for a, b in zip(bottom, frame[column].tolist())]
    ax.set_title("Aspect x Sentiment Distribution")
    ax.set_xlabel("aspect")
    ax.set_ylabel("opinions")
    ax.legend()
    plt.xticks(rotation=20)
    plt.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def plot_histogram(frame, column, bins, title, output_path, color="#5BC0DE"):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(frame[column], bins=bins, color=color, edgecolor="black")
    ax.set_title(title)
    ax.set_xlabel(column)
    ax.set_ylabel("count")
    plt.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def save_charts(frames, output_dir: Path):
    plot_bar(
        frames["aspect"],
        x_col="aspect",
        y_col="count",
        title="Aspect Distribution",
        output_path=output_dir / "aspect_distribution.png",
        color="#4C78A8",
        rotation=20,
    )

    plot_bar(
        frames["global"],
        x_col="global_sentiment",
        y_col="count",
        title="Global Sentiment Distribution",
        output_path=output_dir / "global_sentiment_distribution.png",
        color="#72B7B2",
    )

    plot_stacked_aspect_sentiment(
        frames["aspect_sentiment"],
        output_path=output_dir / "aspect_sentiment_distribution.png",
    )

    plot_bar(
        frames["opinions"],
        x_col="opinions_per_record",
        y_col="records",
        title="Opinions Per Record",
        output_path=output_dir / "opinions_per_record.png",
        color="#F58518",
    )

    plot_histogram(
        frames["text_len"],
        column="text_len_tokens",
        bins=30,
        title="Text Length Distribution",
        output_path=output_dir / "text_length_distribution.png",
    )

    top_targets = frames["top_targets"].head(15).copy()
    plot_bar(
        top_targets,
        x_col="target",
        y_col="count",
        title="Top 15 Targets",
        output_path=output_dir / "top_targets.png",
        color="#E45756",
        rotation=35,
    )


def main():
    parser = argparse.ArgumentParser(description="Generate dataset statistics and charts before training.")
    parser.add_argument(
        "--input",
        default="data/processed/data_train_v5.jsonl",
        help="Path to training jsonl file.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/processed/eda_train_v5",
        help="Directory to save CSV summaries and PNG charts.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    records = load_records(input_path)
    frames = build_frames(records)
    save_csvs(frames, output_dir)
    save_charts(frames, output_dir)

    print(f"Saved EDA outputs to {output_dir}")
    print("Generated files:")
    for path in sorted(output_dir.iterdir()):
        print(f"- {path.name}")


if __name__ == "__main__":
    main()