output "bucket_id" {
  description = "S3 bucket name."
  value       = aws_s3_bucket.artifacts.id
}

output "bucket_arn" {
  description = "S3 bucket ARN."
  value       = aws_s3_bucket.artifacts.arn
}

output "artifact_prefixes" {
  description = "Configured artifact key prefixes."
  value       = var.artifact_prefixes
}
