# CortexOS Vault Configuration
# §13 Secret Management — HashiCorp Vault integration

terraform {
  required_providers {
    vault = {
      source  = "hashicorp/vault"
      version = "~> 3.0"
    }
  }
}

provider "vault" {
  address = var.vault_address
  token   = var.vault_token
}

# ── Vault KV Secrets Engine ──

resource "vault_mount" "cortexos" {
  path        = "cortexos"
  type        = "kv"
  options     = { version = "2" }
  description = "CortexOS secrets store"
}

# ── Per-environment secret paths ──

resource "vault_kv_secret_v2" "app_secrets" {
  mount = vault_mount.cortexos.path
  name  = "${var.environment}/app"

  data_json = jsonencode({
    JWT_SECRET   = var.jwt_secret
    DATABASE_URL = var.database_url
    REDIS_URL    = var.redis_url
    KAFKA_BROKER = var.kafka_broker
    API_KEYS     = var.api_keys
  })
}

# ── Vault Policy for CortexOS services ──

resource "vault_policy" "cortexos_read" {
  name = "cortexos-${var.environment}-read"

  policy = <<-EOT
    path "cortexos/data/${var.environment}/*" {
      capabilities = ["read", "list"]
    }
  EOT
}

# ── Kubernetes Auth Method (for pods to authenticate) ──

resource "vault_auth_backend" "kubernetes" {
  type = "kubernetes"
  path = "kubernetes-${var.environment}"
}

resource "vault_kubernetes_auth_backend_config" "main" {
  backend            = vault_auth_backend.kubernetes.path
  kubernetes_host    = var.kubernetes_host
  kubernetes_ca_cert = var.kubernetes_ca_cert
}

resource "vault_kubernetes_auth_backend_role" "cortexos" {
  backend                          = vault_auth_backend.kubernetes.path
  role_name                        = "cortexos-${var.environment}"
  bound_service_account_names      = ["cortexos-sa"]
  bound_service_account_namespaces = ["cortexos-${var.environment}"]
  token_policies                   = [vault_policy.cortexos_read.name]
  token_ttl                        = 3600
}
