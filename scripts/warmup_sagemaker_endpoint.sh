#!/usr/bin/env bash
# Warm up SageMaker endpoint after deploy or model upload (model load can take 2–5 minutes).
set -euo pipefail

ENDPOINT="${1:-absa-mlops-demo-endpoint}"
AWS_REGION="${AWS_REGION:-ap-southeast-1}"
BODY='{"text":"Gia tot nhung giao cham"}'
OUT="$(mktemp)"

echo "Warming endpoint: ${ENDPOINT} (${AWS_REGION})"
for attempt in $(seq 1 24); do
  STATUS="$(aws sagemaker describe-endpoint \
    --endpoint-name "${ENDPOINT}" \
    --region "${AWS_REGION}" \
    --query 'EndpointStatus' \
    --output text 2>/dev/null || echo "Missing")"
  echo "Attempt ${attempt}/24 — endpoint status: ${STATUS}"

  if [[ "${STATUS}" != "InService" ]]; then
    sleep 15
    continue
  fi

  printf '%s' "${BODY}" > /tmp/absa-warmup-body.json
  if aws sagemaker-runtime invoke-endpoint \
    --endpoint-name "${ENDPOINT}" \
    --region "${AWS_REGION}" \
    --content-type application/json \
    --accept application/json \
    --body fileb:///tmp/absa-warmup-body.json \
    "${OUT}" >/tmp/absa-warmup-meta.json 2>/tmp/absa-warmup-err.txt; then
    echo "Warmup OK:"
    head -c 400 "${OUT}"
    echo
    rm -f "${OUT}" /tmp/absa-warmup-body.json /tmp/absa-warmup-meta.json /tmp/absa-warmup-err.txt
    exit 0
  fi

  echo "Invoke failed (will retry in 15s):"
  tail -3 /tmp/absa-warmup-err.txt || true
  sleep 15
done

echo "Warmup failed after 24 attempts. Check CloudWatch: /aws/sagemaker/Endpoints/${ENDPOINT}" >&2
exit 1
