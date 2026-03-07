output "vault_mount_path" {
  description = "Path of the KV secrets engine"
  value       = vault_mount.cortexos.path
}

output "vault_policy_name" {
  description = "Name of the read policy"
  value       = vault_policy.cortexos_read.name
}
