locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

# ---------------------------------------------------------------------------
# API Gateway log group (backward compat with old root module)
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "api_gateway" {
  count = var.api_gateway_name != "" ? 1 : 0

  name              = "/aws/apigateway/${var.api_gateway_name}"
  retention_in_days = 14
}

# ---------------------------------------------------------------------------
# Lambda error alarms — one per function
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each = toset(var.lambda_function_names)

  alarm_name          = "${each.value}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = var.lambda_error_threshold
  treat_missing_data  = "notBreaching"

  dimensions = { FunctionName = each.value }

  alarm_description = "Lambda error count exceeded threshold for ${each.value}"
}

# ---------------------------------------------------------------------------
# API Gateway 5xx alarm
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_metric_alarm" "api_5xx" {
  count = var.enable_api_5xx_alarm ? 1 : 0

  alarm_name          = "${local.name_prefix}-api-5xx"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "Sum"
  threshold           = var.api_5xx_threshold
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApiId = var.api_gateway_id
    Stage = "$default"
  }

  alarm_description = "API Gateway 5xx error rate exceeded threshold"
}

# ---------------------------------------------------------------------------
# Step Functions failed executions alarm
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_metric_alarm" "sfn_failed" {
  count = var.enable_sfn_failed_alarm ? 1 : 0

  alarm_name          = "${local.name_prefix}-sfn-failed"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ExecutionsFailed"
  namespace           = "AWS/States"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  treat_missing_data  = "notBreaching"

  dimensions = { StateMachineArn = var.state_machine_arn }

  alarm_description = "Step Functions training pipeline execution failed"
}

# ---------------------------------------------------------------------------
# CloudWatch dashboard
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${local.name_prefix}-overview"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "text"
        x      = 0
        y      = 0
        width  = 24
        height = 1
        properties = {
          markdown = "## ABSA MLOps Platform — ${var.environment}"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 1
        width  = 8
        height = 6
        properties = {
          title  = "Lambda Errors"
          period = 300
          stat   = "Sum"
          view   = "timeSeries"
          metrics = [
            for fn in var.lambda_function_names :
            ["AWS/Lambda", "Errors", "FunctionName", fn]
          ]
        }
      },
      {
        type   = "metric"
        x      = 8
        y      = 1
        width  = 8
        height = 6
        properties = {
          title  = "Lambda Duration (avg ms)"
          period = 300
          stat   = "Average"
          view   = "timeSeries"
          metrics = [
            for fn in var.lambda_function_names :
            ["AWS/Lambda", "Duration", "FunctionName", fn]
          ]
        }
      },
      {
        type   = "metric"
        x      = 16
        y      = 1
        width  = 8
        height = 6
        properties = {
          title  = "Lambda Invocations"
          period = 300
          stat   = "Sum"
          view   = "timeSeries"
          metrics = [
            for fn in var.lambda_function_names :
            ["AWS/Lambda", "Invocations", "FunctionName", fn]
          ]
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 7
        width  = 12
        height = 6
        properties = {
          title  = "API 4xx / 5xx"
          period = 300
          stat   = "Sum"
          view   = "timeSeries"
          metrics = var.enable_api_5xx_alarm ? [
            ["AWS/ApiGateway", "4XXError", "ApiId", var.api_gateway_id, "Stage", "$default"],
            ["AWS/ApiGateway", "5XXError", "ApiId", var.api_gateway_id, "Stage", "$default"],
          ] : []
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 7
        width  = 12
        height = 6
        properties = {
          title  = "Step Functions Executions"
          period = 300
          stat   = "Sum"
          view   = "timeSeries"
          metrics = var.enable_sfn_failed_alarm ? [
            ["AWS/States", "ExecutionsStarted", "StateMachineArn", var.state_machine_arn],
            ["AWS/States", "ExecutionsSucceeded", "StateMachineArn", var.state_machine_arn],
            ["AWS/States", "ExecutionsFailed", "StateMachineArn", var.state_machine_arn],
          ] : []
        }
      },
    ]
  })
}
