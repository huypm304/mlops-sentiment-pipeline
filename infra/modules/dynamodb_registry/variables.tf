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
