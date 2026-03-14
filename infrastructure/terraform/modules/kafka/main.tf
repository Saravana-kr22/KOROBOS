# Terraform Module: Kafka
# KOROBOS Event Streaming via Amazon MSK

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

resource "aws_security_group" "kafka" {
  name_prefix = "korobos-${var.environment}-kafka-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 9092
    to_port     = 9092
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidrs
  }

  ingress {
    from_port   = 2181
    to_port     = 2181
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
    Name        = "korobos-${var.environment}-kafka-sg"
    Environment = var.environment
  }
}

resource "aws_msk_cluster" "main" {
  cluster_name           = "korobos-${var.environment}-kafka"
  kafka_version          = "3.5.1"
  number_of_broker_nodes = var.environment == "production" ? 3 : 2

  broker_node_group_info {
    instance_type   = var.broker_instance_type
    client_subnets  = var.subnet_ids
    security_groups = [aws_security_group.kafka.id]

    storage_info {
      ebs_storage_info {
        volume_size = var.broker_volume_size
      }
    }
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "TLS_PLAINTEXT"
      in_cluster    = true
    }
  }

  logging_info {
    broker_logs {
      cloudwatch_logs {
        enabled   = true
        log_group = "/aws/msk/korobos-${var.environment}"
      }
    }
  }

  tags = {
    Name        = "korobos-${var.environment}-kafka"
    Environment = var.environment
    Project     = "korobos"
  }
}
