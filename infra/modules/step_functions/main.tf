locals {
  name = "${var.project_name}-${var.environment}-retrain"

  definition = templatefile(var.definition_file, {
    artifacts_bucket    = var.artifacts_bucket_name
    project_name        = "${var.project_name}-${var.environment}"
    audit_lambda_arn    = lookup(var.lambda_function_arns, "audit", "")
    pipeline_lambda_arn = lookup(var.lambda_function_arns, "pipeline", lookup(var.lambda_function_arns, "retrain_trigger", ""))
  })
}

resource "aws_cloudwatch_log_group" "sfn" {
  name              = "/aws/states/${local.name}"
  retention_in_days = var.log_retention_days
}

resource "aws_sfn_state_machine" "retrain" {
  name     = local.name
  role_arn = var.role_arn
  type     = "STANDARD"

  definition = local.definition

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.sfn.arn}:*"
    include_execution_data = false
    level                  = "ERROR"
  }

  tags = {
    Workflow  = "training-pipeline"
    ManagedBy = "terraform"
  }
}
