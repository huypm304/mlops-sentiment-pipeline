#!/usr/bin/env bash
# Upload a dataset file to S3 (datasets/pending/ prefix).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATASET_FILE="${1:-}"
PROJECT="${PROJECT:-absa-mlops}"
ENVIRONMENT="${ENVIRONMENT:-demo}"
AWS_REGION="${AWS_REGION:-ap-southeast-1}"
BUCKET="${ARTIFACTS_BUCKET:-${PROJECT}-${ENVIRONMENT}-artifacts}"

if [[ -z "$DATASET_FILE" ]]; then
  echo "Usage: $0 <path-to-dataset.jsonl> [s3-key]"
  echo "Example: $0 data/train.jsonl datasets/pending/train-v2.jsonl"
  exit 1
fi

if [[ ! -f "$DATASET_FILE" ]]; then
  echo "File not found: $DATASET_FILE"
  exit 1
fi

S3_KEY="${2:-datasets/pending/$(basename "$DATASET_FILE")}"

echo "Uploading: $DATASET_FILE"
echo "Target: s3://${BUCKET}/${S3_KEY}"

aws s3 cp "$DATASET_FILE" "s3://${BUCKET}/${S3_KEY}" --region "$AWS_REGION"

echo "Done. Dataset available at s3://${BUCKET}/${S3_KEY}"
