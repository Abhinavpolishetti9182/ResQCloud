# Generate a unique suffix for the S3 bucket name.
resource "random_id" "backup_bucket_suffix" {
  byte_length = 4
}

# Create the S3 bucket for ResQCloud backups.
resource "aws_s3_bucket" "backup_storage" {
  bucket = "${var.project_name}-backups-${random_id.backup_bucket_suffix.hex}"

  # Prevent accidental deletion of the backup bucket.
  force_destroy = false

  lifecycle {
    prevent_destroy = true
  }
}

# Enable versioning for backup objects.
resource "aws_s3_bucket_versioning" "backup_storage" {
  bucket = aws_s3_bucket.backup_storage.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable server-side encryption using Amazon S3-managed keys.
resource "aws_s3_bucket_server_side_encryption_configuration" "backup_storage" {
  bucket = aws_s3_bucket.backup_storage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access to the backup bucket.
resource "aws_s3_bucket_public_access_block" "backup_storage" {
  bucket = aws_s3_bucket.backup_storage.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Prevent objects from being owned by external accounts.
resource "aws_s3_bucket_ownership_controls" "backup_storage" {
  bucket = aws_s3_bucket.backup_storage.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}