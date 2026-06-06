variable "project" {
  type    = string
  default = "absa-mlops"
}

variable "environment" {
  type    = string
  default = "demo"
}

variable "github_org" {
  description = "GitHub organisation or username (e.g. minh-huy)."
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name without the org prefix (e.g. mlops-sentiment-pipeline)."
  type        = string
}

variable "deploy_branches" {
  description = "Branches allowed to assume the deploy role (glob patterns accepted)."
  type        = list(string)
  default     = ["main"]
}

variable "common_tags" {
  type    = map(string)
  default = {}
}
