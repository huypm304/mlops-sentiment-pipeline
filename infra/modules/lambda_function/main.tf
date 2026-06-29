locals {
  full_name = "${var.project}-${var.environment}-${var.function_name}"
}

# Build a zip archive when using Zip package type
data "archive_file" "lambda_zip" {
  count = var.package_type == "Zip" ? 1 : 0

  type        = "zip"
  source_dir  = var.source_path
  output_path = "${path.module}/build/${var.function_name}.zip"
}

# Log group created before the function to avoid implicit creation without retention
resource "aws_cloudwatch_log_group" "this" {
  name              = "/aws/lambda/${local.full_name}"
  retention_in_days = var.log_retention_days

  tags = merge(var.common_tags, { Function = local.full_name })
}

resource "aws_lambda_function" "this" {
  function_name = local.full_name
  role          = var.role_arn

  # Zip deployment
  filename         = var.package_type == "Zip" ? data.archive_file.lambda_zip[0].output_path : null
  source_code_hash = var.package_type == "Zip" ? data.archive_file.lambda_zip[0].output_base64sha256 : null
  handler          = var.package_type == "Zip" ? var.handler : null
  runtime          = var.package_type == "Zip" ? var.runtime : null

  # Image deployment
  image_uri    = var.package_type == "Image" ? var.image_uri : null
  package_type = var.package_type

  memory_size = var.memory_size
  timeout     = var.timeout

  environment {
    variables = var.environment_variables
  }

  tags = merge(var.common_tags, { Name = local.full_name })

  depends_on = [aws_cloudwatch_log_group.this]
}
