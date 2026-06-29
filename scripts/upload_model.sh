#!/usr/bin/env bash
# Upload model artifacts to S3 and optionally seed DynamoDB registry.
#
# Usage:
#   ./scripts/upload_model.sh /path/to/staging models/v1
#   ./scripts/upload_model.sh /path/to/staging models/v1 --seed --model-id absa-v2b
#
# Staging dir must contain at least train_log.csv and run_config.json for metrics API.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_DIR="${1:-}"
PREFIX="${2:-models/v1}"
PROJECT="${PROJECT:-absa-mlops}"
ENVIRONMENT="${ENVIRONMENT:-demo}"
AWS_REGION="${AWS_REGION:-ap-southeast-1}"
BUCKET="${ARTIFACTS_BUCKET:-${PROJECT}-${ENVIRONMENT}-artifacts}"
SEED=false
MODEL_ID="absa-v2b"
DATASET_ID="dataset-v1"

shift 2 2>/dev/null || true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --seed) SEED=true; shift ;;
    --model-id) MODEL_ID="$2"; shift 2 ;;
    --dataset-id) DATASET_ID="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$MODEL_DIR" ]]; then
  echo "Usage: $0 <staging-dir> [s3-prefix] [--seed] [--model-id ID]" >&2
  echo "  Staging dir needs train_log.csv, run_config.json, best_model.pt (optional)." >&2
  exit 1
fi

if [[ ! -d "$MODEL_DIR" ]]; then
  echo "ERROR: staging dir not found: $MODEL_DIR" >&2
  exit 1
fi

if [[ ! -f "$MODEL_DIR/train_log.csv" ]]; then
  echo "ERROR: missing train_log.csv in $MODEL_DIR (required for metrics API)" >&2
  exit 1
fi

echo "Uploading model from: $MODEL_DIR"
echo "Target: s3://${BUCKET}/${PREFIX}/"

aws s3 sync "$MODEL_DIR" "s3://${BUCKET}/${PREFIX}/" \
  --region "$AWS_REGION" \
  --exclude "*.pyc" \
  --exclude "__pycache__/*" \
  --exclude ".git/*"

echo "Done. Model artifacts at s3://${BUCKET}/${PREFIX}/"

if [[ "$SEED" == true ]]; then
  echo "Seeding model registry from S3..."
  export ARTIFACTS_BUCKET="$BUCKET"
  python3 "${ROOT_DIR}/scripts/seed_registry.py" \
    --model-id "$MODEL_ID" \
    --dataset-id "$DATASET_ID" \
    --artifact-prefix "$PREFIX"
fi
