#!/usr/bin/env bash
# Upload train_kaggle.py training package and print deploy checklist for real GPU training.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export ARTIFACTS_BUCKET="${ARTIFACTS_BUCKET:-absa-mlops-demo-artifacts}"
export AWS_REGION="${AWS_REGION:-ap-southeast-1}"

echo "==> Building & uploading SageMaker training source (train_kaggle.py + sagemaker_train.py)"
bash "${ROOT}/scripts/build_training_package.sh"

cat <<EOF

==> Next: enable real training on AWS

1. GitHub Actions → Deploy Runtime
   - enable_sagemaker_training: true  (default in workflow)
   - auto_approve: true

2. GitHub Actions → Deploy Frontend (UI banner shows GPU vs mock)

3. Dataset on S3 must include:
   - datasets/pending/<id>/train.jsonl
   - datasets/pending/<id>/dev.jsonl

4. Trigger training from console — Step Functions polls SageMaker until 50 epochs complete.

Verify API:
  curl -s https://api.minhhuy.me/pipeline/config | jq '.training_mode, .sagemaker_training_enabled'

Expected after deploy: "sagemaker" / true

EOF
