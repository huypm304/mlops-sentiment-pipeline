#!/usr/bin/env bash
# Package and deploy a Lambda function via AWS CLI (thesis demo helper).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FUNCTION_KEY="${1:-}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
PROJECT_NAME="${PROJECT_NAME:-absa-mlops-platform}"
AWS_REGION="${AWS_REGION:-ap-southeast-1}"

usage() {
  echo "Usage: $0 <predict|analytics|audit|retrain_trigger>"
  echo "Deploys lambda/<name>/ to ${PROJECT_NAME}-${ENVIRONMENT}-<name>"
  exit 1
}

[[ -z "$FUNCTION_KEY" ]] && usage

case "$FUNCTION_KEY" in
  predict)         DIR_NAME="predict"; AWS_SUFFIX="predict" ;;
  analytics)       DIR_NAME="analytics"; AWS_SUFFIX="analytics" ;;
  audit)           DIR_NAME="audit"; AWS_SUFFIX="audit" ;;
  retrain_trigger) DIR_NAME="retrain_trigger"; AWS_SUFFIX="retrain-trigger" ;;
  *) usage ;;
esac

SRC_DIR="${ROOT_DIR}/lambda/${DIR_NAME}"
BUILD_DIR="${ROOT_DIR}/.build/lambda"
ZIP_PATH="${BUILD_DIR}/${DIR_NAME}.zip"
AWS_NAME="${PROJECT_NAME}-${ENVIRONMENT}-${AWS_SUFFIX}"

if [[ ! -d "$SRC_DIR" ]]; then
  echo "Lambda source not found: $SRC_DIR"
  exit 1
fi

mkdir -p "$BUILD_DIR"
rm -f "$ZIP_PATH"

echo "Packaging $SRC_DIR -> $ZIP_PATH"
(
  cd "$SRC_DIR"
  if [[ -f requirements.txt ]] && grep -qv '^\s*$' requirements.txt 2>/dev/null; then
    pip install -q -r requirements.txt -t "$BUILD_DIR/${DIR_NAME}_deps" --upgrade
    cd "$BUILD_DIR/${DIR_NAME}_deps"
    zip -qr "$ZIP_PATH" .
    cd "$SRC_DIR"
    zip -q "$ZIP_PATH" handler.py
    if ls *.py 2>/dev/null | grep -qv '^handler\.py$'; then
      zip -q "$ZIP_PATH" *.py
    fi
  else
    zip -q "$ZIP_PATH" handler.py
    if ls *.py 2>/dev/null | grep -qv '^handler\.py$'; then
      zip -q "$ZIP_PATH" *.py
    fi
  fi
)

echo "Updating Lambda: $AWS_NAME (region $AWS_REGION)"
aws lambda update-function-code \
  --function-name "$AWS_NAME" \
  --zip-file "fileb://${ZIP_PATH}" \
  --region "$AWS_REGION"

echo "Done. Deployed $AWS_NAME"
