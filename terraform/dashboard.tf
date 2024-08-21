# VPC and Subnets (Assuming you have them; otherwise, include them)
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

resource "aws_cloudwatch_log_group" "streamlit_log_group" {
  name              = "/ecs/c12-court-dashboard"
  retention_in_days = 7
}


# Security Group for Fargate and RDS Access
resource "aws_security_group" "fargate_sg" {
  name        = "c12-court-dashboard-fargate-sg"
  vpc_id      = data.aws_vpc.default.id
  description = "Security group for Fargate tasks hosting Streamlit dashboard"

  ingress {
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 5432
    to_port     = 5432
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

# Reference the existing ECS Cluster
data "aws_ecs_cluster" "streamlit_cluster" {
  cluster_name = "c12-ecs-cluster"
}

# IAM Role for Fargate Task Execution
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "c12-court-ecs-dashboard-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
  ]
}

resource "aws_ecs_task_definition" "streamlit_task" {
  family                   = "c12-court-streamlit-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  cpu                      = 1024
  memory                   = 2048

  container_definitions = jsonencode([
    {
      name        = "c12-court-streamlit"
      image       = "129033205317.dkr.ecr.eu-west-2.amazonaws.com/c12-court-transcript-ecr:latest"
      essential   = true
      portMappings = [
        {
          containerPort = 8501
          hostPort      = 8501
        }
      ]
      environment = [
        {
          name  = "DB_HOST"
          value = var.DB_HOST
        },
        {
          name  = "DB_USER"
          value = var.DB_USER
        },
        {
          name  = "DB_PASSWORD"
          value = var.DB_PASSWORD
        },
        {
          name  = "DB_NAME"
          value = var.DB_NAME
        },
        {
          name  = "DB_PORT"
          value = var.DB_PORT
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.streamlit_log_group.name
          "awslogs-region"        = var.REGION
          "awslogs-stream-prefix" = "streamlit"
        }
      }
    }
  ])
}


# ECS Service to run the Fargate task
resource "aws_ecs_service" "streamlit_service" {
  name            = "c12-court-dashboard-service"
  cluster         = data.aws_ecs_cluster.streamlit_cluster.id
  task_definition = aws_ecs_task_definition.streamlit_task.arn
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = data.aws_subnets.default.ids
    security_groups = [aws_security_group.fargate_sg.id]
    assign_public_ip = true  # Set to true if you want public access
  }

  desired_count = 1
}

# Output the DNS Name of the Fargate Service
output "fargate_service_url" {
  value = aws_ecs_service.streamlit_service.network_configuration[0].assign_public_ip
}
