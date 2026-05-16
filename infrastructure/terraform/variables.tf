variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "ap-southeast-1"
}

variable "project_name" {
  description = "Short project identifier used in resource names."
  type        = string
  default     = "absa-mlops-platform"
}

variable "environment" {
  description = "Deployment environment (dev, prod)."
  type        = string
  default     = "dev"
}

variable "lambda_runtime" {
  description = "Python runtime for Lambda functions."
  type        = string
  default     = "python3.11"
}

variable "lambda_memory_mb" {
  description = "Default Lambda memory (MB)."
  type        = number
  default     = 512
}

variable "lambda_timeout_seconds" {
  description = "Default Lambda timeout (seconds)."
  type        = number
  default     = 30
}

variable "sagemaker_instance_type" {
  description = "SageMaker inference instance type (demo-sized)."
  type        = string
  default     = "ml.m5.large"
}

variable "enable_sagemaker_endpoint" {
  description = "Create SageMaker endpoint resources (costly; disable for plan-only demos)."
  type        = bool
  default     = false
}

variable "cors_allow_origins" {
  description = "Allowed CORS origins for API Gateway."
  type        = list(string)
  default     = ["http://localhost:3000", "https://localhost:3000"]
}

variable "domain_name" {
  description = "Root domain managed in Route53 (e.g. minhhuy.me). Empty disables DNS/TLS custom domain."
  type        = string
  default     = ""
}

variable "enable_custom_domain" {
  description = "Enable Route53, ACM, and API Gateway custom domain."
  type        = bool
  default     = false
}

variable "create_hosted_zone" {
  description = "Create Route53 hosted zone. Set false for prod if zone was created by dev."
  type        = bool
  default     = true
}

variable "route53_zone_id" {
  description = "Existing hosted zone ID when create_hosted_zone is false."
  type        = string
  default     = ""
}

variable "api_subdomain" {
  description = "API hostname prefix (api.minhhuy.me or api.dev.minhhuy.me)."
  type        = string
  default     = "api"
}

variable "www_cname_target" {
  description = "Optional www CNAME for frontend (e.g. cname.vercel-dns.com from Vercel)."
  type        = string
  default     = ""
}
