variable "project" {
  type    = string
  default = "absa-mlops"
}

variable "environment" {
  type    = string
  default = "demo"
}

variable "cors_allow_origins" {
  type    = list(string)
  default = ["http://localhost:3000"]
}

# Lambda ARN/name pairs for each logical integration
variable "predict_lambda_invoke_arn" { type = string }
variable "predict_lambda_function_name" { type = string }

variable "audit_lambda_invoke_arn" { type = string }
variable "audit_lambda_function_name" { type = string }

variable "pipeline_lambda_invoke_arn" { type = string }
variable "pipeline_lambda_function_name" { type = string }

variable "metrics_lambda_invoke_arn" { type = string }
variable "metrics_lambda_function_name" { type = string }

# Optional custom domain
variable "custom_domain_name" {
  description = "FQDN for API (e.g. api.demo.minhhuy.me). Empty disables custom domain."
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "ACM certificate ARN. Required when custom_domain_name is set."
  type        = string
  default     = ""
}

variable "log_retention_days" {
  type    = number
  default = 14
}

variable "common_tags" {
  type    = map(string)
  default = {}
}
