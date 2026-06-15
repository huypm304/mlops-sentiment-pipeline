#!/usr/bin/env bash
# Destroy runtime stack only. Core artifacts are preserved.
set -euo pipefail
exec "$(dirname "$0")/terraform_stack.sh" runtime destroy "$@"
