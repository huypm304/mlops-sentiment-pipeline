#!/usr/bin/env bash
# Launch a short EC2 CPU training demo for thesis video.
#
# Usage:
#   ./scripts/demo_ec2_train.sh                 # 1 epoch, ~120 train rows (real short train)
#   ./scripts/demo_ec2_train.sh --smoke         # EC2 boots + copy baseline (fast ~2-4 min)
#   ./scripts/demo_ec2_train.sh --dry-run       # print plan only
#   ./scripts/demo_ec2_train.sh --keep          # do not terminate instance after success
#
# Requires: AWS CLI credentials, default VPC, EC2 Standard quota (already 16 vCPU).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AWS_REGION="${AWS_REGION:-ap-southeast-1}"
PROJECT="${PROJECT:-absa-mlops}"
ENVIRONMENT="${ENVIRONMENT:-demo}"
BUCKET="${ARTIFACTS_BUCKET:-${PROJECT}-${ENVIRONMENT}-artifacts}"
INSTANCE_TYPE="${INSTANCE_TYPE:-m5.2xlarge}"
DATASET_PREFIX="${DATASET_PREFIX:-datasets/pending/data-train-v2-fa3ee196}"
MODE="short"
EPOCHS=1
MAX_TRAIN=120
MAX_DEV=40
BATCH_SIZE=4
MAX_LEN=96
KEEP=0
DRY_RUN=0
POLL_SECONDS=30
TIMEOUT_MINUTES=90

while [[ $# -gt 0 ]]; do
  case "$1" in
    --smoke) MODE="smoke"; shift ;;
    --keep) KEEP=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --instance-type) INSTANCE_TYPE="$2"; shift 2 ;;
    --epochs) EPOCHS="$2"; shift 2 ;;
    --max-train) MAX_TRAIN="$2"; shift 2 ;;
    --max-dev) MAX_DEV="$2"; shift 2 ;;
    --dataset-prefix) DATASET_PREFIX="$2"; shift 2 ;;
    --timeout-minutes) TIMEOUT_MINUTES="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,14p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 1
      ;;
  esac
done

RUN_ID="ec2-demo-$(date -u +%Y%m%d-%H%M%S)"
STATUS_KEY="training-runs/${RUN_ID}/_STATUS.json"
OUT_URI="s3://${BUCKET}/training-runs/${RUN_ID}/"

echo "== ABSA EC2 demo training =="
echo "run_id:         $RUN_ID"
echo "mode:           $MODE"
echo "instance_type:  $INSTANCE_TYPE"
echo "dataset:        s3://${BUCKET}/${DATASET_PREFIX}/"
echo "output:         $OUT_URI"
echo

# Ensure source package exists
if ! aws s3 ls "s3://${BUCKET}/training/source/source.tar.gz" --region "$AWS_REGION" >/dev/null 2>&1; then
  echo "Uploading training source package..."
  bash "$ROOT/scripts/build_training_package.sh"
fi

# IAM + SG
echo "Ensuring IAM / security group..."
IAM_OUT="$(bash "$ROOT/scripts/ec2_demo/ensure_iam.sh")"
echo "$IAM_OUT"
# shellcheck disable=SC1090
eval "$(echo "$IAM_OUT" | grep -E '^(ROLE_NAME|PROFILE_NAME|SG_ID|VPC_ID)=')"

SUBNET_ID="$(aws ec2 describe-subnets --region "$AWS_REGION" \
  --filters "Name=vpc-id,Values=${VPC_ID}" "Name=default-for-az,Values=true" \
  --query 'Subnets[0].SubnetId' --output text)"

AMI_ID="$(aws ec2 describe-images --region "$AWS_REGION" --owners 099720109477 \
  --filters \
    "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
    "Name=state,Values=available" \
  --query 'sort_by(Images,&CreationDate)[-1].ImageId' --output text)"

# Upload bootstrap
aws s3 cp "$ROOT/scripts/ec2_demo/bootstrap.sh" \
  "s3://${BUCKET}/training/ec2-demo/bootstrap.sh" --region "$AWS_REGION" >/dev/null

USER_DATA=$(cat <<EOF
#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
export BUCKET=${BUCKET}
export RUN_ID=${RUN_ID}
export AWS_REGION=${AWS_REGION}
export DATASET_PREFIX=${DATASET_PREFIX}
export MODE=${MODE}
export EPOCHS=${EPOCHS}
export MAX_TRAIN=${MAX_TRAIN}
export MAX_DEV=${MAX_DEV}
export BATCH_SIZE=${BATCH_SIZE}
export MAX_LEN=${MAX_LEN}
export INSTANCE_TYPE=${INSTANCE_TYPE}
apt-get update -y
apt-get install -y awscli curl unzip
# Prefer AWSCLIv2 if apt package is thin/missing
if ! command -v aws >/dev/null 2>&1; then
  curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
  unzip -q /tmp/awscliv2.zip -d /tmp
  /tmp/aws/install
fi
aws s3 cp "s3://${BUCKET}/training/ec2-demo/bootstrap.sh" /tmp/bootstrap.sh --region "${AWS_REGION}"
chmod +x /tmp/bootstrap.sh
/tmp/bootstrap.sh
EOF
)

if [[ "$DRY_RUN" == "1" ]]; then
  echo "[dry-run] would launch:"
  echo "  AMI=$AMI_ID subnet=$SUBNET_ID sg=$SG_ID profile=$PROFILE_NAME"
  echo "  user-data bytes=$(printf '%s' "$USER_DATA" | wc -c)"
  exit 0
