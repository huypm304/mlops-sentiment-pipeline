locals {
  bucket_name = "${var.project}-${var.environment}-artifacts"

  # Full MLOps prefix layout — markers ensure prefixes appear in the console
  artifact_prefixes = [
    "dvc-store/",
    "datasets/pending/",
    "datasets/approved/",
    "datasets/rejected/",
    "datasets/manifests/",
    "models/v1/",
    "models/candidates/",
    "models/production/",
    "models/archived/",
    "training-runs/",
    "reports/audit/",
    "reports/evaluation/",
    "reports/calibration/",
    "prediction-logs/raw/",
    "prediction-logs/aggregated/",
    "feedback/labeled/",
    "training-checkpoints/",
    "temp/",
  ]
}

resource "aws_s3_bucket" "artifacts" {
  bucket = local.bucket_name

  tags = merge(var.common_tags, {
    Name    = local.bucket_name
    Purpose = "mlops-artifacts"
  })

  # Protect model artifacts, dataset history, and evaluation reports from
  # accidental `terraform destroy`. Remove this block only if you intend to
  # permanently delete all data.
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket                  = aws_s3_bucket.artifacts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    id     = "expire-rejected-datasets"
    status = "Enabled"
    filter { prefix = "datasets/rejected/" }
    expiration { days = 30 }
    noncurrent_version_expiration { noncurrent_days = 7 }
  }

  rule {
    id     = "expire-training-checkpoints"
    status = "Enabled"
    filter { prefix = "training-checkpoints/" }
    expiration { days = 7 }
    noncurrent_version_expiration { noncurrent_days = 3 }
  }

  rule {
    id     = "expire-temp"
    status = "Enabled"
    filter { prefix = "temp/" }
    expiration { days = 3 }
  }

  rule {
    id     = "tier-raw-prediction-logs"
    status = "Enabled"
    filter { prefix = "prediction-logs/raw/" }
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    expiration { days = 90 }
    noncurrent_version_expiration { noncurrent_days = 7 }
  }

  # Abort stuck multi-part uploads to avoid orphaned charges
  rule {
    id     = "abort-incomplete-multipart"
    status = "Enabled"
    filter { prefix = "" }
    abort_incomplete_multipart_upload { days_after_initiation = 3 }
  }

  # Keep models/production/ and reports/evaluation/ indefinitely (no expiry rule)
}

# Placeholder objects so prefixes are visible in the AWS console
resource "aws_s3_object" "prefix_markers" {
  for_each = toset(local.artifact_prefixes)

  bucket  = aws_s3_bucket.artifacts.id
  key     = "${each.value}.keep"
  content = "absa-mlops artifact prefix marker"

  tags = { Purpose = "prefix-marker" }
}
