variable "project" {
  type    = string
  default = "absa-mlops"
}

variable "environment" {
  type    = string
  default = "demo"
}

variable "aws_region" {
  type    = string
  default = "ap-southeast-1"
}

variable "artifact_bucket_arn" {
  description = "ARN of the core artifact S3 bucket."
  type        = string
}

variable "dynamodb_table_arns" {
  description = "List of DynamoDB table ARNs the Lambda role may read/write."
  type        = list(string)
  default     = []
}

variable "weekly_reports_table_arn" {
  description = "ARN of the weekly-reports DynamoDB table (optional separate grant)."
  type        = string
  default     = ""
}

variable "common_tags" {
  type    = map(string)
  default = {}
}
