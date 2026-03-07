variable "environment" {
  description = "The environment"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
  default     = ""
}

variable "subnet_ids" {
  description = "Subnet IDs"
  type        = list(string)
  default     = []
}

variable "node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "allowed_cidrs" {
  description = "CIDR blocks allowed to connect"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}
