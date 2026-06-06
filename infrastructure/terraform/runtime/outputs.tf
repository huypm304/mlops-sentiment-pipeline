output "api_url" {
  description = "Base HTTP API URL (execute-api default)."
  value       = module.api_gateway.api_endpoint
}

output "api_custom_domain_url" {
  description = "HTTPS API URL when custom domain is configured."
  value       = module.api_gateway.custom_domain_url
}

output "step_functions_arn" {
  description = "Training pipeline state machine ARN."
  value       = module.step_functions.state_machine_arn
}

output "step_functions_name" {
  value = module.step_functions.state_machine_name
}

output "step_functions_log_group" {
  value = module.step_functions.log_group_name
}

output "lambda_function_names" {
  value = {
    predict  = module.lambda_predict.function_name
    audit    = module.lambda_audit.function_name
    pipeline = module.lambda_pipeline.function_name
    metrics  = module.lambda_metrics.function_name
  }
}

output "cloudwatch_dashboard_url" {
  value = module.cloudwatch.dashboard_url
}

output "sagemaker_endpoint_name" {
  value = module.sagemaker_optional.endpoint_name
}

output "sagemaker_endpoint_enabled" {
  value = module.sagemaker_optional.endpoint_enabled
}

output "route53_name_servers" {
  description = "Nameservers from core stack (set at registrar once)."
  value       = local.use_remote_state ? try(data.terraform_remote_state.core[0].outputs.route53_name_servers, []) : []
}

output "route53_zone_id" {
  value = local.route53_zone_id
}

output "frontend_url" {
  description = "HTTPS URL for the static frontend."
  value       = local.custom_domain_enabled ? module.frontend_cdn[0].frontend_url : ""
}

output "frontend_bucket_name" {
  value = local.custom_domain_enabled ? module.frontend_cdn[0].bucket_name : ""
}

output "cloudfront_distribution_id" {
  value = local.custom_domain_enabled ? module.frontend_cdn[0].distribution_id : ""
}
