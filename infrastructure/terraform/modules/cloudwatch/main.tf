resource "aws_cloudwatch_log_group" "api_gateway" {
  count = var.api_gateway_name != "" ? 1 : 0

  name              = "/aws/apigateway/${var.project_name}-${var.environment}"
  retention_in_days = 14
}

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each = toset(var.lambda_function_names)

  alarm_name          = "${each.value}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 1
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = each.value
  }

  alarm_description = "Lambda error count for ${each.value}"
}
