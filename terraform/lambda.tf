# # IAM Role for Lambda
# resource "aws_iam_role" "lambda_role" {
#   name = "c12-court-lambda-role"

#   assume_role_policy = jsonencode({
#     Version = "2012-10-17",
#     Statement = [
#       {
#         Action = "sts:AssumeRole",
#         Effect = "Allow",
#         Principal = {
#           Service = "lambda.amazonaws.com"
#         }
#       },
#     ]
#   })
# }

# # Lambda function using Docker image from ECR
# resource "aws_lambda_function" "my_lambda_function" {
#   function_name = "c12-court-pipeline"
#   role          = aws_iam_role.lambda_role.
#   package_type  = "Image"

#   image_uri = aws_ecr_repository.lambda_ecr_repo.repository_url

#   environment {
#     variables = {
#       OPENAI_API_KEY = var.OPENAI_API_KEY
#     }
#   }

#   memory_size = 128
#   timeout     = 30
# }

# # IAM Role for EventBridge Scheduler to invoke the Lambda function
# resource "aws_iam_role" "scheduler_lambda_role" {
#   name = "c12-court-scheduler-role"

#   assume_role_policy = jsonencode({
#     Version = "2012-10-17",
#     Statement = [
#       {
#         Effect = "Allow",
#         Principal = {
#           Service = "scheduler.amazonaws.com"
#         },
#         Action = "sts:AssumeRole"
#       }
#     ]
#   })

#   # Attach necessary policies for the role to invoke Lambda
#   inline_policy {
#     name = "lambda-invoke-policy"
#     policy = jsonencode({
#       Version = "2012-10-17",
#       Statement = [
#         {
#           Effect = "Allow",
#           Action = "lambda:InvokeFunction",
#           Resource = aws_lambda_function.my_lambda_function.arn
#         }
#       ]
#     })
#   }

#   depends_on = [aws_lambda_function.my_lambda_function]
# }
# # EventBridge Scheduler Schedule to trigger Lambda every 2 hours between 09:00 and 17:00
# resource "aws_scheduler_schedule" "court_lambda_schedule" {
#   name       = "c12-court-lambda-schedule"
#   group_name = "default"

#   flexible_time_window {
#     mode = "OFF"
#   }

#   schedule_expression = "cron(0 9-17/2 * * ? *)"

#   target {
#     arn      = aws_lambda_function.my_lambda_function.arn
#     role_arn = aws_iam_role.scheduler_lambda_role.arn
#   }

#   depends_on = [aws_lambda_function.my_lambda_function, aws_iam_role.scheduler_lambda_role]
# }

# # Outputs
# output "lambda_function_arn" {
#   value = aws_lambda_function.my_lambda_function.arn
# }
