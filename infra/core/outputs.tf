output "artifact_bucket_name" {
  description = "Name of the primary S3 artifact bucket."
  value       = module.s3_artifacts.bucket_name
}

output "artifact_bucket_arn" {
  value = module.s3_artifacts.bucket_arn
}

output "artifact_prefixes" {
  value = module.s3_artifacts.artifact_prefixes
}

output "datasets_table_name" {
  value = module.dynamodb_registry.datasets_table_name
}

output "datasets_table_arn" {
  value = module.dynamodb_registry.datasets_table_arn
}

output "training_runs_table_name" {
  value = module.dynamodb_registry.training_runs_table_name
}

output "training_runs_table_arn" {
  value = module.dynamodb_registry.training_runs_table_arn
}

output "models_table_name" {
  value = module.dynamodb_registry.models_table_name
}

output "models_table_arn" {
  value = module.dynamodb_registry.models_table_arn
}

output "predictions_table_name" {
  value = module.dynamodb_registry.predictions_table_name
}

output "predictions_table_arn" {
  value = module.dynamodb_registry.predictions_table_arn
}

output "monitoring_snapshots_table_name" {
  value = module.dynamodb_registry.monitoring_snapshots_table_name
}

output "approval_requests_table_name" {
  value = module.dynamodb_registry.approval_requests_table_name
}

output "review_queue_table_name" {
  value = module.dynamodb_registry.review_queue_table_name
}

output "weekly_reports_table_name" {
  value = module.dynamodb_registry.weekly_reports_table_name
}

output "all_dynamodb_table_arns" {
  description = "All registry table ARNs — useful for IAM policy attachment in runtime stack."
  value       = module.dynamodb_registry.all_table_arns
}

output "route53_zone_id" {
  description = "Route53 hosted zone ID for custom domains."
  value       = var.domain_name != "" ? module.route53[0].zone_id : ""
}

output "route53_name_servers" {
  description = "Set as nameservers at your domain registrar."
  value       = var.domain_name != "" ? module.route53[0].name_servers : []
}

output "domain_name" {
  value = var.domain_name
}
