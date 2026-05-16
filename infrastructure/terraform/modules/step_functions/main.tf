locals {
  definition = templatefile(var.definition_file, {
    artifacts_bucket = var.artifacts_bucket_name
    project_name     = "${var.project_name}-${var.environment}"
    audit_lambda_arn = var.lambda_function_arns["audit"]
  })
}

resource "aws_sfn_state_machine" "retrain" {
  name     = "${var.project_name}-${var.environment}-retrain"
  role_arn = var.role_arn

  definition = local.definition

  tags = {
    Workflow = "retrain-pipeline"
  }
}
