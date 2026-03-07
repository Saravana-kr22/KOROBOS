# Terraform Module: VPC
# CortexOS Network Infrastructure
# Implements §14 Network Security Architecture: public/private subnets

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ── VPC ──

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name        = "cortexos-${var.environment}-vpc"
    Environment = var.environment
    Project     = "cortexos"
  }
}

# ── Public Subnets (Load Balancer, CDN) ──

resource "aws_subnet" "public" {
  count                   = length(var.availability_zones)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, count.index)
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name        = "cortexos-${var.environment}-public-${count.index}"
    Environment = var.environment
    Tier        = "public"
  }
}

# ── Private Subnets (Kubernetes Nodes, Databases, Redis, Kafka) ──

resource "aws_subnet" "private" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index + length(var.availability_zones))
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name        = "cortexos-${var.environment}-private-${count.index}"
    Environment = var.environment
    Tier        = "private"
  }
}

# ── Internet Gateway ──

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "cortexos-${var.environment}-igw"
    Environment = var.environment
  }
}

# ── NAT Gateway (for private subnet outbound) ──

resource "aws_eip" "nat" {
  domain = "vpc"

  tags = {
    Name        = "cortexos-${var.environment}-nat-eip"
    Environment = var.environment
  }
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id

  tags = {
    Name        = "cortexos-${var.environment}-nat"
    Environment = var.environment
  }
}

# ── Route Tables ──

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "cortexos-${var.environment}-public-rt"
  }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }

  tags = {
    Name = "cortexos-${var.environment}-private-rt"
  }
}

resource "aws_route_table_association" "public" {
  count          = length(var.availability_zones)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count          = length(var.availability_zones)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}
