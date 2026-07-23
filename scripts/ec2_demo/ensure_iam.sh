#!/usr/bin/env bash
# Ensure IAM role + instance profile + security group for EC2 demo training.
set -euo pipefail

AWS_REGION="${AWS_REGION:-ap-southeast-1}"
PROJECT="${PROJECT:-absa-mlops}"
ENVIRONMENT="${ENVIRONMENT:-demo}"
BUCKET="${ARTIFACTS_BUCKET:-${PROJECT}-${ENVIRONMENT}-artifacts}"
ROLE_NAME="${EC2_ROLE_NAME:-${PROJECT}-${ENVIRONMENT}-ec2-train-role}"
PROFILE_NAME="${EC2_PROFILE_NAME:-${PROJECT}-${ENVIRONMENT}-ec2-train-profile}"
SG_NAME="${EC2_SG_NAME:-${PROJECT}-${ENVIRONMENT}-ec2-train-sg}"

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
VPC_ID="${VPC_ID:-$(aws ec2 describe-vpcs --region "$AWS_REGION" --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text)}"

if [[ -z "$VPC_ID" || "$VPC_ID" == "None" ]]; then
  echo "ERROR: no default VPC in $AWS_REGION" >&2
  exit 1
fi

# --- IAM role ---
if ! aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
  aws iam create-role \
    --role-name "$ROLE_NAME" \
    --assume-role-policy-document '{
      "Version":"2012-10-17",
      "Statement":[{
        "Effect":"Allow",
        "Principal":{"Service":"ec2.amazonaws.com"},
        "Action":"sts:AssumeRole"
      }]
    }' >/dev/null
  echo "Created role $ROLE_NAME"
fi

aws iam attach-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore >/dev/null || true

INLINE_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ArtifactsBucket",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket", "s3:DeleteObject"],
      "Resource": [
        "arn:aws:s3:::${BUCKET}",
        "arn:aws:s3:::${BUCKET}/*"
      ]
    },
    {
      "Sid": "Logs",
      "Effect": "Allow",
      "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
      "Resource": "*"
    }
  ]
}
EOF
)
aws iam put-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name "${ROLE_NAME}-inline" \
  --policy-document "$INLINE_POLICY" >/dev/null

if ! aws iam get-instance-profile --instance-profile-name "$PROFILE_NAME" >/dev/null 2>&1; then
  aws iam create-instance-profile --instance-profile-name "$PROFILE_NAME" >/dev/null
  aws iam add-role-to-instance-profile --instance-profile-name "$PROFILE_NAME" --role-name "$ROLE_NAME" >/dev/null
  echo "Created instance profile $PROFILE_NAME"
  # IAM eventual consistency
  sleep 8
fi

# --- Security group (egress only; SSM needs no inbound) ---
SG_ID="$(aws ec2 describe-security-groups --region "$AWS_REGION" \
  --filters "Name=group-name,Values=${SG_NAME}" "Name=vpc-id,Values=${VPC_ID}" \
  --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null || true)"

if [[ -z "$SG_ID" || "$SG_ID" == "None" ]]; then
  SG_ID="$(aws ec2 create-security-group --region "$AWS_REGION" \
    --group-name "$SG_NAME" \
    --description "ABSA EC2 demo train (SSM, egress only)" \
    --vpc-id "$VPC_ID" \
    --query GroupId --output text)"
  aws ec2 authorize-security-group-egress --region "$AWS_REGION" \
    --group-id "$SG_ID" \
    --ip-permissions 'IpProtocol=-1,IpRanges=[{CidrIp=0.0.0.0/0}]' >/dev/null 2>&1 || true
  echo "Created security group $SG_ID"
fi

cat <<EOF
ROLE_NAME=$ROLE_NAME
PROFILE_NAME=$PROFILE_NAME
SG_ID=$SG_ID
VPC_ID=$VPC_ID
ACCOUNT_ID=$ACCOUNT_ID
BUCKET=$BUCKET
EOF
