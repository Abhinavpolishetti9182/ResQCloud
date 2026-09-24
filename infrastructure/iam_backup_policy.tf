# IAM policy for the ResQCloud backup service.
#
# This policy is restricted to the ResQCloud backup bucket.
# It does not create an IAM user, role, or access key.

data "aws_iam_policy_document" "backup_service_policy_document" {
  # Allow the service to list the specific backup bucket.
  statement {
    sid    = "AllowListBackupBucket"
    effect = "Allow"

    actions = [
      "s3:ListBucket"
    ]

    resources = [
      aws_s3_bucket.backup_storage.arn
    ]
  }

  # Allow the service to work with objects inside the backup bucket.
  statement {
    sid    = "AllowBackupObjectOperations"
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:PutObject"
    ]

    resources = [
      "${aws_s3_bucket.backup_storage.arn}/*"
    ]
  }
}

# Create a customer-managed IAM policy.
resource "aws_iam_policy" "backup_service_policy" {
  provider    = aws.no_tags
  name        = "${var.project_name}-backup-service-policy"
  description = "Least-privilege S3 access policy for the ResQCloud backup service"

  policy = data.aws_iam_policy_document.backup_service_policy_document.json
}
