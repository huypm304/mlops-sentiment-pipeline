#!/usr/bin/env bash
# Upload model artifacts to S3 (production baseline under models/v1/).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_DIR="${1:-$ROOT_DIR/model}"
PREFIX="${2:-models/v1}"
PROJECT="${PROJECT:-absa-mlops}"
ENVIRONMENT="${ENVIRONMENT:-demo}"
AWS_REGION="${AWS_REGION:-ap-southeast-1}"
BUCKET="${ARTIFACTS_BUCKET:-${PROJECT}-${ENVIRONMENT}-artifacts}"

echo "Uploading model from: $MODEL_DIR"
echo "Target: s3://${BUCKET}/${PREFIX}/"

aws s3 sync "$MODEL_DIR" "s3://${BUCKET}/${PREFIX}/" \
  --region "$AWS_REGION" \
  --exclude "*.pyc" \
  --exclude "__pycache__/*" \
  --exclude ".git/*"

echo "Done. Model artifacts available at s3://${BUCKET}/${PREFIX}/"
