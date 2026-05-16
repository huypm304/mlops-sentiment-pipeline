variable "aws_region" {
  type    = string
  default = "ap-southeast-1"
}

variable "project_name" {
  type    = string
  default = "absa-mlops-platform"
}

variable "lambda_memory_mb" {
  type    = number
  default = 1024
}

variable "lambda_timeout_seconds" {
  type    = number
  default = 60
}

variable "enable_sagemaker_endpoint" {
  type    = bool
  default = false
}

variable "sagemaker_instance_type" {
  type    = string
  default = "ml.m5.large"
}

variable "cors_allow_origins" {
  type = list(string)
  default = [
    "https://minhhuy.me",
    "https://www.minhhuy.me",
  ]
}

variable "domain_name" {
  type    = string
  default = "minhhuy.me"
}

variable "enable_custom_domain" {
  type    = bool
  default = true
}

variable "create_hosted_zone" {
  description = "false — reuse hosted zone created by dev apply."
  type        = bool
  default     = false
}

variable "route53_zone_id" {
  type    = string
  default = ""
}

variable "api_subdomain" {
  description = "Prod API host: api.minhhuy.me"
  type        = string
  default     = "api"
}

variable "www_cname_target" {
  type    = string
  default = ""
}
