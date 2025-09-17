
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

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
}

variable "az_count" {
  description = "Availability zone count"
  type        = number
}

variable "db_az_count" {
  description = "Number of AZs for database subnets (minimum 2 required by AWS)"
  type        = number
  default     = 2
}
