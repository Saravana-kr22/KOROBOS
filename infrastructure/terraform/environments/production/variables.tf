variable "environment" {
  description = "The deployment environment"
  type        = string
}

variable "cluster_size" {
  description = "Size of the kubernetes nodes"
  type        = string
}

variable "database_size" {
  description = "Size of the postgres db"
  type        = string
}
