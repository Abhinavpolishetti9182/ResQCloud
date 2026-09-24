variable "aws_region" {
  description = "AWS region for ResQCloud infrastructure"

  type = string

  default = "ap-south-2"
}


variable "environment" {
  description = "Deployment environment"

  type = string

  default = "development"
}


variable "project_name" {
  description = "Project name"

  type = string

  default = "resqcloud"
}

variable "admin_ip_cidr" {
  description = "Public IPv4 CIDR allowed to access EC2 through SSH"
  type        = string

  validation {
    condition     = can(cidrhost(var.admin_ip_cidr, 0))
    error_message = "admin_ip_cidr must be a valid IPv4 CIDR block."
  }
}

variable "ec2_instance_type" {
  description = "EC2 instance type for the ResQCloud server"
  type        = string
  default     = "t3.micro"
}