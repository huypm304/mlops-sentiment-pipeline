variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "artifact_prefixes" {
  description = "S3 key prefixes representing the MLOps artifact layout."
  type        = list(string)
  default = [
    "datasets/",
    "models/",
    "reports/",
    "evaluation/",
    "artifacts/",
  ]
}
