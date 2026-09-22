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