variable "domain_name" {
  description = "Root domain (e.g. minhhuy.me)."
  type        = string
}

variable "create_hosted_zone" {
  description = "Create a new Route53 hosted zone. Set false for second env after zone exists."
  type        = bool
  default     = true
}

variable "zone_id" {
  description = "Existing hosted zone ID when create_hosted_zone is false."
  type        = string
  default     = ""
}

variable "www_cname_target" {
  description = "Optional CNAME target for www (e.g. cname.vercel-dns.com)."
  type        = string
  default     = ""
}
