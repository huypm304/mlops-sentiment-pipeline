variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "lambda_function_names" {
  description = "Lambda function names to attach basic error alarms."
  type        = list(string)
  default     = []
}

variable "api_gateway_name" {
  type    = string
  default = ""
}
