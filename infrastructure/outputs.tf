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

output "resqcloud_ec2_role_name" {
  description = "IAM role name for the ResQCloud EC2 instance"
  value       = aws_iam_role.resqcloud_ec2_role.name
}

output "resqcloud_ec2_instance_profile_name" {
  description = "EC2 instance profile name for ResQCloud"
  value       = aws_iam_instance_profile.resqcloud_ec2_profile.name
}

output "vpc_id" {
  description = "ID of the ResQCloud VPC"
  value       = aws_vpc.resqcloud_vpc.id
}

output "public_subnet_id" {
  description = "ID of the ResQCloud public subnet"
  value       = aws_subnet.resqcloud_public_subnet.id
}

output "internet_gateway_id" {
  description = "ID of the ResQCloud Internet Gateway"
  value       = aws_internet_gateway.resqcloud_igw.id
}

output "public_route_table_id" {
  description = "ID of the ResQCloud public route table"
  value       = aws_route_table.resqcloud_public_route_table.id
}

output "ec2_security_group_id" {
  description = "ID of the ResQCloud EC2 security group"
  value       = aws_security_group.resqcloud_ec2_sg.id
}