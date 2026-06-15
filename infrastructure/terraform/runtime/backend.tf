# Remote state is stored in the S3 bucket created by the bootstrap stack.
# Initialise with:
#   terraform init \
#     -backend-config="bucket=absa-mlops-demo-tf-state" \
#     -backend-config="key=runtime/terraform.tfstate" \
#     -backend-config="region=ap-southeast-1" \
#     -backend-config="dynamodb_table=absa-mlops-demo-tf-locks"
terraform {
  backend "s3" {}
}
