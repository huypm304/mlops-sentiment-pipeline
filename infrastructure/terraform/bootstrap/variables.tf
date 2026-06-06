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

variable "github_org" {
  description = "GitHub organisation or username."
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name (without org prefix)."
  type        = string
}

variable "deploy_branches" {
  description = "Branches that may assume the GitHub deploy role."
  type        = list(string)
  default     = ["main"]
}

variable "monthly_budget_usd" {
  description = "Monthly AWS spend limit in USD. Set 0 to disable."
  type        = number
  default     = 20
}

variable "budget_alert_email" {
  description = "Email address for budget alerts. Required when monthly_budget_usd > 0."
  type        = string
  default     = ""
}
