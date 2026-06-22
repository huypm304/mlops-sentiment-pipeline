variable "project" {
  type    = string
  default = "absa-mlops"
}

variable "environment" {
  type    = string
  default = "demo"
}

variable "metrics_lambda_arn" {
  description = "ARN of the metrics/monitoring Lambda function."
  type        = string
}

variable "metrics_lambda_function_name" {
  description = "Name of the metrics/monitoring Lambda function (for permissions)."
  type        = string
}

variable "enable_monitoring_schedule" {
  description = "Create EventBridge rule to periodically trigger monitoring snapshots."
  type        = bool
  default     = true
}

variable "monitoring_schedule_expression" {
  description = "EventBridge schedule expression for monitoring snapshots (cron or rate)."
  type        = string
  default     = "rate(1 hour)"
}

variable "common_tags" {
  type    = map(string)
  default = {}
}
