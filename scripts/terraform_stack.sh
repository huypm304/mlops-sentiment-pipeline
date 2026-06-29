#!/usr/bin/env bash
# Run terraform against bootstrap, core, or runtime stack.
# Usage: ./scripts/terraform_stack.sh <bootstrap|core|runtime> <init|plan|apply|destroy|validate>
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STACK="${1:?stack required: bootstrap|core|runtime}"
COMMAND="${2:?command required: init|plan|apply|destroy|validate}"
TF_DIR="${ROOT_DIR}/infra/${STACK}"

PROJECT="${PROJECT:-absa-mlops}"
ENVIRONMENT="${ENVIRONMENT:-demo}"
AWS_REGION="${AWS_REGION:-ap-southeast-1}"
TF_STATE_BUCKET="${TF_STATE_BUCKET:-${PROJECT}-${ENVIRONMENT}-tf-state}"
TF_STATE_LOCK_TABLE="${TF_STATE_LOCK_TABLE:-${PROJECT}-${ENVIRONMENT}-tf-locks}"

case "$STACK" in
  bootstrap) TF_STATE_KEY="" ;;
  core)      TF_STATE_KEY="core/terraform.tfstate" ;;
  runtime)   TF_STATE_KEY="runtime/terraform.tfstate" ;;
  *) echo "Unknown stack: $STACK"; exit 1 ;;
esac

export TF_VAR_core_state_bucket="${TF_STATE_BUCKET}"

cd "$TF_DIR"

_init() {
  if [[ "$STACK" == "bootstrap" ]]; then
    terraform init -input=false
  else
    terraform init -input=false \
      -backend-config="bucket=${TF_STATE_BUCKET}" \
      -backend-config="key=${TF_STATE_KEY}" \
      -backend-config="region=${AWS_REGION}" \
      -backend-config="encrypt=true" \
      -backend-config="dynamodb_table=${TF_STATE_LOCK_TABLE}"
  fi
}

case "$COMMAND" in
  init)
    _init
    ;;
  validate)
    _init
    terraform validate
    ;;
  plan)
    _init
    terraform plan -input=false
    ;;
  apply)
    _init
    terraform apply -input=false
    ;;
  destroy)
    _init
    terraform destroy -input=false
    ;;
  *)
    echo "Unknown command: $COMMAND"
    exit 1
    ;;
esac
