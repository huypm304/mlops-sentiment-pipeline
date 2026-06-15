locals {
  name_prefix   = "${var.project}-${var.environment}"
  endpoint_name = "${local.name_prefix}-endpoint"
  model_name    = "${local.name_prefix}-absa"
  model_s3_uri  = "s3://${var.artifact_bucket_name}/${var.model_s3_key}"

  # ap-southeast-1 DLC tag is 2.1.0-cpu-py310 (py311 tag does not exist for 2.1.0).
  inference_image = var.inference_image != "" ? var.inference_image : (
    "763104351884.dkr.ecr.${var.aws_region}.amazonaws.com/pytorch-inference:${var.pytorch_inference_version}-cpu-${var.pytorch_inference_py_version}"
  )
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
      SAGEMAKER_PROGRAM    = "inference.py"
      SAGEMAKER_SUBMIT_DIR = "/opt/ml/code"
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
