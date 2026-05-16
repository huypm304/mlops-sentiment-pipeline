locals {
  model_name     = "${var.project_name}-${var.environment}-absa"
  endpoint_name  = "${var.project_name}-${var.environment}-endpoint"
  model_s3_uri   = "s3://${var.artifacts_bucket_name}/models/latest/"
  execution_role = aws_iam_role.sagemaker.arn
}

data "aws_iam_policy_document" "sagemaker_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["sagemaker.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "sagemaker_execution" {
  statement {
    sid    = "ArtifactsBucket"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = [
      "arn:aws:s3:::${var.artifacts_bucket_name}",
      "arn:aws:s3:::${var.artifacts_bucket_name}/*",
    ]
  }

  statement {
    sid    = "CloudWatchLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["arn:aws:logs:*:*:*"]
  }
}

resource "aws_iam_role" "sagemaker" {
  name               = "${var.project_name}-${var.environment}-sagemaker"
  assume_role_policy = data.aws_iam_policy_document.sagemaker_assume_role.json
}

resource "aws_iam_role_policy" "sagemaker_execution" {
  name   = "${var.project_name}-${var.environment}-sagemaker-execution"
  role   = aws_iam_role.sagemaker.id
  policy = data.aws_iam_policy_document.sagemaker_execution.json
}

# Endpoint resources are optional for cost-aware thesis demos.
resource "aws_sagemaker_model" "absa" {
  count              = var.enable_endpoint ? 1 : 0
  name               = local.model_name
  execution_role_arn = local.execution_role

  primary_container {
    image          = "763104351884.dkr.ecr.${data.aws_region.current.name}.amazonaws.com/pytorch-inference:2.1.0-cpu-py311"
    model_data_url = local.model_s3_uri
    environment = {
      SAGEMAKER_PROGRAM = "inference.py"
    }
  }
}

data "aws_region" "current" {}

resource "aws_sagemaker_endpoint_configuration" "absa" {
  count = var.enable_endpoint ? 1 : 0
  name  = "${local.model_name}-config"

  production_variants {
    variant_name           = "primary"
    model_name             = aws_sagemaker_model.absa[0].name
    initial_instance_count = 1
    instance_type          = var.instance_type
  }
}

resource "aws_sagemaker_endpoint" "absa" {
  count                = var.enable_endpoint ? 1 : 0
  name                 = local.endpoint_name
  endpoint_config_name = aws_sagemaker_endpoint_configuration.absa[0].name
}
