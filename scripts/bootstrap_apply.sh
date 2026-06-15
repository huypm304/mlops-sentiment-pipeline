#!/usr/bin/env bash
# Apply bootstrap stack (once per AWS account).
set -euo pipefail
exec "$(dirname "$0")/terraform_stack.sh" bootstrap apply "$@"
