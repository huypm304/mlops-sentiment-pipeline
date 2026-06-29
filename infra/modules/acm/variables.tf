variable "domain_name" {
  description = "Primary certificate domain (e.g. api.minhhuy.me)."
  type        = string
}

variable "subject_alternative_names" {
  description = "Additional names on the certificate."
  type        = list(string)
  default     = []
}

variable "zone_id" {
  description = "Route53 hosted zone ID for DNS validation."
  type        = string
}

variable "wait_for_validation" {
  description = "Wait until ACM certificate is issued (apply may take several minutes)."
  type        = bool
  default     = true
}
