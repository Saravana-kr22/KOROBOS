variable "environment" {
  description = "The environment"
  type        = string
}

variable "vault_address" {
  description = "Vault server address"
  type        = string
  default     = "https://vault.korobos.internal:8200"
}

variable "vault_token" {
  description = "Vault root token (for provisioning only)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "kubernetes_host" {
  description = "Kubernetes API server URL"
  type        = string
  default     = ""
}

variable "kubernetes_ca_cert" {
  description = "Kubernetes CA certificate"
  type        = string
  default     = ""
}

variable "jwt_secret" {
  description = "JWT signing secret"
  type        = string
  sensitive   = true
  default     = "change-me-in-production"
}

variable "database_url" {
  description = "PostgreSQL connection string"
  type        = string
  sensitive   = true
  default     = ""
}

variable "redis_url" {
  description = "Redis connection URL"
  type        = string
  sensitive   = true
  default     = ""
}

variable "kafka_broker" {
  description = "Kafka bootstrap servers"
  type        = string
  default     = ""
}

variable "api_keys" {
  description = "External API keys"
  type        = string
  sensitive   = true
  default     = ""
}
