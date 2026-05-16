data "aws_caller_identity" "current" {}

locals {
  name_prefix    = "${var.project_name}-${var.environment}"
  lambda_root    = "${path.module}/../../lambda"
  asl_definition = "${path.module}/../step-functions/retrain-pipeline.asl.json"

  # Deterministic ARN avoids circular dependency with step_functions module.
  retrain_state_machine_arn = "arn:aws:states:${var.aws_region}:${data.aws_caller_identity.current.account_id}:stateMachine:${var.project_name}-${var.environment}-retrain"

  custom_domain_enabled = var.domain_name != "" && var.enable_custom_domain
  api_fqdn                = local.custom_domain_enabled ? "${var.api_subdomain}.${var.domain_name}" : ""

  cors_origins = distinct(concat(
    var.cors_allow_origins,
    local.custom_domain_enabled ? [
      "https://${var.domain_name}",
      "https://www.${var.domain_name}",
      "https://${local.api_fqdn}",
    ] : [],
  ))
}

module "s3" {
  source = "./modules/s3"

  project_name = var.project_name
  environment  = var.environment
}

module "iam" {
  source = "./modules/iam"

  project_name         = var.project_name
  environment          = var.environment
  artifacts_bucket_arn = module.s3.bucket_arn
  aws_region           = var.aws_region
}

locals {
  lambda_env = {
    ARTIFACTS_BUCKET = module.s3.bucket_id
    ENVIRONMENT      = var.environment
    PROJECT_NAME     = var.project_name
  }
}

module "lambda_predict" {
  source = "./modules/lambda"

  project_name = var.project_name
  environment  = var.environment
  function_name = "predict"
  role_arn      = module.iam.lambda_role_arn
  source_path   = "${local.lambda_root}/predict"
  runtime       = var.lambda_runtime
  memory_size   = var.lambda_memory_mb
  timeout       = var.lambda_timeout_seconds

  environment_variables = merge(local.lambda_env, {
    SAGEMAKER_ENDPOINT_NAME = module.sagemaker.endpoint_name
  })
}

module "lambda_analytics" {
  source = "./modules/lambda"

  project_name  = var.project_name
  environment   = var.environment
  function_name = "analytics"
  role_arn      = module.iam.lambda_role_arn
  source_path   = "${local.lambda_root}/analytics"
  runtime       = var.lambda_runtime
  memory_size   = 256
  timeout       = 15

  environment_variables = local.lambda_env
}

module "lambda_audit" {
  source = "./modules/lambda"

  project_name  = var.project_name
  environment   = var.environment
  function_name = "audit"
  role_arn      = module.iam.lambda_role_arn
  source_path   = "${local.lambda_root}/audit"
  runtime       = var.lambda_runtime
  memory_size   = 512
  timeout       = 60

  environment_variables = local.lambda_env
}

module "lambda_retrain_trigger" {
  source = "./modules/lambda"

  project_name  = var.project_name
  environment   = var.environment
  function_name = "retrain-trigger"
  role_arn      = module.iam.lambda_role_arn
  source_path   = "${local.lambda_root}/retrain_trigger"
  runtime       = var.lambda_runtime
  memory_size   = 256
  timeout       = 15

  environment_variables = merge(local.lambda_env, {
    RETRAIN_STATE_MACHINE_ARN = local.retrain_state_machine_arn
  })
}

module "sagemaker" {
  source = "./modules/sagemaker"

  project_name          = var.project_name
  environment           = var.environment
  artifacts_bucket_name = module.s3.bucket_id
  instance_type         = var.sagemaker_instance_type
  enable_endpoint       = var.enable_sagemaker_endpoint
}

module "step_functions" {
  source = "./modules/step_functions"

  project_name          = var.project_name
  environment           = var.environment
  role_arn              = module.iam.step_functions_role_arn
  definition_file       = local.asl_definition
  artifacts_bucket_name = module.s3.bucket_id

  lambda_function_arns = {
    audit = module.lambda_audit.function_arn
  }
}

module "route53" {
  count  = local.custom_domain_enabled ? 1 : 0
  source = "./modules/route53"

  domain_name        = var.domain_name
  create_hosted_zone = var.create_hosted_zone
  zone_id            = var.route53_zone_id
  www_cname_target   = var.www_cname_target
}

module "acm" {
  count  = local.custom_domain_enabled ? 1 : 0
  source = "./modules/acm"

  domain_name = local.api_fqdn
  zone_id     = module.route53[0].zone_id
}

module "api_gateway" {
  source = "./modules/api_gateway"

  project_name       = var.project_name
  environment        = var.environment
  cors_allow_origins = local.cors_origins

  custom_domain_name = local.custom_domain_enabled ? local.api_fqdn : ""
  certificate_arn    = local.custom_domain_enabled ? module.acm[0].certificate_arn : ""

  predict_lambda_invoke_arn            = module.lambda_predict.invoke_arn
  predict_lambda_function_name         = module.lambda_predict.function_name
  analytics_lambda_invoke_arn          = module.lambda_analytics.invoke_arn
  analytics_lambda_function_name       = module.lambda_analytics.function_name
  audit_lambda_invoke_arn              = module.lambda_audit.invoke_arn
  audit_lambda_function_name           = module.lambda_audit.function_name
  retrain_trigger_lambda_invoke_arn    = module.lambda_retrain_trigger.invoke_arn
  retrain_trigger_lambda_function_name = module.lambda_retrain_trigger.function_name
}

resource "aws_route53_record" "api" {
  count = local.custom_domain_enabled ? 1 : 0

  zone_id = module.route53[0].zone_id
  name    = var.api_subdomain
  type    = "A"

  alias {
    name                   = module.api_gateway.custom_domain_target
    zone_id                = module.api_gateway.custom_domain_hosted_zone_id
    evaluate_target_health = false
  }
}

module "cloudwatch" {
  source = "./modules/cloudwatch"

  project_name = var.project_name
  environment  = var.environment
  api_gateway_name = "${local.name_prefix}-api"

  lambda_function_names = [
    module.lambda_predict.function_name,
    module.lambda_analytics.function_name,
    module.lambda_audit.function_name,
    module.lambda_retrain_trigger.function_name,
  ]
}
