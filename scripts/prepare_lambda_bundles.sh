#!/usr/bin/env bash
# Copy Lambda sources + shared registry package into apps/backend/lambda/.build/* for Terraform packaging.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REGISTRY_SRC="$ROOT/apps/backend/registry"
LAMBDA_ROOT="$ROOT/apps/backend/lambda"

copy_bundle() {
  local name="$1"
  local src="$LAMBDA_ROOT/$name"
  local dest="$LAMBDA_ROOT/.build/$name"

  rm -rf "$dest"
  mkdir -p "$dest"
  cp -a "$src/." "$dest/"
  cp -a "$REGISTRY_SRC" "$dest/registry"
}

for fn in audit pipeline metrics predict; do
  copy_bundle "$fn"
done

echo "Lambda bundles ready under apps/backend/lambda/.build/{audit,pipeline,metrics,predict}"
