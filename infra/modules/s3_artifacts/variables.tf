variable "project" {
  type    = string
  default = "absa-mlops"
}

variable "environment" {
  type    = string
  default = "demo"
}

variable "common_tags" {
  type    = map(string)
  default = {}
}

variable "cors_allowed_origins" {
  description = "Browser origins allowed to PUT dataset files via presigned S3 URLs."
  type        = list(string)
  default = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://minhhuy.me",
    "https://www.minhhuy.me",
  ]
}
