# Deny requests to the backup bucket that do not use HTTPS.
data "aws_iam_policy_document" "backup_bucket_security_policy" {
  statement {
    sid    = "DenyInsecureTransport"
    effect = "Deny"

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions = [
      "s3:*"
    ]

    resources = [
      aws_s3_bucket.backup_storage.arn,
      "${aws_s3_bucket.backup_storage.arn}/*"
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

# Attach the security policy to the backup bucket.
resource "aws_s3_bucket_policy" "backup_storage" {
  bucket = aws_s3_bucket.backup_storage.id
  policy = data.aws_iam_policy_document.backup_bucket_security_policy.json
}