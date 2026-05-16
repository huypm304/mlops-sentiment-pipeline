output "execution_role_arn" {
  value = aws_iam_role.sagemaker.arn
}

output "model_s3_uri" {
  value = local.model_s3_uri
}

output "endpoint_name" {
  value = var.enable_endpoint ? aws_sagemaker_endpoint.absa[0].name : local.endpoint_name
}

output "endpoint_enabled" {
  value = var.enable_endpoint
}
