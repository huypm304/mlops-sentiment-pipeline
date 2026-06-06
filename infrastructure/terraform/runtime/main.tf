data "aws_caller_identity" "current" {}

locals {
  name_prefix = "${var.project}-${var.environment}"
  lambda_root = "${path.module}/../../../lambda"

  # Deterministic state machine ARN avoids circular dependency between
  # lambda_pipeline (needs STATE_MACHINE_ARN env var) and step_functions
  # (needs lambda_pipeline ARN for the ASL template).
  state_machine_arn = "arn:aws:states:${var.aws_region}:${data.aws_caller_identity.current.account_id}:stateMachine:${local.name_prefix}-retrain"

  common_tags = {
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    ManagedBy   = "terraform"
    CostCenter  = "student-demo"
    Stack       = "runtime"
  }

  # ---------------------------------------------------------------------------
  # Core resource references: prefer direct variable injection;
  # fall back to remote state when variables are empty.
  # ---------------------------------------------------------------------------
  use_remote_state = var.core_state_bucket != "" && var.artifact_bucket_name == ""

  artifact_bucket_name = local.use_remote_state ? data.terraform_remote_state.core[0].outputs.artifact_bucket_name : var.artifact_bucket_name
  artifact_bucket_arn  = local.use_remote_state ? data.terraform_remote_state.core[0].outputs.artifact_bucket_arn : var.artifact_bucket_arn
  dynamodb_table_arns  = local.use_remote_state ? data.terraform_remote_state.core[0].outputs.all_dynamodb_table_arns : var.dynamodb_table_arns

  datasets_table_name             = local.use_remote_state ? data.terraform_remote_state.core[0].outputs.datasets_table_name : var.datasets_table_name
  training_runs_table_name        = local.use_remote_state ? data.terraform_remote_state.core[0].outputs.training_runs_table_name : var.training_runs_table_name
  models_table_name               = local.use_remote_state ? data.terraform_remote_state.core[0].outputs.models_table_name : var.models_table_name
  predictions_table_name          = local.use_remote_state ? data.terraform_remote_state.core[0].outputs.predictions_table_name : var.predictions_table_name
  monitoring_snapshots_table_name = local.use_remote_state ? data.terraform_remote_state.core[0].outputs.monitoring_snapshots_table_name : var.monitoring_snapshots_table_name
  approval_requests_table_name    = local.use_remote_state ? data.terraform_remote_state.core[0].outputs.approval_requests_table_name : var.approval_requests_table_name
  review_queue_table_name         = local.use_remote_state ? data.terraform_remote_state.core[0].outputs.review_queue_table_name : var.review_queue_table_name

  # Custom domain assembly
  custom_domain_enabled = var.domain_name != "" && var.enable_custom_domain
  api_fqdn              = local.custom_domain_enabled ? "${var.api_subdomain}.${var.domain_name}" : ""

  # Full CORS origins including custom domain if enabled
  cors_origins = distinct(concat(
    var.cors_allow_origins,
    local.custom_domain_enabled ? [
      "https://${var.domain_name}",
      "https://www.${var.domain_name}",
      "https://${local.api_fqdn}",
    ] : [],
  ))

  # Common Lambda environment variables
  lambda_env = {
    PROJECT             = var.project
    ENVIRONMENT         = var.environment
    ARTIFACTS_BUCKET    = local.artifact_bucket_name
    DATASETS_TABLE      = local.datasets_table_name
    TRAINING_RUNS_TABLE = local.training_runs_table_name
    MODELS_TABLE        = local.models_table_name
    PREDICTIONS_TABLE   = local.predictions_table_name
    MONITORING_TABLE    = local.monitoring_snapshots_table_name
    APPROVAL_TABLE      = local.approval_requests_table_name
    REVIEW_QUEUE_TABLE  = local.review_queue_table_name
  }
}

# ---------------------------------------------------------------------------
# Optional: read core outputs from Terraform remote state
# ---------------------------------------------------------------------------

data "terraform_remote_state" "core" {
  count = local.use_remote_state ? 1 : 0

  backend = "s3"
  config = {
    bucket = var.core_state_bucket
    key    = var.core_state_key
    region = var.aws_region
  }
}

# ---------------------------------------------------------------------------
# IAM — runtime roles for Lambda, Step Functions, SageMaker
# ---------------------------------------------------------------------------

module "iam_runtime" {
  source = "../modules/iam_runtime"

  project             = var.project
  environment         = var.environment
  aws_region          = var.aws_region
  artifact_bucket_arn = local.artifact_bucket_arn
  dynamodb_table_arns = local.dynamodb_table_arns
  common_tags         = local.common_tags
}

# ---------------------------------------------------------------------------
# Lambda functions
# ---------------------------------------------------------------------------

module "lambda_predict" {
  source = "../modules/lambda_function"

  project            = var.project
  environment        = var.environment
  function_name      = "predict"
  role_arn           = module.iam_runtime.lambda_role_arn
  source_path        = "${local.lambda_root}/predict"
  runtime            = var.lambda_runtime
  memory_size        = var.lambda_memory_mb
  timeout            = var.lambda_timeout_seconds
  log_retention_days = var.log_retention_days
  common_tags        = local.common_tags

  environment_variables = merge(local.lambda_env, {
    SAGEMAKER_ENDPOINT_NAME   = module.sagemaker_optional.endpoint_name
    ENABLE_SAGEMAKER_ENDPOINT = tostring(var.enable_sagemaker_endpoint)
  })
}

module "lambda_audit" {
  source = "../modules/lambda_function"

