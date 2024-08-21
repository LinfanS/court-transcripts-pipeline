data "aws_ecs_cluster" "streamlit_cluster" {
  cluster_name = "c12-ecs-cluster"
}

# IAM Role for ECS Task Execution
resource "aws_iam_role" "c12_court_api_task_execution_role" {
  name = "c12-court-api-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
  ]
}

# Security Group for ECS
resource "aws_security_group" "c12_court_api_sg" {
  name        = "c12-court-api-sg"
  description = "Allow traffic to the ECS task"
  vpc_id      = "vpc-061c17c21b97427d8"

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "c12_court_api_task" {
  family                   = "c12-court-api-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = aws_iam_role.c12_court_api_task_execution_role.arn
  cpu                      = "1024"
  memory                   = "2048"

  container_definitions = jsonencode([
    {
      name      = "c12-court-api-container"
      image     = "129033205317.dkr.ecr.eu-west-2.amazonaws.com/c12-court-api-ecr:latest"
      essential = true
      portMappings = [
        {
          containerPort = 80
          hostPort      = 80
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "DB_HOST"
          value = var.DB_HOST
        },
        {
          name  = "DB_PORT"
          value = var.DB_PORT
        },
        {
          name  = "DB_NAME"
          value = var.DB_NAME
        },
        {
          name  = "DB_USER"
          value = var.DB_USER
        },
        {
          name  = "DB_PASSWORD"
          value = var.DB_PASSWORD
        }
      ]
    }
  ])
}

# ECS Service
resource "aws_ecs_service" "c12-court-api-service" {
  name            = "c12-court-api-service"
  cluster         = aws_ecs_cluster.streamlit_cluster.id
  task_definition = aws_ecs_task_definition.c12_court_api_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = ["subnet-0c459ebb007081668"]
    security_groups = [aws_security_group.c12_court_api_sg.id]
    assign_public_ip = true
  }

  depends_on = [aws_ecs_task_definition.c12_court_api_task]
}

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
