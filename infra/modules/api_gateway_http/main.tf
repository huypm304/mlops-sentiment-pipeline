locals {
  api_name = "${var.project}-${var.environment}-api"

  # Route → Lambda integration mapping
  routes = {
    health = {
      route_key     = "GET /health"
      invoke_arn    = var.predict_lambda_invoke_arn
      function_name = var.predict_lambda_function_name
    }
    model_info = {
      route_key     = "GET /model-info"
      invoke_arn    = var.predict_lambda_invoke_arn
      function_name = var.predict_lambda_function_name
    }
    predict = {
      route_key     = "POST /predict"
      invoke_arn    = var.predict_lambda_invoke_arn
      function_name = var.predict_lambda_function_name
    }
    datasets_presign = {
      route_key     = "POST /datasets/presign-upload"
      invoke_arn    = var.audit_lambda_invoke_arn
      function_name = var.audit_lambda_function_name
    }
    dataset_audit = {
      route_key     = "POST /datasets/{dataset_id}/audit"
      invoke_arn    = var.audit_lambda_invoke_arn
      function_name = var.audit_lambda_function_name
    }
    dataset_approve = {
      route_key     = "POST /datasets/{dataset_id}/approve"
      invoke_arn    = var.audit_lambda_invoke_arn
      function_name = var.audit_lambda_function_name
    }
    datasets_list = {
      route_key     = "GET /datasets"
      invoke_arn    = var.audit_lambda_invoke_arn
      function_name = var.audit_lambda_function_name
    }
    dataset_get = {
      route_key     = "GET /datasets/{dataset_id}"
      invoke_arn    = var.audit_lambda_invoke_arn
      function_name = var.audit_lambda_function_name
    }
    dataset_delete = {
      route_key     = "DELETE /datasets/{dataset_id}"
      invoke_arn    = var.audit_lambda_invoke_arn
      function_name = var.audit_lambda_function_name
    }
    pipeline_trigger = {
      route_key     = "POST /pipeline/trigger"
      invoke_arn    = var.pipeline_lambda_invoke_arn
      function_name = var.pipeline_lambda_function_name
    }
    pipeline_run = {
      route_key     = "GET /pipeline/runs/{run_id}"
      invoke_arn    = var.pipeline_lambda_invoke_arn
      function_name = var.pipeline_lambda_function_name
    }
    pipeline_run_cancel = {
      route_key     = "POST /pipeline/runs/{run_id}/cancel"
      invoke_arn    = var.pipeline_lambda_invoke_arn
      function_name = var.pipeline_lambda_function_name
    }
    pipeline_runs_list = {
      route_key     = "GET /pipeline/runs"
      invoke_arn    = var.pipeline_lambda_invoke_arn
      function_name = var.pipeline_lambda_function_name
    }
    pipeline_training_config = {
      route_key     = "GET /pipeline/training-config"
      invoke_arn    = var.pipeline_lambda_invoke_arn
      function_name = var.pipeline_lambda_function_name
    }
    pipeline_config = {
      route_key     = "GET /pipeline/config"
      invoke_arn    = var.pipeline_lambda_invoke_arn
      function_name = var.pipeline_lambda_function_name
    }
    pipeline_approval_get = {
      route_key     = "GET /pipeline/approvals/{approval_id}"
      invoke_arn    = var.pipeline_lambda_invoke_arn
      function_name = var.pipeline_lambda_function_name
    }
    pipeline_approval_decide = {
      route_key     = "POST /pipeline/approvals/{approval_id}/decide"
      invoke_arn    = var.pipeline_lambda_invoke_arn
      function_name = var.pipeline_lambda_function_name
    }
    models_list = {
      route_key     = "GET /models"
      invoke_arn    = var.pipeline_lambda_invoke_arn
      function_name = var.pipeline_lambda_function_name
    }
    models_compare = {
      route_key     = "GET /models/compare"
      invoke_arn    = var.pipeline_lambda_invoke_arn
      function_name = var.pipeline_lambda_function_name
    }
    model_promote = {
      route_key     = "POST /models/{model_id}/promote"
      invoke_arn    = var.pipeline_lambda_invoke_arn
      function_name = var.pipeline_lambda_function_name
    }
    model_rollback = {
      route_key     = "POST /models/{model_id}/rollback"
      invoke_arn    = var.pipeline_lambda_invoke_arn
      function_name = var.pipeline_lambda_function_name
    }
    metrics_monitoring = {
      route_key     = "GET /metrics/monitoring"
      invoke_arn    = var.metrics_lambda_invoke_arn
      function_name = var.metrics_lambda_function_name
    }
    metrics_drift = {
      route_key     = "GET /metrics/drift"
      invoke_arn    = var.metrics_lambda_invoke_arn
      function_name = var.metrics_lambda_function_name
    }
    metrics_models = {
      route_key     = "GET /metrics/models"
      invoke_arn    = var.metrics_lambda_invoke_arn
      function_name = var.metrics_lambda_function_name
    }
    metrics_model_version = {
      route_key     = "GET /metrics/models/{version}"
      invoke_arn    = var.metrics_lambda_invoke_arn
      function_name = var.metrics_lambda_function_name
    }
    metrics_analytics = {
      route_key     = "GET /metrics/analytics"
      invoke_arn    = var.metrics_lambda_invoke_arn
      function_name = var.metrics_lambda_function_name
    }
    metrics_platform = {
      route_key     = "GET /metrics/platform"
      invoke_arn    = var.metrics_lambda_invoke_arn
      function_name = var.metrics_lambda_function_name
    }
    metrics_platform_context = {
      route_key     = "GET /metrics/platform/context"
      invoke_arn    = var.metrics_lambda_invoke_arn
      function_name = var.metrics_lambda_function_name
    }
    metrics_review_queue = {
      route_key     = "GET /metrics/review-queue"
      invoke_arn    = var.metrics_lambda_invoke_arn
      function_name = var.metrics_lambda_function_name
    }
    metrics_runtime = {
      route_key     = "GET /metrics/runtime"
      invoke_arn    = var.metrics_lambda_invoke_arn
      function_name = var.metrics_lambda_function_name
    }
    metrics_training_history = {
      route_key     = "GET /metrics/training/history"
      invoke_arn    = var.metrics_lambda_invoke_arn
      function_name = var.metrics_lambda_function_name
    }
    metrics_weekly_reports_list = {
      route_key     = "GET /metrics/weekly-reports"
      invoke_arn    = var.metrics_lambda_invoke_arn
      function_name = var.metrics_lambda_function_name
    }
    metrics_weekly_reports_create = {
      route_key     = "POST /metrics/weekly-reports"
      invoke_arn    = var.metrics_lambda_invoke_arn
      function_name = var.metrics_lambda_function_name
    }
    metrics_weekly_report_detail = {
      route_key     = "GET /metrics/weekly-reports/{report_id}"
      invoke_arn    = var.metrics_lambda_invoke_arn
      function_name = var.metrics_lambda_function_name
    }
    review_queue_list = {
      route_key     = "GET /review-queue"
      invoke_arn    = var.metrics_lambda_invoke_arn
      function_name = var.metrics_lambda_function_name
    }
    review_queue_submit = {
      route_key     = "POST /review-queue/{review_id}/submit"
      invoke_arn    = var.metrics_lambda_invoke_arn
      function_name = var.metrics_lambda_function_name
    }
  }
}