  project            = var.project
  environment        = var.environment
  function_name      = "audit"
  role_arn           = module.iam_runtime.lambda_role_arn
  source_path        = "${local.lambda_root}/audit"
  runtime            = var.lambda_runtime
  memory_size        = 512
  timeout            = 120
  log_retention_days = var.log_retention_days
  common_tags        = local.common_tags

  environment_variables = local.lambda_env
}

module "lambda_pipeline" {
  source = "../modules/lambda_function"

  project            = var.project
  environment        = var.environment
  function_name      = "pipeline"
  role_arn           = module.iam_runtime.lambda_role_arn
  source_path        = "${local.lambda_root}/pipeline"
  runtime            = var.lambda_runtime
  memory_size        = 512
  timeout            = 60
  log_retention_days = var.log_retention_days
  common_tags        = local.common_tags

  environment_variables = merge(local.lambda_env, {
    STATE_MACHINE_ARN         = local.state_machine_arn
    ENABLE_SAGEMAKER_TRAINING = tostring(var.enable_sagemaker_training)
    SAGEMAKER_ROLE_ARN        = module.iam_runtime.sagemaker_role_arn
  })
}

module "lambda_metrics" {
  source = "../modules/lambda_function"

  project            = var.project
  environment        = var.environment
  function_name      = "metrics"
  role_arn           = module.iam_runtime.lambda_role_arn
  source_path        = "${local.lambda_root}/metrics"
  runtime            = var.lambda_runtime
  memory_size        = 256
  timeout            = 30
  log_retention_days = var.log_retention_days
  common_tags        = local.common_tags

  environment_variables = local.lambda_env
}

# ---------------------------------------------------------------------------
# API Gateway HTTP API
# ---------------------------------------------------------------------------

module "api_gateway" {
  source = "../modules/api_gateway_http"

  project     = var.project
  environment = var.environment

  cors_allow_origins = local.cors_origins

  predict_lambda_invoke_arn    = module.lambda_predict.invoke_arn
  predict_lambda_function_name = module.lambda_predict.function_name

  audit_lambda_invoke_arn    = module.lambda_audit.invoke_arn
  audit_lambda_function_name = module.lambda_audit.function_name

  pipeline_lambda_invoke_arn    = module.lambda_pipeline.invoke_arn
  pipeline_lambda_function_name = module.lambda_pipeline.function_name

  metrics_lambda_invoke_arn    = module.lambda_metrics.invoke_arn
  metrics_lambda_function_name = module.lambda_metrics.function_name

  custom_domain_name = local.api_fqdn
  certificate_arn    = local.custom_domain_enabled ? module.acm[0].certificate_arn : ""
  log_retention_days = var.log_retention_days
  common_tags        = local.common_tags
}

# ---------------------------------------------------------------------------
# Step Functions — training pipeline
# ---------------------------------------------------------------------------

module "step_functions" {
  source = "../modules/step_functions"

  project_name          = var.project
  environment           = var.environment
  role_arn              = module.iam_runtime.step_functions_role_arn
  definition_file       = "${path.module}/../modules/step_functions/training_pipeline.asl.json"
  artifacts_bucket_name = local.artifact_bucket_name
  log_retention_days    = var.log_retention_days

  lambda_function_arns = {
    audit    = module.lambda_audit.function_arn
    pipeline = module.lambda_pipeline.function_arn
  }
}

# ---------------------------------------------------------------------------
# EventBridge — monitoring and retrain recommendation schedules
# ---------------------------------------------------------------------------

module "eventbridge" {
  source = "../modules/eventbridge"

  project     = var.project
  environment = var.environment

  metrics_lambda_arn           = module.lambda_metrics.function_arn
  metrics_lambda_function_name = module.lambda_metrics.function_name

  enable_monitoring_schedule = var.enable_eventbridge_monitoring
  common_tags                = local.common_tags
}

# ---------------------------------------------------------------------------
# CloudWatch — dashboard, Lambda alarms, API 5xx, SFN failures
# ---------------------------------------------------------------------------

module "cloudwatch" {
  source = "../modules/cloudwatch"

  project_name = var.project
  environment  = var.environment

  lambda_function_names = [
    module.lambda_predict.function_name,
    module.lambda_audit.function_name,
    module.lambda_pipeline.function_name,
    module.lambda_metrics.function_name,
  ]

  api_gateway_id    = module.api_gateway.api_id
  state_machine_arn = local.state_machine_arn

  enable_api_5xx_alarm  = true
  enable_sfn_failed_alarm = true
}

# ---------------------------------------------------------------------------
# SageMaker endpoint (optional, expensive — disabled by default)
# ---------------------------------------------------------------------------

module "sagemaker_optional" {
  source = "../modules/sagemaker_optional"

  project                      = var.project
  environment                  = var.environment
  artifact_bucket_name         = local.artifact_bucket_name
  sagemaker_execution_role_arn = module.iam_runtime.sagemaker_role_arn
  enable_endpoint              = var.enable_sagemaker_endpoint
  instance_type                = var.sagemaker_instance_type
  aws_region                   = var.aws_region
  common_tags                  = local.common_tags
}

# ---------------------------------------------------------------------------
# Optional: Route53 hosted zone (shared between custom domain + ACM)
# ---------------------------------------------------------------------------

module "route53" {
  count  = local.custom_domain_enabled ? 1 : 0
  source = "../modules/route53"

  domain_name        = var.domain_name
  create_hosted_zone = var.create_hosted_zone
  zone_id            = var.route53_zone_id
  www_cname_target   = var.www_cname_target
}

module "acm" {
  count  = local.custom_domain_enabled ? 1 : 0
  source = "../modules/acm"

  domain_name = local.api_fqdn
  zone_id     = module.route53[0].zone_id
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
