#!/usr/bin/env bash
# Destroy Terraform stack (save AWS costs when not testing).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENVIRONMENT="${1:-dev}"
TF_DIR="${ROOT_DIR}/infrastructure/terraform/environments/${ENVIRONMENT}"

if [[ ! -d "$TF_DIR" ]]; then
  echo "Unknown environment: $ENVIRONMENT"
  exit 1
fi

shift || true
CONFIRM="${CONFIRM:-}"

if [[ "${CONFIRM}" != "destroy-${ENVIRONMENT}" ]]; then
  echo "Set CONFIRM=destroy-${ENVIRONMENT} to proceed, e.g.:"
  echo "  CONFIRM=destroy-dev $0 dev"
  exit 1
fi

echo "Destroying environment: $ENVIRONMENT"
cd "$TF_DIR"

if [[ -n "${TF_STATE_BUCKET:-}" ]]; then
  terraform init -input=false \
    -backend-config="bucket=${TF_STATE_BUCKET}" \
    -backend-config="key=${TF_STATE_KEY:-absa-mlops-platform/${ENVIRONMENT}/terraform.tfstate}" \
    -backend-config="region=${AWS_REGION:-ap-southeast-1}" \
    -backend-config="encrypt=true" \
    -backend-config="dynamodb_table=${TF_STATE_LOCK_TABLE:-absa-mlops-platform-terraform-lock}"
else
  terraform init -input=false
fi

terraform destroy -input=false "$@"
