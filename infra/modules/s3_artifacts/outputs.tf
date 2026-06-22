output "bucket_id" {
  description = "Artifact bucket name."
  value       = aws_s3_bucket.artifacts.id
}

output "bucket_arn" {
  description = "Artifact bucket ARN."
  value       = aws_s3_bucket.artifacts.arn
}

output "bucket_name" {
  description = "Artifact bucket name (alias for bucket_id)."
  value       = aws_s3_bucket.artifacts.id
}

output "artifact_prefixes" {
  description = "All configured S3 key prefixes."
  value       = local.artifact_prefixes
}
