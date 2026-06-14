variable "project" {
  type    = string
  default = "absa-mlops"
}

variable "environment" {
  type    = string
  default = "demo"
}

variable "artifact_bucket_name" {
  description = "Name of the S3 artifact bucket."
  type        = string
}

variable "sagemaker_execution_role_arn" {
  description = "ARN of the SageMaker execution role (from iam_runtime module)."
  type        = string
}

variable "enable_endpoint" {
  description = "Create a real SageMaker inference endpoint. Incurs cost — keep false for demos."
  type        = bool
  default     = false
}

variable "instance_type" {
  description = "SageMaker inference instance type."
  type        = string
  default     = "ml.m5.large"
}

variable "model_s3_key" {
  description = "S3 object key for the SageMaker model.tar.gz artifact."
  type        = string
  default     = "models/production/model.tar.gz"
}

variable "inference_image" {
  description = "ECR or public Docker image URI for SageMaker serving. Leave empty to use default PyTorch inference image."
  type        = string
  default     = ""
}

variable "model_package_version" {
  description = "Bump when model.tar.gz changes to force a new SageMaker model + endpoint config."
  type        = string
  default     = "v2"
}

variable "aws_region" {
  type    = string
  default = "ap-southeast-1"
}

variable "common_tags" {
  type    = map(string)
  default = {}
}

locals {
  name_prefix   = "${var.project}-${var.environment}"
  endpoint_name = "${local.name_prefix}-endpoint"
  model_name    = "${local.name_prefix}-absa-${var.model_package_version}"
  model_s3_uri  = "s3://${var.artifact_bucket_name}/${var.model_s3_key}"

  # ap-southeast-1 DLC tag is 2.1.0-cpu-py310 (py311 tag does not exist for 2.1.0).
  default_pytorch_inference_image = "763104351884.dkr.ecr.${var.aws_region}.amazonaws.com/pytorch-inference:2.1.0-cpu-py310"
  inference_image                 = var.inference_image != "" ? var.inference_image : local.default_pytorch_inference_image
}

# Endpoint resources are conditionally created via count.
# When enable_endpoint = false, only the local values are scaffolded so
# callers can still reference endpoint_name for configuration purposes.

resource "aws_sagemaker_model" "absa" {
  count = var.enable_endpoint ? 1 : 0

  name               = local.model_name
  execution_role_arn = var.sagemaker_execution_role_arn

  primary_container {
    image          = local.inference_image
    model_data_url = local.model_s3_uri
    environment = {
      SAGEMAKER_PROGRAM = "inference.py"
    }
  }

  tags = merge(var.common_tags, { Name = local.model_name })
}

resource "aws_sagemaker_endpoint_configuration" "absa" {
  count = var.enable_endpoint ? 1 : 0

  name = "${local.model_name}-config"

  production_variants {
    variant_name           = "primary"
    model_name             = aws_sagemaker_model.absa[0].name
    initial_instance_count = 1
    instance_type          = var.instance_type
  }

  tags = merge(var.common_tags, { Name = "${local.model_name}-config" })
}

resource "aws_sagemaker_endpoint" "absa" {
  count = var.enable_endpoint ? 1 : 0

  name                 = local.endpoint_name
  endpoint_config_name = aws_sagemaker_endpoint_configuration.absa[0].name

  tags = merge(var.common_tags, { Name = local.endpoint_name })
}
