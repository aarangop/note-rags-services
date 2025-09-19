
# Backend outputs
output "terraform_state_bucket" {
  description = "Name of the S3 bucket for Terraform state"
  value       = aws_s3_bucket.terraform_state.bucket
}

# Networking outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.networking.private_subnet_ids
}

output "database_subnet_ids" {
  description = "IDs of the database subnets"
  value       = module.networking.database_subnet_ids
}

output "bastion_public_ip" {
  description = "Bastion's public IP"
  value       = module.bastion.bastion_public_ip
}

# Security
output "oidc_provider_arn" {
  description = "ARN of the GitHub OIDC provider"
  value       = module.security.oidc_provider_arn
}

output "github_actions_role_arn" {
  description = "ARN of the GitHub Actions ECR role"
  value       = module.security.github_actions_role_arn
}

# ECR
output "ecr_repository_name" {
  description = "Name of the ECR repository"
  value       = module.ecr.repository_name
}

# Database
output "db_instance_endpoint" {
  description = "Database's private endpoint"
  value       = module.database.db_instance_endpoint
}

# EKS
output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = var.create_eks ? module.eks[0].cluster_endpoint : null
}

output "eks_cluster_secrets_manager_role_arn" {
  description = "EKS cluster's Secrets Manager role ARN"
  value       = var.create_eks ? module.eks[0].secrets_manager_role_arn : null
}