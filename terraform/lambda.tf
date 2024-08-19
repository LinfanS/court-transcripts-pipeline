data "aws_caller_identity" "current" {}

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

resource "aws_cloudwatch_log_group" "lambda_log_group" {
  name              = "/aws/lambda/c12-court-pipeline"
  retention_in_days = 14
}

resource "aws_iam_role_policy" "lambda_logging_policy" {
  name = "lambda-logging-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = [
          "arn:aws:logs:${var.REGION}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/*"
        ]
      }
    ]
  })
}

resource "aws_lambda_function" "my_lambda_function" {
  function_name = "c12-court-pipeline"
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"

  image_uri = "129033205317.dkr.ecr.eu-west-2.amazonaws.com/c12-court-transcript-lambda-ecr:latest"

  environment {
    variables = {
      OPENAI_API_KEY     = var.OPENAI_API_KEY,
      DB_HOST            = var.DB_HOST,
      DB_NAME            = var.DB_NAME,
      DB_PASSWORD        = var.DB_PASSWORD,
      DB_USER            = var.DB_USER,
      DB_PORT            = var.DB_PORT,
      ACCESS_KEY_ID      = var.ACCESS_KEY_ID,
      SECRET_ACCESS_KEY  = var.SECRET_ACCESS_KEY,
      REGION             = var.REGION
    }
  }

  memory_size = 512
  ephemeral_storage {
    size = 1024
  }
  timeout     = 600

  depends_on = [aws_cloudwatch_log_group.lambda_log_group, aws_iam_role_policy.lambda_logging_policy]
}

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

resource "aws_scheduler_schedule" "court_lambda_schedule" {
  name       = "c12-court-lambda-schedule"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "cron(0 9-17/2 ? * * *)"

  target {
    arn      = aws_lambda_function.my_lambda_function.arn
    role_arn = aws_iam_role.scheduler_lambda_role.arn
  }

  depends_on = [aws_lambda_function.my_lambda_function, aws_iam_role.scheduler_lambda_role, aws_iam_role_policy.lambda_logging_policy]
}

output "lambda_function_arn" {
  value = aws_lambda_function.my_lambda_function.arn
}

output "cloudwatch_log_group_name" {
  value = aws_cloudwatch_log_group.lambda_log_group.name
}
