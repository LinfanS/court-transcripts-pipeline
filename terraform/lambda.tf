# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "c12-court-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
    ]
  })
}

# Lambda function using Docker image from ECR
resource "aws_lambda_function" "my_lambda_function" {
  function_name = "c12-court-pipeline"
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"

  image_uri = "129033205317.dkr.ecr.eu-west-2.amazonaws.com/c12-court-transcript-lambda-ecr:latest"

  environment {
    variables = {
      OPENAI_API_KEY = var.OPENAI_API_KEY,
      DB_HOST = var.DB_HOST,
      DB_NAME = var.DB_NAME,
      DB_PASSWORD = var.DB_PASSWORD,
      DB_USER = var.DB_USER,
      DB_PORT = var.DB_PORT,
      ACCESS_KEY_ID = var.ACCESS_KEY_ID,
      SECRET_ACCESS_KEY = var.SECRET_ACCESS_KEY,
      REGION = var.REGION
    }
  }

  memory_size = 512
  ephemeral_storage {
    size = 1024
  }
  timeout     = 600
}

# IAM Role for EventBridge Scheduler to invoke the Lambda function
resource "aws_iam_role" "scheduler_lambda_role" {
  name = "c12-court-scheduler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "scheduler.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })

  # Attach necessary policies for the role to invoke Lambda
  inline_policy {
    name = "lambda-invoke-policy"
    policy = jsonencode({
      Version = "2012-10-17",
      Statement = [
        {
          Effect = "Allow",
          Action = "lambda:InvokeFunction",
          Resource = aws_lambda_function.my_lambda_function.arn
        }
      ]
    })
  }

  depends_on = [aws_lambda_function.my_lambda_function]
}
# EventBridge Scheduler Schedule to trigger Lambda every 2 hours between 09:00 and 17:00
resource "aws_scheduler_schedule" "court_lambda_schedule" {
  name       = "c12-court-lambda-schedule"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "cron(0 9-17/2 ? * MON-FRI *)"

  target {
    arn      = aws_lambda_function.my_lambda_function.arn
    role_arn = aws_iam_role.scheduler_lambda_role.arn
  }

  depends_on = [aws_lambda_function.my_lambda_function, aws_iam_role.scheduler_lambda_role]
}

# Outputs
output "lambda_function_arn" {
  value = aws_lambda_function.my_lambda_function.arn
}
