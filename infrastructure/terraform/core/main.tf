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

  project     = var.project
  environment = var.environment
  common_tags = local.common_tags
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
