output "endpoint_name" {
  description = "SageMaker endpoint name. Available even when endpoint is disabled."
  value       = local.endpoint_name
}

output "endpoint_enabled" {
  value = var.enable_endpoint
}

output "endpoint_arn" {
  description = "ARN of the SageMaker endpoint. Empty string when disabled."
  value       = var.enable_endpoint ? aws_sagemaker_endpoint.absa[0].arn : ""
}

output "model_s3_uri" {
  value = local.model_s3_uri
}
