variable "prefix" {
  description = "Prefix for project resources"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "github_org" {
  description = "GitHub organization name"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
}

variable "github_branches" {
  description = "List of GitHub branches allowed to assume roles"
  type        = list(string)
  default     = ["main", "dev"]
}