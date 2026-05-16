variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "cors_allow_origins" {
  type = list(string)
}

variable "predict_lambda_invoke_arn" {
  type = string
}

variable "predict_lambda_function_name" {
  type = string
}

variable "analytics_lambda_invoke_arn" {
  type = string
}

variable "analytics_lambda_function_name" {
  type = string
}

variable "audit_lambda_invoke_arn" {
  type = string
}

variable "audit_lambda_function_name" {
  type = string
}

variable "retrain_trigger_lambda_invoke_arn" {
  type = string
}

variable "retrain_trigger_lambda_function_name" {
  type = string
}

variable "custom_domain_name" {
  description = "Custom domain FQDN (e.g. api.minhhuy.me). Empty disables custom domain."
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "ACM certificate ARN (must be in the same region as the API)."
  type        = string
  default     = ""
}
