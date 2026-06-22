output "api_id" {
  value = aws_apigatewayv2_api.http.id
}

output "api_endpoint" {
  description = "Base invoke URL (execute-api default)."
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "api_execution_arn" {
  value = aws_apigatewayv2_api.http.execution_arn
}

output "custom_domain_url" {
  description = "HTTPS URL when custom domain is configured."
  value       = var.custom_domain_name != "" ? "https://${var.custom_domain_name}" : ""
}

output "custom_domain_target" {
  description = "Regional domain target for Route53 alias record."
  value       = var.custom_domain_name != "" ? aws_apigatewayv2_domain_name.api[0].domain_name_configuration[0].target_domain_name : ""
}

output "custom_domain_hosted_zone_id" {
  description = "Hosted zone ID for the Route53 alias record."
  value       = var.custom_domain_name != "" ? aws_apigatewayv2_domain_name.api[0].domain_name_configuration[0].hosted_zone_id : ""
}
