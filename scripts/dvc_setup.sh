#!/usr/bin/env bash
# One-time DVC setup for official benchmark dataset versioning.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUCKET="${ARTIFACTS_BUCKET:-absa-mlops-demo-artifacts}"
REMOTE_NAME="${DVC_REMOTE_NAME:-s3remote}"
REMOTE_URL="${DVC_REMOTE_URL:-s3://${BUCKET}/dvc-store}"

cd "${ROOT}"

if ! command -v dvc >/dev/null 2>&1; then
  echo "Installing DVC with S3 support..."
  python3 -m pip install --upgrade 'dvc[s3]'
fi

if [[ ! -d .dvc ]]; then
  echo "Initializing DVC..."
  dvc init -q
fi

if dvc remote list | grep -q "^${REMOTE_NAME}[[:space:]]"; then
  echo "Updating DVC remote '${REMOTE_NAME}' -> ${REMOTE_URL}"
  dvc remote modify "${REMOTE_NAME}" url "${REMOTE_URL}"
else
  echo "Adding DVC remote '${REMOTE_NAME}' -> ${REMOTE_URL}"
  dvc remote add -d "${REMOTE_NAME}" "${REMOTE_URL}"
fi

echo ""
echo "DVC ready."
echo ""
echo "Next:"
echo "  1. Place train.jsonl, dev.jsonl, test.jsonl in data/processed/"
echo "  2. cd data/processed && dvc add train.jsonl dev.jsonl test.jsonl"
echo "  3. dvc push"
echo "  4. git add *.dvc .gitignore && git commit -m 'Track benchmark dataset with DVC'"
echo "  5. python scripts/publish_approved_dataset.py --dataset-id dataset-v1"
