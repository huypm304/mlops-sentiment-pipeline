#!/usr/bin/env bash
# Apply runtime stack (Lambda, API, Step Functions, monitoring).
set -euo pipefail
exec "$(dirname "$0")/terraform_stack.sh" runtime apply "$@"
