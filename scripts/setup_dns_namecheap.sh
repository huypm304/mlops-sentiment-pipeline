#!/usr/bin/env bash
# Print Route53 nameservers from the runtime stack (for domain registrar delegation).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="${ROOT_DIR}/infrastructure/terraform/runtime"

cd "$TF_DIR"

echo "Route53 nameservers:"
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
echo "API URL:"
terraform output -raw api_custom_domain_url 2>/dev/null || terraform output -raw api_url 2>/dev/null || echo "  (run runtime apply first)"
