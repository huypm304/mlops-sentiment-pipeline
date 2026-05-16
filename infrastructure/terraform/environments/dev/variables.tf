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
  default = 512
}

variable "lambda_timeout_seconds" {
  type    = number
  default = 30
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
    "http://localhost:3000",
    "http://127.0.0.1:3000",
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
  description = "Create Route53 zone on first apply. Set false in prod after dev created the zone."
  type        = bool
  default     = true
}

variable "route53_zone_id" {
  type    = string
  default = ""
}

variable "api_subdomain" {
  description = "Dev API host: api.dev.minhhuy.me"
  type        = string
  default     = "api.dev"
}

variable "www_cname_target" {
  description = "From Vercel → Domains (e.g. cname.vercel-dns.com). Leave empty until frontend is deployed."
  type        = string
  default     = ""
}
