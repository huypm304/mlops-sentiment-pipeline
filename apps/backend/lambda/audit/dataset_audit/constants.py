"""Schema constants aligned with model training (ViBERTa ABSA)."""

ASPECT_ORDER = [
    "Fashion",
    "Electronics",
    "General",
    "Service",
    "Ship",
    "Price",
    "App",
]
VALID_ASPECTS = frozenset(ASPECT_ORDER)
VALID_SENTIMENTS = frozenset({0, 1, 2})
SENTIMENT_LABELS = {0: "Negative", 1: "Positive", 2: "Neutral"}

# Thesis demo thresholds (benchmark gates for training approval).
BENCHMARK_THRESHOLDS = {
    "record_parse_rate": 1.0,
    "span_offset_accuracy": 0.97,
    "aspect_schema_rate": 1.0,
    "sentiment_schema_rate": 1.0,
    "duplicate_opinion_rate_max": 0.02,
    "empty_target_rate_max": 0.01,
    "global_consistency_rate": 0.85,
}
