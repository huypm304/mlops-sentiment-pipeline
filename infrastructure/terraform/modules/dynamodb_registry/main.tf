locals {
  prefix = "${var.project}-${var.environment}"
}

# ---------------------------------------------------------------------------
# datasets
# ---------------------------------------------------------------------------
resource "aws_dynamodb_table" "datasets" {
  name         = "${local.prefix}-datasets"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "dataset_id"
  range_key    = "created_at"

  attribute {
    name = "dataset_id"
    type = "S"
  }
  attribute {
    name = "created_at"
    type = "S"
  }
  attribute {
    name = "status"
    type = "S"
  }

  global_secondary_index {
    name            = "status-created_at-index"
    hash_key        = "status"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  point_in_time_recovery { enabled = true }

  tags = merge(var.common_tags, { Name = "${local.prefix}-datasets" })
}

# ---------------------------------------------------------------------------
# training_runs
# ---------------------------------------------------------------------------
resource "aws_dynamodb_table" "training_runs" {
  name         = "${local.prefix}-training-runs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "run_id"
  range_key    = "created_at"

  attribute {
    name = "run_id"
    type = "S"
  }
  attribute {
    name = "created_at"
    type = "S"
  }
  attribute {
    name = "status"
    type = "S"
  }

  global_secondary_index {
    name            = "status-created_at-index"
    hash_key        = "status"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  point_in_time_recovery { enabled = true }

  tags = merge(var.common_tags, { Name = "${local.prefix}-training-runs" })
}

# ---------------------------------------------------------------------------
# models (registry)
# ---------------------------------------------------------------------------
resource "aws_dynamodb_table" "models" {
  name         = "${local.prefix}-models"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "model_id"
  range_key    = "version"

  attribute {
    name = "model_id"
    type = "S"
  }
  attribute {
    name = "version"
    type = "S"
  }
  attribute {
    name = "status"
    type = "S"
  }

  global_secondary_index {
    name            = "status-version-index"
    hash_key        = "status"
    range_key       = "version"
    projection_type = "ALL"
  }

  point_in_time_recovery { enabled = true }

  tags = merge(var.common_tags, { Name = "${local.prefix}-models" })
}

# ---------------------------------------------------------------------------
# predictions (inference logs)
# ---------------------------------------------------------------------------
resource "aws_dynamodb_table" "predictions" {
  name         = "${local.prefix}-predictions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "prediction_id"
  range_key    = "created_at"

  attribute {
    name = "prediction_id"
    type = "S"
  }
  attribute {
    name = "created_at"
    type = "S"
  }
  attribute {
    name = "model_version"
    type = "S"
  }

  # Allows querying predictions by model version for comparison
  global_secondary_index {
    name            = "model_version-created_at-index"
    hash_key        = "model_version"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  point_in_time_recovery { enabled = true }

  tags = merge(var.common_tags, { Name = "${local.prefix}-predictions" })
}

# ---------------------------------------------------------------------------
# monitoring_snapshots
# ---------------------------------------------------------------------------
resource "aws_dynamodb_table" "monitoring_snapshots" {
  name         = "${local.prefix}-monitoring-snapshots"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "snapshot_id"
  range_key    = "period_start"

  attribute {
    name = "snapshot_id"
    type = "S"
  }
  attribute {
    name = "period_start"
    type = "S"
  }

  point_in_time_recovery { enabled = true }

  tags = merge(var.common_tags, { Name = "${local.prefix}-monitoring-snapshots" })
}

# ---------------------------------------------------------------------------
# approval_requests
# ---------------------------------------------------------------------------
resource "aws_dynamodb_table" "approval_requests" {
  name         = "${local.prefix}-approval-requests"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "approval_id"
  range_key    = "created_at"

  attribute {
    name = "approval_id"
    type = "S"
  }
  attribute {
    name = "created_at"
    type = "S"
  }
  attribute {
    name = "status"
    type = "S"
  }

  global_secondary_index {
    name            = "status-created_at-index"
    hash_key        = "status"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  point_in_time_recovery { enabled = true }

  tags = merge(var.common_tags, { Name = "${local.prefix}-approval-requests" })
}

# ---------------------------------------------------------------------------
# review_queue (human feedback / low-confidence predictions)
# ---------------------------------------------------------------------------
resource "aws_dynamodb_table" "review_queue" {
  name         = "${local.prefix}-review-queue"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "review_id"
  range_key    = "created_at"

  attribute {
    name = "review_id"
    type = "S"
  }
  attribute {
    name = "created_at"
    type = "S"
  }
  attribute {
    name = "status"
    type = "S"
  }

  global_secondary_index {
    name            = "status-created_at-index"
    hash_key        = "status"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  # TTL only on resolved/rejected items — labeled feedback is kept indefinitely
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  point_in_time_recovery { enabled = true }

  tags = merge(var.common_tags, { Name = "${local.prefix}-review-queue" })
}
