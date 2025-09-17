
# Base variables

variable "prefix" {
  description = "Prefix for project resources"
  type        = string
  default     = "note-rags"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

# Networking

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "az_count" {
  description = "Availability zone count"
  type        = number
  default     = 1
}

variable "db_az_count" {
  description = "Number of AZs for database subnets (minimum 2 required by AWS)"
  type        = number
  default     = 2
}

# Security
variable "github_org" {
  description = "GitHub organization name"
  type        = string
  default     = "aarangop"
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
  default     = "note-rags-services"
}

variable "github_branches" {
  description = "List of GitHub branches allowed to assume roles"
  type        = list(string)
  default     = ["main", "dev"]
}

# ECR
variable "repository_name" {
  description = "Name of the ECR repository"
  type        = string
  default     = "services"
}

variable "image_retention_count" {
  description = "Number of images to retain in ECR"
  type        = number
  default     = 20 # Higher since we'll have multiple services
}

# Database
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "create_bastion" {
  description = "Whether to create a bastion host"
  type        = bool
  default     = false
}

variable "bastion_key_name" {
  description = "EC2 Key Pair name for bastion host"
  type        = string
  default     = ""
}

variable "allowed_ssh_cidrs" {
  description = "CIDR blocks allowed to SSH to bastion"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
