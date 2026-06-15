output "monitoring_rule_arn" {
  value = var.enable_monitoring_schedule ? aws_cloudwatch_event_rule.monitoring_snapshot[0].arn : ""
}

output "retrain_check_rule_arn" {
  value = aws_cloudwatch_event_rule.retrain_check.arn
}