fi

# Seed DynamoDB row so console can show a run (best-effort)
TABLE="${TRAINING_RUNS_TABLE:-${PROJECT}-${ENVIRONMENT}-training-runs}"
CREATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
DATASET_ID="${DATASET_PREFIX##*/}"
python3 - <<PY || true
import boto3
table = "${TABLE}"
ddb = boto3.resource("dynamodb", region_name="${AWS_REGION}")
item = {
  "run_id": "${RUN_ID}",
  "created_at": "${CREATED_AT}",
  "status": "TRAINING_IN_PROGRESS",
  "training_mode": "ec2-${MODE}",
  "dataset_id": "${DATASET_ID}",
  "dataset_key": "${DATASET_PREFIX}/train.jsonl",
  "artifact_prefix": "training-runs/${RUN_ID}",
  "artifact_uri": "${OUT_URI}",
  "training_config": {
    "epochs": ${EPOCHS},
    "batch_size": ${BATCH_SIZE},
    "max_len": ${MAX_LEN},
    "sagemaker_instance_type": "${INSTANCE_TYPE}",
    "training_backend": "ec2",
  },
  "updated_at": "${CREATED_AT}",
  "requested_by": "ec2-demo-script",
}
try:
  ddb.Table(table).put_item(Item=item)
  print(f"DynamoDB put {table} ok")
except Exception as e:
  print(f"DynamoDB put skipped: {e}")
PY

echo "Launching EC2 ${INSTANCE_TYPE}..."
INSTANCE_ID="$(aws ec2 run-instances --region "$AWS_REGION" \
  --image-id "$AMI_ID" \
  --instance-type "$INSTANCE_TYPE" \
  --subnet-id "$SUBNET_ID" \
  --security-group-ids "$SG_ID" \
  --iam-instance-profile "Name=${PROFILE_NAME}" \
  --user-data "$USER_DATA" \
  --instance-initiated-shutdown-behavior terminate \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=${RUN_ID}},{Key=Project,Value=${PROJECT}},{Key=Environment,Value=${ENVIRONMENT}},{Key=Purpose,Value=ec2-demo-train}]" \
  --query 'Instances[0].InstanceId' --output text)"

echo "instance_id: $INSTANCE_ID"
echo "Console: https://${AWS_REGION}.console.aws.amazon.com/ec2/home?region=${AWS_REGION}#InstanceDetails:instanceId=${INSTANCE_ID}"
echo "S3 status: s3://${BUCKET}/${STATUS_KEY}"
echo

deadline=$(( $(date +%s) + TIMEOUT_MINUTES * 60 ))
final_status="TIMEOUT"
while (( $(date +%s) < deadline )); do
  state="$(aws ec2 describe-instances --region "$AWS_REGION" --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].State.Name' --output text 2>/dev/null || echo unknown)"
  status_json="$(aws s3 cp "s3://${BUCKET}/${STATUS_KEY}" - --region "$AWS_REGION" 2>/dev/null || true)"
  if [[ -n "$status_json" ]]; then
    echo "[$(date -u +%H:%M:%S)] ec2=$state status=$status_json"
    if echo "$status_json" | grep -q '"status": "COMPLETED"'; then
      final_status="COMPLETED"
      break
    fi
    if echo "$status_json" | grep -q '"status": "FAILED"'; then
      final_status="FAILED"
      break
    fi
  else
    echo "[$(date -u +%H:%M:%S)] ec2=$state waiting for status object..."
  fi
  if [[ "$state" == "terminated" || "$state" == "shutting-down" ]]; then
    # may have completed then shut down
    status_json="$(aws s3 cp "s3://${BUCKET}/${STATUS_KEY}" - --region "$AWS_REGION" 2>/dev/null || true)"
    if echo "$status_json" | grep -q '"status": "COMPLETED"'; then
      final_status="COMPLETED"
    else
      final_status="FAILED"
    fi
    break
  fi
  sleep "$POLL_SECONDS"
done

if [[ "$final_status" == "COMPLETED" ]]; then
  python3 - <<PY || true
import boto3
from datetime import datetime, timezone
ddb = boto3.resource("dynamodb", region_name="${AWS_REGION}")
now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
try:
  ddb.Table("${TABLE}").update_item(
    Key={"run_id": "${RUN_ID}", "created_at": "${CREATED_AT}"},
    UpdateExpression="SET #s=:s, updated_at=:u, training_mode=:m",
    ExpressionAttributeNames={"#s": "status"},
    ExpressionAttributeValues={
      ":s": "TRAINING_COMPLETED",
      ":u": now,
      ":m": "ec2-${MODE}",
    },
  )
  print("DynamoDB status -> TRAINING_COMPLETED")
except Exception as e:
  print(f"DynamoDB update skipped: {e}")
PY
  echo
  echo "SUCCESS"
  echo "  run_id:   $RUN_ID"
  echo "  artifacts:$OUT_URI"
  echo "  listing:"
  aws s3 ls "$OUT_URI" --region "$AWS_REGION" || true
else
  echo "ENDED with $final_status — check /var/log/absa-ec2-demo.log via SSM on $INSTANCE_ID" >&2
fi

if [[ "$KEEP" == "0" ]]; then
  echo "Terminating $INSTANCE_ID ..."
  aws ec2 terminate-instances --region "$AWS_REGION" --instance-ids "$INSTANCE_ID" >/dev/null || true
else
  echo "Keeping instance $INSTANCE_ID (--keep). Remember to terminate to save credits."
fi

[[ "$final_status" == "COMPLETED" ]]
