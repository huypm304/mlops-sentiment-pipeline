output "api_log_group_name" {
  value = try(aws_cloudwatch_log_group.api_gateway[0].name, "")
}

output "lambda_error_alarm_names" {
  value = [for k, v in aws_cloudwatch_metric_alarm.lambda_errors : v.alarm_name]
}
