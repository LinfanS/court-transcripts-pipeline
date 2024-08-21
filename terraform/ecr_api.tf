resource "aws_ecr_repository" "c12_court_api" {
  name                 = "c12-court-api-ecr"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "c12-court-api-ecr"
    Environment = "production"
  }
}

output "ecr_repository_url_api" {
  value = aws_ecr_repository.c12_court_api.repository_url
}
