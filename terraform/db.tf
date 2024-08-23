resource "aws_security_group" "db_sg" {
  description = "security group for court database"
  
  egress  {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = 5432
    protocol    = "tcp"
    to_port     = 5432
  }
  
  egress  {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = 8501
    protocol    = "tcp"
    to_port     = 8501
  }
  
  ingress  {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = 5432
    protocol    = "tcp"
    to_port     = 5432
  }
  
  ingress  {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = 8501
    protocol    = "tcp"
    to_port     = 8501
  }
  
  name   = "c12-milanesers-db"
  vpc_id = "vpc-061c17c21b97427d8"
}

resource "aws_db_instance" "court_db" {
  allocated_storage            = 20
  availability_zone            = "eu-west-2c"
  db_name                      = var.DB_NAME
  db_subnet_group_name         = "c12-public-subnet-group"
  engine                       = "postgres"
  engine_version               = "16.3"
  identifier                   = "c12-milanesers-court"
  instance_class               = "db.t3.micro"
  multi_az                     = false
  password                     = var.DB_PASSWORD
  performance_insights_enabled = false
  port                         = var.DB_PORT
  publicly_accessible          = true
  skip_final_snapshot          = true
  username                     = var.DB_USER
  vpc_security_group_ids       = [aws_security_group.db_sg.id]
}
