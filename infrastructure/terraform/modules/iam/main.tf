data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "lambda_execution" {
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

  statement {
    sid    = "ArtifactsBucket"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket",
    ]
    resources = [
      var.artifacts_bucket_arn,
      "${var.artifacts_bucket_arn}/*",
    ]
  }

  statement {
    sid    = "StartRetrainWorkflow"
    effect = "Allow"
    actions = [
      "states:StartExecution",
    ]
    resources = [
      "arn:aws:states:${var.aws_region}:*:stateMachine:${var.project_name}-${var.environment}-*",
    ]
  }
}

resource "aws_iam_role" "lambda" {
  name               = "${var.project_name}-${var.environment}-lambda"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy" "lambda_execution" {
  name   = "${var.project_name}-${var.environment}-lambda-execution"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.lambda_execution.json
}

data "aws_iam_policy_document" "step_functions_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "step_functions_execution" {
  statement {
    sid    = "InvokeLambda"
    effect = "Allow"
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "SageMakerJobs"
    effect = "Allow"
    actions = [
      "sagemaker:CreateTrainingJob",
      "sagemaker:DescribeTrainingJob",
      "sagemaker:CreateModel",
      "sagemaker:CreateEndpointConfig",
      "sagemaker:UpdateEndpoint",
      "sagemaker:DescribeEndpoint",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "ArtifactsBucket"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket",
    ]
    resources = [
      var.artifacts_bucket_arn,
      "${var.artifacts_bucket_arn}/*",
    ]
  }
}

resource "aws_iam_role" "step_functions" {
  name               = "${var.project_name}-${var.environment}-sfn"
  assume_role_policy = data.aws_iam_policy_document.step_functions_assume_role.json
}

resource "aws_iam_role_policy" "step_functions_execution" {
  name   = "${var.project_name}-${var.environment}-sfn-execution"
  role   = aws_iam_role.step_functions.id
  policy = data.aws_iam_policy_document.step_functions_execution.json
}
