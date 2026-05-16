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
  description = "Path to ASL JSON definition."
  type        = string
}

variable "lambda_function_arns" {
  description = "Map of logical step names to Lambda ARNs for template substitution."
  type        = map(string)
  default     = {}
}

variable "artifacts_bucket_name" {
  type = string
}
