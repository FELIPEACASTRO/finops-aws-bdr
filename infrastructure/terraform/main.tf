################################################################################
# FinOps AWS - Terraform Main Configuration
# Infraestrutura completa para deploy do Lambda de analise de custos AWS
################################################################################

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }

  # Backend S3 (opcional - veja backend.tf.example)
  # Para usar local state, deixe comentado
  # Para usar S3 backend, copie backend.tf.example para backend.tf
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "FinOps-AWS"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = var.owner
      CostCenter  = var.cost_center
    }
  }
}

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  default_tags {
    tags = {
      Project     = "FinOps-AWS"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

################################################################################
# Data Sources
################################################################################

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

data "aws_partition" "current" {}

################################################################################
# Local Values
################################################################################

locals {
  account_id   = data.aws_caller_identity.current.account_id
  region       = data.aws_region.current.name
  partition    = data.aws_partition.current.partition
  
  lambda_name  = "${var.project_name}-${var.environment}"
  
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    Version     = var.app_version
  }
}
