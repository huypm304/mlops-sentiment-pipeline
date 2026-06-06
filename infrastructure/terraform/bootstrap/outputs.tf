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

output "aws_region" {
  value = var.aws_region
}

output "name_prefix" {
  description = "Common name prefix used by all resources in this project."
  value       = "${var.project}-${var.environment}"
}
