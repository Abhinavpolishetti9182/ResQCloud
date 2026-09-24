output "aws_region" {
  description = "Configured AWS region"
  value       = var.aws_region
}

output "project_name" {
  description = "Configured project name"
  value       = var.project_name
}

output "environment" {
  description = "Configured deployment environment"
  value       = var.environment
}

output "backup_bucket_name" {
  description = "Name of the ResQCloud backup S3 bucket"
  value       = aws_s3_bucket.backup_storage.bucket
}

output "backup_bucket_arn" {
  description = "ARN of the ResQCloud backup S3 bucket"
  value       = aws_s3_bucket.backup_storage.arn
}

output "backup_service_policy_arn" {
  description = "ARN of the ResQCloud backup service IAM policy"
  value       = aws_iam_policy.backup_service_policy.arn
}