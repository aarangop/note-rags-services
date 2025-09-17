terraform {
  required_version = ">= 1.2"
  backend "s3" {
    bucket  = "note-rags-terraform-state-x8nsnwip"
    key     = "terraform.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
  required_providers {
    aws = {
      version = "6.13.0"
      source  = "hashicorp/aws"
    }
    random = {
      source  = "hashicorp/random"
      version = "3.7.2"
    }
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = {
      Project     = "note-rags"
      Environment = terraform.workspace
      ManagedBy   = "terraform"
    }
  }
}
