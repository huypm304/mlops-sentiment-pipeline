#!/usr/bin/env bash
# Upload model artifacts to S3 (models/ prefix).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_DIR="${1:-$ROOT_DIR/model}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
PROJECT_NAME="${PROJECT_NAME:-absa-mlops-platform}"
AWS_REGION="${AWS_REGION:-ap-southeast-1}"
BUCKET="${ARTIFACTS_BUCKET:-${PROJECT_NAME}-${ENVIRONMENT}}"

echo "Uploading model from: $MODEL_DIR"
echo "Target: s3://${BUCKET}/models/latest/"

aws s3 sync "$MODEL_DIR" "s3://${BUCKET}/models/latest/" \
  --region "$AWS_REGION" \
  --exclude "*.pyc" \
  --exclude "__pycache__/*" \
  --exclude ".git/*"

echo "Done. Model artifacts available at s3://${BUCKET}/models/latest/"
