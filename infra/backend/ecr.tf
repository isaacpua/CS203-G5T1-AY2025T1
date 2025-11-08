variable "backend_service_names" {
  description = "A list of backend service names for ECR repos."
  type        = set(string)
  default = [
    "tariff-backend",
    "mcp-gateway-backend",
    "mcp-chatbot-backend",
    "mcp-server-backend"
  ]
}

# create one ECR repository for each backend service
resource "aws_ecr_repository" "backend_repos" {
  for_each = var.backend_service_names

  name = "${var.project_name}-${each.value}"
  
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Project = var.project_name
  }
}

# apply a lifecycle policy to EACH repository we just created
resource "aws_ecr_lifecycle_policy" "backend_repo_policies" {
  # loops over the map of repositories created above
  for_each = aws_ecr_repository.backend_repos

  # each.key is the service name (e.g. "tariff-backend")
  # each.value is the repository object
  repository = each.value.name 

  # keep the 10 most recent images, saving on storage costs
  policy = jsonencode({
    rules = [{
      rulePriority = 1,
      description  = "Keep last 10 images",
      selection = {
        tagStatus   = "any",
        countType   = "imageCountMoreThan",
        countNumber = 10
      },
      action = {
        type = "expire"
      }
    }]
  })
}
