variable "prefix" {
  description = "Prefix for project resources"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

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