#!/usr/bin/env bash
# Demo E2E pipeline (mock training) — trigger via API and poll until complete.
#
# Prerequisites:
#   - Deploy Runtime with Step Functions + pipeline Lambda
#   - ARTIFACTS_BUCKET, API_URL, optional DATASET_ID
#
# Usage:
#   export API_URL=https://api.minhhuy.me
#   export DATASET_ID=my-dataset-id
#   ./scripts/demo_e2e_pipeline.sh
set -euo pipefail

API_URL="${API_URL:-https://api.minhhuy.me}"
DATASET_ID="${DATASET_ID:-}"
BASE_MODEL_ID="${BASE_MODEL_ID:-absa-v2b}"
POLL_SEC="${POLL_SEC:-8}"
MAX_WAIT_SEC="${MAX_WAIT_SEC:-600}"

if [[ -z "$DATASET_ID" ]]; then
  echo "Fetching first dataset from API..."
  DATASET_ID="$(curl -sf "${API_URL}/datasets" | python3 -c "
import json, sys
rows = json.load(sys.stdin)
if isinstance(rows, list) and rows:
    print(rows[0].get('dataset_id', ''))
elif isinstance(rows, dict) and rows.get('datasets'):
    print(rows['datasets'][0].get('dataset_id', ''))
")"
fi

if [[ -z "$DATASET_ID" ]]; then
  echo "ERROR: Set DATASET_ID or ensure /datasets returns at least one row." >&2
  exit 1
fi

echo "Triggering pipeline: dataset=$DATASET_ID base=$BASE_MODEL_ID"

BODY="$(python3 - <<PY
import json
print(json.dumps({
    "dataset_id": "${DATASET_ID}",
    "base_model_id": "${BASE_MODEL_ID}",
    "requested_by": "demo-script",
    "training_config": {
        "epochs": 50,
        "batch_size": 24,
        "lr_backbone": 8e-6,
        "lr_heads": 3e-5,
        "lambda_bio": 1.1,
        "lambda_sent": 1.4,
        "lambda_global": 0.2,
        "contrast_sampler_weight": 1.2,
        "pred_span_ratio": 0.1,
    },
}))
PY
)"

RESP="$(curl -sf -X POST "${API_URL}/pipeline/trigger" \
  -H "Content-Type: application/json" \
  -d "$BODY")"

echo "$RESP" | python3 -m json.tool

RUN_ID="$(echo "$RESP" | python3 -c "import json,sys; print(json.load(sys.stdin).get('run_id',''))")"

if [[ -z "$RUN_ID" ]]; then
  echo "ERROR: No run_id in response" >&2
  exit 1
fi

echo ""
echo "Run ID: $RUN_ID"
echo "Polling ${API_URL}/pipeline/runs/${RUN_ID} (max ${MAX_WAIT_SEC}s)..."

deadline=$((SECONDS + MAX_WAIT_SEC))
while (( SECONDS < deadline )); do
  DETAIL="$(curl -sf "${API_URL}/pipeline/runs/${RUN_ID}")"
  STATUS="$(echo "$DETAIL" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status',''))")"
  BEST="$(echo "$DETAIL" | python3 -c "
import json,sys
d=json.load(sys.stdin)
m=d.get('metrics') or (d.get('evaluation') or {}).get('metrics') or {}
print(m.get('tas_relaxed_f1', m.get('global_f1', '')))
")"
  echo "[$(date -Iseconds)] status=$STATUS best_f1=$BEST"
  if [[ "$STATUS" == "COMPLETED" || "$STATUS" == "REJECTED" || "$STATUS" == "FAILED" ]]; then
    echo ""
    echo "$DETAIL" | python3 -m json.tool
    exit 0
  fi
  sleep "$POLL_SEC"
done

echo "TIMEOUT waiting for run $RUN_ID" >&2
exit 1
