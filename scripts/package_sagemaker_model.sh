#!/usr/bin/env bash
# Build model.tar.gz for SageMaker endpoint and optionally upload to S3.
#
# Usage:
#   ./scripts/package_sagemaker_model.sh
#   ./scripts/package_sagemaker_model.sh --upload --bucket absa-mlops-demo-artifacts
#   ./scripts/package_sagemaker_model.sh --model-dir final_artifacts/model --upload
#
# Upload target (matches Terraform default):
#   s3://<bucket>/models/production/model.tar.gz
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_DIR="${ROOT}/final_artifacts/model"
OUTPUT="${ROOT}/dist/model.tar.gz"
S3_KEY="models/production/model.tar.gz"
UPLOAD=0
BUCKET="${ARTIFACTS_BUCKET:-absa-mlops-demo-artifacts}"
AWS_REGION="${AWS_REGION:-ap-southeast-1}"

usage() {
  sed -n '2,12p' "$0"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model-dir)
      MODEL_DIR="$2"
      shift 2
      ;;
    --output)
      OUTPUT="$2"
      shift 2
      ;;
    --bucket)
      BUCKET="$2"
      shift 2
      ;;
    --s3-key)
      S3_KEY="$2"
      shift 2
      ;;
    --upload)
      UPLOAD=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ ! -f "${MODEL_DIR}/best_model.pt" ]]; then
  echo "ERROR: ${MODEL_DIR}/best_model.pt not found." >&2
  echo "Run export first, e.g.:" >&2
  echo "  python scripts/export_model_artifacts.py --copy-checkpoint --output-dir ${MODEL_DIR}" >&2
  exit 1
fi

if [[ ! -f "${MODEL_DIR}/run_config.json" ]]; then
  echo "ERROR: ${MODEL_DIR}/run_config.json not found." >&2
  exit 1
fi

STAGING="$(mktemp -d)"
trap 'rm -rf "$STAGING"' EXIT

mkdir -p "${STAGING}/code/src"
cp -a "${ROOT}/src/absa" "${STAGING}/code/src/"
cp "${ROOT}/serving/inference.py" "${STAGING}/code/inference.py"
cp "${ROOT}/serving/requirements.txt" "${STAGING}/code/requirements.txt"

for file in best_model.pt run_config.json postprocess_config.json label_mapping.json; do
  if [[ -f "${MODEL_DIR}/${file}" ]]; then
    cp "${MODEL_DIR}/${file}" "${STAGING}/${file}"
  fi
done

mkdir -p "$(dirname "${OUTPUT}")"
tar -C "${STAGING}" -czf "${OUTPUT}" .

SIZE_MB=$(python3 - <<PY
from pathlib import Path
print(f"{Path('${OUTPUT}').stat().st_size / (1024 * 1024):.1f}")
PY
)

echo "Created ${OUTPUT} (${SIZE_MB} MB)"
echo "Contents:"
tar -tzf "${OUTPUT}" | head -20
COUNT=$(tar -tzf "${OUTPUT}" | wc -l)
if [[ "${COUNT}" -gt 20 ]]; then
  echo "... (${COUNT} files total)"
fi

if [[ "${UPLOAD}" -eq 1 ]]; then
  aws s3 cp "${OUTPUT}" "s3://${BUCKET}/${S3_KEY}" --region "${AWS_REGION}"
  echo "Uploaded: s3://${BUCKET}/${S3_KEY}"
  echo ""
  echo "Next steps:"
  echo "  1. Deploy Runtime with enable_sagemaker_endpoint=true"
  echo "  2. Wait for endpoint InService"
  echo "  3. curl -X POST https://api.minhhuy.me/predict -H 'Content-Type: application/json' -d '{\"text\":\"Giá tốt nhưng giao chậm\"}'"
fi
