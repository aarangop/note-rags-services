
variable "prefix" {
  description = "Prefix for project resources"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where bastion will be created"
  type        = string
}

variable "public_subnet_id" {
  description = "Public subnet ID for bastion placement"
  type        = string
}

variable "db_endpoint" {
  description = "Database endpoint for bastion configuration"
  type        = string
  default     = ""
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