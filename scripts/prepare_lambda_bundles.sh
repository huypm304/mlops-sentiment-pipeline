#!/usr/bin/env bash
# Copy Lambda sources + shared registry package into lambda/.build/* for Terraform packaging.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REGISTRY_SRC="$ROOT/registry"

copy_bundle() {
  local name="$1"
  local src="$ROOT/lambda/$name"
  local dest="$ROOT/lambda/.build/$name"

  rm -rf "$dest"
  mkdir -p "$dest"
  cp -a "$src/." "$dest/"
  cp -a "$REGISTRY_SRC" "$dest/registry"
}

for fn in audit pipeline metrics predict; do
  copy_bundle "$fn"
done

echo "Lambda bundles ready under lambda/.build/{audit,pipeline,metrics,predict}"
