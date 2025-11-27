################################################################################
# FinOps AWS - S3 Storage Configuration
# Armazenamento unificado para estado, relatorios e checkpoints
# OTIMIZADO: Sem DynamoDB - usando apenas S3 para reducao de custo
################################################################################

################################################################################
# S3 Bucket - Reports, State and Checkpoints
################################################################################

resource "aws_s3_bucket" "reports" {
  bucket = var.s3_bucket_name != "" ? var.s3_bucket_name : "${local.lambda_name}-storage-${local.account_id}"
  
  force_destroy = var.environment != "prod"

  tags = merge(local.common_tags, {
    Name = "${local.lambda_name}-storage"
    Purpose = "Reports, State, Checkpoints"
  })
}

resource "aws_s3_bucket_versioning" "reports" {
  count  = var.enable_s3_versioning ? 1 : 0
  bucket = aws_s3_bucket.reports.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "reports" {
  bucket = aws_s3_bucket.reports.id

  rule {
    id     = "expire-old-reports"
    status = "Enabled"

    filter {
      prefix = "reports/"
    }

    expiration {
      days = var.s3_retention_days
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }

  rule {
    id     = "expire-execution-state"
    status = "Enabled"

    filter {
      prefix = "state/executions/"
    }

    expiration {
      days = 7
    }
  }

  rule {
    id     = "expire-checkpoints"
    status = "Enabled"

    filter {
      prefix = "checkpoints/"
    }

    expiration {
      days = 3
    }
  }

  rule {
    id     = "intelligent-tiering-archives"
    status = "Enabled"

    filter {
      prefix = "archives/"
    }

    transition {
      days          = 30
      storage_class = "INTELLIGENT_TIERING"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }
  }

  rule {
    id     = "abort-incomplete-multipart"
    status = "Enabled"

    filter {
      prefix = ""
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "reports" {
  bucket = aws_s3_bucket.reports.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.enable_kms_encryption ? "aws:kms" : "AES256"
      kms_master_key_id = var.enable_kms_encryption ? aws_kms_key.main[0].arn : null
    }
    bucket_key_enabled = var.enable_kms_encryption
  }
}

resource "aws_s3_bucket_public_access_block" "reports" {
  bucket = aws_s3_bucket.reports.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "reports" {
  bucket = aws_s3_bucket.reports.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "EnforceTLS"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.reports.arn,
          "${aws_s3_bucket.reports.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      },
      {
        Sid       = "EnforceMinTLSVersion"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.reports.arn,
          "${aws_s3_bucket.reports.arn}/*"
        ]
        Condition = {
          NumericLessThan = {
            "s3:TlsVersion" = "1.2"
          }
        }
      }
    ]
  })
}

################################################################################
# S3 Bucket Metrics (para dashboard)
################################################################################

resource "aws_s3_bucket_metric" "reports" {
  bucket = aws_s3_bucket.reports.id
  name   = "EntireBucket"
}

resource "aws_s3_bucket_metric" "state" {
  bucket = aws_s3_bucket.reports.id
  name   = "StatePrefix"
  
  filter {
    prefix = "state/"
  }
}

resource "aws_s3_bucket_metric" "reports_prefix" {
  bucket = aws_s3_bucket.reports.id
  name   = "ReportsPrefix"
  
  filter {
    prefix = "reports/"
  }
}
