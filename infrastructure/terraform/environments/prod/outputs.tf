output "api_endpoint" {
  value = module.platform.api_endpoint
}

output "artifacts_bucket" {
  value = module.platform.artifacts_bucket
}

output "retrain_state_machine_arn" {
  value = module.platform.retrain_state_machine_arn
}

output "api_custom_domain_url" {
  value = module.platform.api_custom_domain_url
}

output "route53_zone_id" {
  value = module.platform.route53_zone_id
}
