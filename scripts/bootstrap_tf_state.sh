#!/usr/bin/env bash
# One-time: create S3 bucket + DynamoDB table for Terraform remote state (CI/CD + local).
set -euo pipefail

AWS_REGION="${AWS_REGION:-ap-southeast-1}"
PROJECT_NAME="${PROJECT_NAME:-absa-mlops-platform}"
BUCKET="${TF_STATE_BUCKET:-${PROJECT_NAME}-terraform-state}"
LOCK_TABLE="${TF_STATE_LOCK_TABLE:-${PROJECT_NAME}-terraform-lock}"

echo "Region: $AWS_REGION"
echo "State bucket: $BUCKET"
echo "Lock table: $LOCK_TABLE"

if aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  echo "Bucket already exists: $BUCKET"
else
  if [[ "$AWS_REGION" == "us-east-1" ]]; then
    aws s3api create-bucket --bucket "$BUCKET" --region "$AWS_REGION"
  else
    aws s3api create-bucket \
      --bucket "$BUCKET" \
      --region "$AWS_REGION" \
      --create-bucket-configuration "LocationConstraint=$AWS_REGION"
  fi
  aws s3api put-bucket-versioning \
    --bucket "$BUCKET" \
    --versioning-configuration Status=Enabled
  aws s3api put-bucket-encryption \
    --bucket "$BUCKET" \
    --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
  echo "Created bucket: $BUCKET"
fi

if aws dynamodb describe-table --table-name "$LOCK_TABLE" --region "$AWS_REGION" 2>/dev/null; then
  echo "Lock table already exists: $LOCK_TABLE"
else
  aws dynamodb create-table \
    --table-name "$LOCK_TABLE" \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region "$AWS_REGION"
  echo "Created lock table: $LOCK_TABLE"
fi

echo ""
echo "Add these GitHub repository secrets (Settings → Secrets → Actions):"
echo "  AWS_ACCESS_KEY_ID"
echo "  AWS_SECRET_ACCESS_KEY"
echo "  AWS_REGION=$AWS_REGION"
echo "  TF_STATE_BUCKET=$BUCKET"
echo "  TF_STATE_LOCK_TABLE=$LOCK_TABLE"
echo ""
echo "Local init example (dev):"
echo "  cd infrastructure/terraform/environments/dev"
echo "  terraform init \\"
echo "    -backend-config=bucket=$BUCKET \\"
echo "    -backend-config=key=absa-mlops-platform/dev/terraform.tfstate \\"
echo "    -backend-config=region=$AWS_REGION \\"
echo "    -backend-config=dynamodb_table=$LOCK_TABLE \\"
echo "    -backend-config=encrypt=true"
