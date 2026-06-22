locals {
  name_prefix = "${var.project}-${var.environment}"
}

# ---------------------------------------------------------------------------
# Monitoring snapshot schedule
# Triggers metrics Lambda periodically to compute drift and quality snapshots.
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_event_rule" "monitoring_snapshot" {
  count = var.enable_monitoring_schedule ? 1 : 0

  name                = "${local.name_prefix}-monitoring-snapshot"
  description         = "Periodic trigger for ABSA monitoring snapshot computation."
  schedule_expression = var.monitoring_schedule_expression
  state               = "ENABLED"

  tags = merge(var.common_tags, { Name = "${local.name_prefix}-monitoring-snapshot" })
}

resource "aws_cloudwatch_event_target" "monitoring_snapshot" {
  count = var.enable_monitoring_schedule ? 1 : 0

  rule      = aws_cloudwatch_event_rule.monitoring_snapshot[0].name
  target_id = "metrics-lambda"
  arn       = var.metrics_lambda_arn

  input = jsonencode({
    action = "compute_snapshot"
    source = "eventbridge-schedule"
  })
}

resource "aws_lambda_permission" "monitoring_snapshot" {
  count = var.enable_monitoring_schedule ? 1 : 0

  statement_id  = "AllowEventBridgeMonitoringSnapshot"
  action        = "lambda:InvokeFunction"
  function_name = var.metrics_lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.monitoring_snapshot[0].arn
}

# ---------------------------------------------------------------------------
# Retrain recommendation check
# Triggers metrics Lambda daily to evaluate if retraining should be recommended.
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_event_rule" "retrain_check" {
  name                = "${local.name_prefix}-retrain-check"
  description         = "Daily check for drift-based retrain recommendations."
  schedule_expression = "rate(24 hours)"
  state               = "ENABLED"

  tags = merge(var.common_tags, { Name = "${local.name_prefix}-retrain-check" })
}

resource "aws_cloudwatch_event_target" "retrain_check" {
  rule      = aws_cloudwatch_event_rule.retrain_check.name
  target_id = "metrics-lambda"
  arn       = var.metrics_lambda_arn

  input = jsonencode({
    action = "check_retrain_recommendation"
    source = "eventbridge-schedule"
  })
}

resource "aws_lambda_permission" "retrain_check" {
  statement_id  = "AllowEventBridgeRetrainCheck"
  action        = "lambda:InvokeFunction"
  function_name = var.metrics_lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.retrain_check.arn
}
