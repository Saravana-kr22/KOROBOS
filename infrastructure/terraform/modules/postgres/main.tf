# Terraform Module: Postgres
# KOROBOS Database Cluster
# Implements §15 Disaster Recovery: automated snapshots, WAL archiving

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ── DB Subnet Group ──

resource "aws_db_subnet_group" "main" {
  name       = "korobos-${var.environment}-db-subnet"
  subnet_ids = var.subnet_ids

  tags = {
    Name        = "korobos-${var.environment}-db-subnet"
    Environment = var.environment
  }
}

# ── Security Group for RDS ──

resource "aws_security_group" "rds" {
  name_prefix = "korobos-${var.environment}-rds-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidrs
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "korobos-${var.environment}-rds-sg"
    Environment = var.environment
  }
}

# ── RDS PostgreSQL Instance ──

resource "aws_db_instance" "main" {
  identifier     = "korobos-${var.environment}-postgres"
  engine         = "postgres"
  engine_version = "15"
  instance_class = var.instance_class

  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_encrypted     = true

  db_name  = "korobos"
  username = "korobos"
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  multi_az            = var.environment == "production" ? true : false
  publicly_accessible = false

  # §15 Disaster Recovery — Automated snapshots
  backup_retention_period = var.environment == "production" ? 14 : 7
  backup_window           = "03:00-04:00"

  # §15 Disaster Recovery — WAL archiving / point-in-time recovery
  # RDS enables WAL archiving automatically with backups enabled
  # RPO: 15 minutes (transaction logs shipped every 5 minutes)

  # Final snapshot before deletion
  skip_final_snapshot       = var.environment == "dev" ? true : false
  final_snapshot_identifier = var.environment != "dev" ? "korobos-${var.environment}-final-snapshot" : null
  deletion_protection       = var.environment == "production" ? true : false

  performance_insights_enabled = var.environment != "dev" ? true : false

  tags = {
    Name        = "korobos-${var.environment}-postgres"
    Environment = var.environment
    Project     = "korobos"
  }
}