resource "aws_apigatewayv2_api" "http" {
  name          = local.api_name
  protocol_type = "HTTP"

  cors_configuration {
    allow_headers  = ["content-type", "authorization", "x-amz-date", "x-api-key"]
    allow_methods  = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_origins  = var.cors_allow_origins
    expose_headers = ["x-request-id"]
    max_age        = 86400
  }

  tags = merge(var.common_tags, { Name = local.api_name })
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/aws/apigateway/${local.api_name}"
  retention_in_days = var.log_retention_days
  tags              = var.common_tags
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api.arn
    format = jsonencode({
      requestId          = "$context.requestId"
      ip                 = "$context.identity.sourceIp"
      routeKey           = "$context.routeKey"
      status             = "$context.status"
      responseLength     = "$context.responseLength"
      integrationLatency = "$context.integrationLatency"
    })
  }

  tags = var.common_tags
}

resource "aws_apigatewayv2_integration" "lambda" {
  for_each = local.routes

  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = each.value.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "lambda" {
  for_each = local.routes

  api_id    = aws_apigatewayv2_api.http.id
  route_key = each.value.route_key
  target    = "integrations/${aws_apigatewayv2_integration.lambda[each.key].id}"
}

resource "aws_lambda_permission" "api_gateway" {
  for_each = local.routes

  statement_id  = "AllowAPIGW-${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = each.value.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}

# ---------------------------------------------------------------------------
# Optional custom domain
# ---------------------------------------------------------------------------

resource "aws_apigatewayv2_domain_name" "api" {
  count = var.custom_domain_name != "" ? 1 : 0

  domain_name = var.custom_domain_name
  domain_name_configuration {
    certificate_arn = var.certificate_arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }

  tags = var.common_tags
}

resource "aws_apigatewayv2_api_mapping" "api" {
  count = var.custom_domain_name != "" ? 1 : 0

  api_id      = aws_apigatewayv2_api.http.id
  domain_name = aws_apigatewayv2_domain_name.api[0].id
  stage       = aws_apigatewayv2_stage.default.name
}
