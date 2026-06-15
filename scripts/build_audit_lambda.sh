#!/usr/bin/env bash
# Bundle audit Lambda with the portable data_benchmark suite.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="$ROOT/lambda/.build/audit"

bash "$ROOT/scripts/prepare_lambda_bundles.sh"
rsync -a --delete "$ROOT/data_benchmark/" "$BUILD/data_benchmark/"
echo "Audit Lambda bundle ready: $BUILD"
