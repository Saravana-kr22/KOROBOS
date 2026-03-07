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
  description = "Subnet IDs for DB"
  type        = list(string)
  default     = []
}

variable "instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

variable "max_allocated_storage" {
  description = "Max autoscaled storage in GB"
  type        = number
  default     = 100
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
  default     = "change-me"
}

variable "allowed_cidrs" {
  description = "CIDR blocks allowed to connect"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}
