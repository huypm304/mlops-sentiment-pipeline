resource "aws_apigatewayv2_api" "http" {
  name          = "${var.project_name}-${var.environment}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_headers = ["content-type", "authorization"]
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_origins = var.cors_allow_origins
  }
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = "$default"
  auto_deploy = true
}

locals {
  routes = {
    predict = {
      route_key = "POST /predict"
      lambda    = var.predict_lambda_invoke_arn
      name      = var.predict_lambda_function_name
    }
    health = {
      route_key = "GET /health"
      lambda    = var.predict_lambda_invoke_arn
      name      = var.predict_lambda_function_name
    }
    analytics = {
      route_key = "GET /analytics/summary"
      lambda    = var.analytics_lambda_invoke_arn
      name      = var.analytics_lambda_function_name
    }
    audit = {
      route_key = "POST /audit"
      lambda    = var.audit_lambda_invoke_arn
      name      = var.audit_lambda_function_name
    }
    retrain = {
      route_key = "POST /retrain"
      lambda    = var.retrain_trigger_lambda_invoke_arn
      name      = var.retrain_trigger_lambda_function_name
    }
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  for_each = local.routes

  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = each.value.lambda
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

  statement_id  = "AllowAPIGatewayInvoke-${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = each.value.name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}

resource "aws_apigatewayv2_domain_name" "api" {
  count = var.custom_domain_name != "" ? 1 : 0

  domain_name = var.custom_domain_name

  domain_name_configuration {
    certificate_arn = var.certificate_arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }
}

resource "aws_apigatewayv2_api_mapping" "api" {
  count = var.custom_domain_name != "" ? 1 : 0

  api_id      = aws_apigatewayv2_api.http.id
  domain_name = aws_apigatewayv2_domain_name.api[0].id
  stage       = aws_apigatewayv2_stage.default.name
}
