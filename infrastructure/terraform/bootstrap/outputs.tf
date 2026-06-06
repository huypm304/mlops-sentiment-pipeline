output "tf_state_bucket" {
  description = "S3 bucket that stores Terraform state for core and runtime stacks."
  value       = aws_s3_bucket.tf_state.id
}

output "tf_state_bucket_arn" {
  value = aws_s3_bucket.tf_state.arn
}

output "tf_lock_table" {
  description = "DynamoDB table used for Terraform state locking."
  value       = aws_dynamodb_table.tf_locks.name
}

output "github_deploy_role_arn" {
  description = "Set this as AWS_ROLE_ARN in your GitHub repository secrets."
  value       = module.iam_github_oidc.github_deploy_role_arn
}

output "github_oidc_provider_arn" {
  value = module.iam_github_oidc.oidc_provider_arn
}

output "aws_region" {
  value = var.aws_region
}

output "name_prefix" {
  description = "Common name prefix used by all resources in this project."
  value       = "${var.project}-${var.environment}"
}
