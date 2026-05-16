variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "artifacts_bucket_name" {
  type = string
}

variable "instance_type" {
  type    = string
  default = "ml.m5.large"
}

variable "enable_endpoint" {
  description = "When false, only IAM role + model artifact path are scaffolded."
  type        = bool
  default     = false
}
