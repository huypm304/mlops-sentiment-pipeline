#!/usr/bin/env bash
# Package ml/inference + training entry for SageMaker source.tar.gz upload.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="${PROJECT:-absa-mlops}"
ENVIRONMENT="${ENVIRONMENT:-demo}"
AWS_REGION="${AWS_REGION:-ap-southeast-1}"
BUCKET="${ARTIFACTS_BUCKET:-${PROJECT}-${ENVIRONMENT}-artifacts}"
OUT="${ROOT_DIR}/dist/training-source.tar.gz"
STAGE="${ROOT_DIR}/dist/training-package"

rm -rf "$STAGE" "$(dirname "$OUT")"
mkdir -p "$STAGE/training" "$STAGE/ml"

cp -r "${ROOT_DIR}/ml/inference" "${STAGE}/ml/"
touch "${STAGE}/ml/__init__.py"
cp "${ROOT_DIR}/ml/training/sagemaker_train.py" "${STAGE}/training/"
cp "${ROOT_DIR}/ml/configs/requirements.txt" "${STAGE}/requirements.txt" 2>/dev/null || \
  cp "${ROOT_DIR}/artifacts/model/requirements.txt" "${STAGE}/requirements.txt"

tar -czf "$OUT" -C "$STAGE" .

echo "Built: $OUT"
aws s3 cp "$OUT" "s3://${BUCKET}/training/source/source.tar.gz" --region "$AWS_REGION"
echo "Uploaded: s3://${BUCKET}/training/source/source.tar.gz"
