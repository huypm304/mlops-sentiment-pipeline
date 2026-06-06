variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "lambda_function_names" {
  description = "Lambda function names to attach error alarms and dashboard widgets."
  type        = list(string)
  default     = []
}

variable "api_gateway_name" {
  description = "API Gateway name (kept for backward compat, not used in dashboard)."
  type        = string
  default     = ""
}

variable "api_gateway_id" {
  description = "API Gateway HTTP API ID for 5xx alarm and dashboard widgets."
  type        = string
  default     = ""
}

variable "state_machine_arn" {
  description = "Step Functions state machine ARN for the failed-executions alarm and dashboard."
  type        = string
  default     = ""
}

variable "lambda_error_threshold" {
  description = "Number of Lambda errors per 5 min period before alarm fires."
  type        = number
  default     = 1
}

variable "api_5xx_threshold" {
  description = "Number of 5xx responses per 5 min period before alarm fires."
  type        = number
  default     = 5
}
