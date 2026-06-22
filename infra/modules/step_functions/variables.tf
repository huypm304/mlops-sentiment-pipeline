variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "role_arn" {
  type = string
}

variable "definition_file" {
  description = "Path to ASL JSON definition file."
  type        = string
}

variable "lambda_function_arns" {
  description = "Map of logical step names to Lambda ARNs. Recognised keys: audit, pipeline, retrain_trigger."
  type        = map(string)
  default     = {}
}

variable "artifacts_bucket_name" {
  type = string
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days for the Step Functions log group."
  type        = number
  default     = 14
}
