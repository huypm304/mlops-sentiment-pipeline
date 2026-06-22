output "api_log_group_name" {
  value = length(aws_cloudwatch_log_group.api_gateway) > 0 ? aws_cloudwatch_log_group.api_gateway[0].name : ""
}

output "lambda_error_alarm_names" {
  value = [for k, v in aws_cloudwatch_metric_alarm.lambda_errors : v.alarm_name]
}

output "api_5xx_alarm_name" {
  value = length(aws_cloudwatch_metric_alarm.api_5xx) > 0 ? aws_cloudwatch_metric_alarm.api_5xx[0].alarm_name : ""
}

output "sfn_failed_alarm_name" {
  value = length(aws_cloudwatch_metric_alarm.sfn_failed) > 0 ? aws_cloudwatch_metric_alarm.sfn_failed[0].alarm_name : ""
}

output "dashboard_name" {
  value = aws_cloudwatch_dashboard.main.dashboard_name
}

output "dashboard_url" {
  description = "Direct link to the CloudWatch dashboard."
  value       = "https://console.aws.amazon.com/cloudwatch/home#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}
