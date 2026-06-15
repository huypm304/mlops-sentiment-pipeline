variable "project" {
  type    = string
  default = "absa-mlops"
}

variable "environment" {
  type    = string
  default = "demo"
}

variable "function_name" {
  description = "Logical function name suffix (e.g. predict, audit, pipeline-trigger)."
  type        = string
}

variable "package_type" {
  description = "Lambda package type: Zip or Image."
  type        = string
  default     = "Zip"
}

# Zip-based deployment
variable "source_path" {
  description = "Path to the Lambda source directory. Required when package_type = Zip."
  type        = string
  default     = null
}

variable "handler" {
  type    = string
  default = "handler.lambda_handler"
}

variable "runtime" {
  type    = string
  default = "python3.12"
}

# Image-based deployment
variable "image_uri" {
  description = "ECR image URI. Required when package_type = Image."
  type        = string
  default     = null
}

variable "memory_size" {
  type    = number
  default = 512
}

variable "timeout" {
  type    = number
  default = 30
}

variable "role_arn" {
  type = string
}

variable "environment_variables" {
  type    = map(string)
  default = {}
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days."
  type        = number
  default     = 14
}

variable "common_tags" {
  type    = map(string)
  default = {}
}
