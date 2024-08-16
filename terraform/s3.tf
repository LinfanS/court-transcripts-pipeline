resource "aws_s3_bucket" "c12-court-s3" {
  bucket = "c12-court-bucket"

  force_destroy = true

  tags = {
    Name = "c12-court-bucket"
    Environment = "prod"
  }
}