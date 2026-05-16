output "environment" {
  value = var.environment
}

output "artifacts_bucket" {
  description = "Primary S3 bucket for datasets, models, reports, evaluation, artifacts."
  value       = module.s3.bucket_id
}

output "artifact_prefixes" {
  value = module.s3.artifact_prefixes
}

output "api_endpoint" {
  description = "HTTP API base URL (default execute-api URL)."
  value       = module.api_gateway.api_endpoint
}

output "api_custom_domain_url" {
  description = "HTTPS API URL when custom domain is enabled."
  value       = module.api_gateway.custom_domain_url
}

output "domain_name" {
  value = var.domain_name
}

output "route53_zone_id" {
  value = length(module.route53) > 0 ? module.route53[0].zone_id : null
}

output "route53_name_servers" {
  description = "Delegate minhhuy.me to these nameservers in Namecheap (Custom DNS)."
  value       = length(module.route53) > 0 ? module.route53[0].name_servers : []
}

output "lambda_functions" {
  value = {
    predict         = module.lambda_predict.function_name
    analytics       = module.lambda_analytics.function_name
    audit           = module.lambda_audit.function_name
    retrain_trigger = module.lambda_retrain_trigger.function_name
  }
}

output "retrain_state_machine_arn" {
  value = module.step_functions.state_machine_arn
}

output "sagemaker_endpoint_name" {
  value = module.sagemaker.endpoint_name
}

output "sagemaker_endpoint_enabled" {
  value = module.sagemaker.endpoint_enabled
}
