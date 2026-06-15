variable "aws_region" {
  type    = string
  default = "ap-southeast-1"
}

variable "project" {
  type    = string
  default = "absa-mlops"
}

variable "environment" {
  type    = string
  default = "demo"
}

variable "owner" {
  type    = string
  default = "minh-huy"
}

variable "domain_name" {
  description = "Root domain for Route53 hosted zone (empty = skip DNS)."
  type        = string
  default     = ""
}

variable "create_hosted_zone" {
  description = "Create a Route53 hosted zone for domain_name."
  type        = bool
  default     = true
}
