#!/usr/bin/env bash
# Apply core stack (persistent artifacts + DynamoDB registry).
set -euo pipefail
exec "$(dirname "$0")/terraform_stack.sh" core apply "$@"
