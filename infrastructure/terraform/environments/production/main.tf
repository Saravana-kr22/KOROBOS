# Environment: production
# KOROBOS Infrastructure setup

module "vpc" {
  source = "../../modules/vpc"
  environment = var.environment
}

module "kubernetes" {
  source = "../../modules/kubernetes"
  environment = var.environment
}

module "postgres" {
  source = "../../modules/postgres"
  environment = var.environment
}

module "redis" {
  source = "../../modules/redis"
  environment = var.environment
}

module "kafka" {
  source = "../../modules/kafka"
  environment = var.environment
}

module "object-storage" {
  source = "../../modules/object-storage"
  environment = var.environment
}

module "monitoring" {
  source = "../../modules/monitoring"
  environment = var.environment
}
