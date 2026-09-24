# Trust policy that allows EC2 to assume this IAM role.
data "aws_iam_policy_document" "ec2_assume_role_policy" {
  statement {
    sid    = "AllowEC2AssumeRole"
    effect = "Allow"

    actions = [
      "sts:AssumeRole"
    ]

    principals {
      type = "Service"

      identifiers = [
        "ec2.amazonaws.com"
      ]
    }
  }
}

# IAM role used by the future ResQCloud EC2 instance.
resource "aws_iam_role" "resqcloud_ec2_role" {
  provider = aws.no_tags
  name     = "${var.project_name}-ec2-backup-role"

  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role_policy.json

  description = "IAM role for the ResQCloud EC2 backup application"
}

# Attach the restricted S3 backup policy to the EC2 role.
resource "aws_iam_role_policy_attachment" "backup_service_policy_attachment" {
  role       = aws_iam_role.resqcloud_ec2_role.name
  policy_arn = aws_iam_policy.backup_service_policy.arn
}

# Instance profile that allows an EC2 instance to use the IAM role.
resource "aws_iam_instance_profile" "resqcloud_ec2_profile" {
  provider = aws.no_tags
  name     = "${var.project_name}-ec2-instance-profile"

  role = aws_iam_role.resqcloud_ec2_role.name
}
