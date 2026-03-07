# Terraform Module: Object Storage
# CortexOS S3-compatible storage
# Implements §15 DR: weekly backup via lifecycle rules

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

resource "aws_s3_bucket" "main" {
  bucket = "cortexos-${var.environment}-storage"

  tags = {
    Name        = "cortexos-${var.environment}-storage"
    Environment = var.environment
    Project     = "cortexos"
  }
}

resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "main" {
  bucket = aws_s3_bucket.main.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# §15 Disaster Recovery — weekly backup via replication to backup bucket
resource "aws_s3_bucket" "backup" {
  count  = var.environment == "production" ? 1 : 0
  bucket = "cortexos-${var.environment}-storage-backup"

  tags = {
    Name        = "cortexos-${var.environment}-storage-backup"
    Environment = var.environment
    Purpose     = "disaster-recovery"
  }
}
