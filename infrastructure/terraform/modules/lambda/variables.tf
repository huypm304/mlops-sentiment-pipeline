variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "function_name" {
  description = "Logical function name suffix (predict, audit, etc.)."
  type        = string
}

variable "handler" {
  type    = string
  default = "handler.lambda_handler"
}

variable "runtime" {
  type    = string
  default = "python3.11"
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

variable "source_path" {
  description = "Path to Lambda source directory (handler.py + requirements)."
  type        = string
}

variable "environment_variables" {
  type    = map(string)
  default = {}
}

variable "log_group_name" {
  description = "CloudWatch log group name for this function."
  type        = string
  default     = ""
}
