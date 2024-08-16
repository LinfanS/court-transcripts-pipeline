resource "aws_ecr_repository" "lambda_ecr_repo" {
  name = "c12-court-transcript-ecr"
}

output "ecr_repository_url" {
  value = aws_ecr_repository.lambda_ecr_repo.repository_url
}

resource "aws_ecr_repository" "real_lambda_ecr_repo" {
  name = "c12-court-transcript-lambda-ecr"
}