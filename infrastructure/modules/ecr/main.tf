resource "aws_ecr_repository" "main" {
  name                 = "${var.prefix}-${var.environment}-${var.repository_name}"
  image_tag_mutability = "MUTABLE" # What's the difference?

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "${var.prefix}-${var.environment}-${var.repository_name}"
  }
}

# ECR Lifecycle Policy
resource "aws_ecr_lifecycle_policy" "main" {
  repository = aws_ecr_repository.main.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last ${var.image_retention_count} tagged images"
        selection = {
          tagStatus     = "tagged"
          countType     = "imageCountMoreThan"
          countNumber   = var.image_retention_count
          tagPrefixList = ["notes-api", "main", "dev"]
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Delete untagged images older than 1 day"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

data "aws_caller_identity" "current" {}