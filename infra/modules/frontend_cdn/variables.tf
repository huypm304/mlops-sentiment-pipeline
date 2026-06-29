variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "domain_name" {
  type = string
}

variable "aliases" {
  description = "CloudFront alternate domain names (must match ACM cert)."
  type        = list(string)
}

variable "certificate_arn" {
  description = "ACM certificate ARN in us-east-1 for CloudFront."
  type        = string
}

variable "zone_id" {
  description = "Route53 zone ID for apex/www alias records."
  type        = string
  default     = ""
}

variable "common_tags" {
  type    = map(string)
  default = {}
}
