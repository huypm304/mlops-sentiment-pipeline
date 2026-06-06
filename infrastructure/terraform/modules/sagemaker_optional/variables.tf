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

variable "aws_region" {
  type    = string
  default = "ap-southeast-1"
}

variable "common_tags" {
  type    = map(string)
  default = {}
}
