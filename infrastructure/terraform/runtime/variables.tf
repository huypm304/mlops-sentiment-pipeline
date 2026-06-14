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

# ---------------------------------------------------------------------------
# Core stack references
# Either supply these directly (CI/CD reads core outputs) or let runtime
# read them from terraform_remote_state using core_state_bucket/key.
# ---------------------------------------------------------------------------

variable "core_state_bucket" {
  description = "S3 bucket holding the core stack's Terraform state. Used by terraform_remote_state."
  type        = string
  default     = ""
}

variable "core_state_key" {
  description = "State key for the core stack within the state bucket."
  type        = string
  default     = "core/terraform.tfstate"
}

# Direct injection alternative (used when running outside CI, e.g. local plan)
variable "artifact_bucket_name" {
  description = "Override: artifact bucket name read from core outputs. Leave empty to read from remote state."
  type        = string
  default     = ""
}

variable "artifact_bucket_arn" {
  description = "Override: artifact bucket ARN read from core outputs. Leave empty to read from remote state."
  type        = string
  default     = ""
}

variable "dynamodb_table_arns" {
  description = "Override: list of DynamoDB table ARNs. Leave empty to read from remote state."
  type        = list(string)
  default     = []
}

variable "datasets_table_name" {
  type    = string
  default = ""
}

variable "training_runs_table_name" {
  type    = string
  default = ""
}

variable "models_table_name" {
  type    = string
  default = ""
}

variable "predictions_table_name" {
  type    = string
  default = ""
}

variable "monitoring_snapshots_table_name" {
  type    = string
  default = ""
}

variable "approval_requests_table_name" {
  type    = string
  default = ""
}

variable "review_queue_table_name" {
  type    = string
  default = ""
}

# ---------------------------------------------------------------------------
# Lambda configuration
# ---------------------------------------------------------------------------

variable "lambda_runtime" {
  type    = string
  default = "python3.12"
}

variable "lambda_memory_mb" {
  type    = number
  default = 512
}

variable "lambda_timeout_seconds" {
  type    = number
  default = 30
}

variable "log_retention_days" {
  type    = number
  default = 14
}

# ---------------------------------------------------------------------------
# Optional feature flags
# ---------------------------------------------------------------------------

variable "enable_sagemaker_training" {
  description = "Wire real SageMaker CreateTrainingJob into the pipeline Lambda."
  type        = bool
  default     = false
}

variable "enable_sagemaker_endpoint" {
  description = "Create a SageMaker inference endpoint. Incurs cost."
  type        = bool
  default     = false
}

variable "enable_eventbridge_monitoring" {
  description = "Create EventBridge rules for periodic monitoring snapshots."
  type        = bool
  default     = true
}

variable "sagemaker_instance_type" {
  type    = string
  default = "ml.m5.large"
}

variable "model_package_version" {
  description = "Bump when models/production/model.tar.gz changes to force a new SageMaker model + endpoint."
  type        = string
  default     = "v3"
}

# ---------------------------------------------------------------------------
# API / CORS
# ---------------------------------------------------------------------------

variable "cors_allow_origins" {
  type    = list(string)
  default = ["http://localhost:3000", "http://127.0.0.1:3000"]
}

# ---------------------------------------------------------------------------
# Optional custom domain (Route53 + ACM)
# ---------------------------------------------------------------------------

variable "domain_name" {
  description = "Root domain managed in Route53. Empty disables custom domain."
  type        = string
  default     = ""
}

variable "enable_custom_domain" {
  type    = bool
  default = false
}

variable "api_subdomain" {
  description = "API hostname prefix (e.g. api → api.minhhuy.me)."
  type        = string
  default     = "api"
}

variable "create_hosted_zone" {
  type    = bool
  default = true
}

variable "route53_zone_id" {
  type    = string
  default = ""
}

variable "www_cname_target" {
  type    = string
  default = ""
}
