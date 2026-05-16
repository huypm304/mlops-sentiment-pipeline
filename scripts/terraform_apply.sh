#!/usr/bin/env bash
# Run terraform apply for dev or prod environment.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENVIRONMENT="${1:-dev}"
TF_DIR="${ROOT_DIR}/infrastructure/terraform/environments/${ENVIRONMENT}"

if [[ ! -d "$TF_DIR" ]]; then
  echo "Unknown environment: $ENVIRONMENT (expected dev or prod)"
  exit 1
fi

shift || true

echo "Terraform apply — environment: $ENVIRONMENT"
echo "Working directory: $TF_DIR"

cd "$TF_DIR"
_init_backend() {
  if [[ -n "${TF_STATE_BUCKET:-}" ]]; then
    terraform init -input=false \
      -backend-config="bucket=${TF_STATE_BUCKET}" \
      -backend-config="key=${TF_STATE_KEY:-absa-mlops-platform/${ENVIRONMENT}/terraform.tfstate}" \
      -backend-config="region=${AWS_REGION:-ap-southeast-1}" \
      -backend-config="encrypt=true" \
      -backend-config="dynamodb_table=${TF_STATE_LOCK_TABLE:-absa-mlops-platform-terraform-lock}"
  else
    echo "Tip: set TF_STATE_BUCKET for remote state (see scripts/bootstrap_tf_state.sh)"
    terraform init -input=false
  fi
}
_init_backend
terraform validate
terraform apply -input=false "$@"
