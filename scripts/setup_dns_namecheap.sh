#!/usr/bin/env bash
# Print Route53 nameservers after terraform apply (for Namecheap delegation).
set -euo pipefail

ENVIRONMENT="${1:-dev}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="${ROOT_DIR}/infrastructure/terraform/environments/${ENVIRONMENT}"

if [[ ! -d "$TF_DIR" ]]; then
  echo "Unknown environment: $ENVIRONMENT"
  exit 1
fi

cd "$TF_DIR"

echo "Route53 nameservers for ${ENVIRONMENT}:"
terraform output -json route53_name_servers 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
if not data:
    print('  (custom domain disabled or not applied yet)')
else:
    for ns in data:
        print(f'  {ns}')
"

echo ""
echo "Namecheap steps:"
echo "  1. Domain List → minhhuy.me → Domain"
echo "  2. Nameservers → Custom DNS"
echo "  3. Paste the 4 nameservers above → Save"
echo ""
echo "API URL:"
terraform output -raw api_custom_domain_url 2>/dev/null || echo "  (run terraform apply with enable_custom_domain=true)"
