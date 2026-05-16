locals {
  bucket_name = "${var.project_name}-${var.environment}"
}

resource "aws_s3_bucket" "artifacts" {
  bucket = local.bucket_name

  tags = {
    Name = local.bucket_name
  }
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Placeholder objects establish the documented folder layout:
# s3://<bucket>/datasets|models|reports|evaluation|artifacts/
resource "aws_s3_object" "prefix_markers" {
  for_each = toset(var.artifact_prefixes)

  bucket  = aws_s3_bucket.artifacts.id
  key     = "${each.value}.keep"
  content = "absa-mlops-platform artifact prefix"
}
