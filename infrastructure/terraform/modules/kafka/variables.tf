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

variable "broker_instance_type" {
  description = "MSK broker instance type"
  type        = string
  default     = "kafka.t3.small"
}

variable "broker_volume_size" {
  description = "EBS volume size per broker in GB"
  type        = number
  default     = 50
}

variable "allowed_cidrs" {
  description = "CIDR blocks allowed to connect"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}
