provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
# Separate provider for IAM resources without default tags
provider "aws" {
  alias  = "no_tags"
  region = var.aws_region
}
