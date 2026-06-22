locals {
  name_prefix = "${var.project}-${var.environment}"

  common_tags = {
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    ManagedBy   = "terraform"
    CostCenter  = "student-demo"
    Stack       = "core"
  }
}

# ---------------------------------------------------------------------------
# Artifact storage — private, encrypted, versioned, lifecycle-managed
# ---------------------------------------------------------------------------

module "s3_artifacts" {
  source = "../modules/s3_artifacts"

  project              = var.project
  environment          = var.environment
  common_tags          = local.common_tags
  cors_allowed_origins = var.cors_allowed_origins
}

# ---------------------------------------------------------------------------
# DynamoDB registry tables — MLOps lifecycle metadata
# ---------------------------------------------------------------------------

module "dynamodb_registry" {
  source = "../modules/dynamodb_registry"

  project     = var.project
  environment = var.environment
  common_tags = local.common_tags
}

# ---------------------------------------------------------------------------
# Route53 hosted zone — persistent DNS (survives runtime destroy)
# ---------------------------------------------------------------------------

module "route53" {
  count  = var.domain_name != "" ? 1 : 0
  source = "../modules/route53"

  domain_name        = var.domain_name
  create_hosted_zone = var.create_hosted_zone
  zone_id            = ""
  www_cname_target   = ""
}
