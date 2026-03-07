output "monitoring_namespace" {
  description = "Namespace where monitoring stack is deployed"
  value       = kubernetes_namespace.monitoring.metadata[0].name
}

output "grafana_release_name" {
  description = "Grafana Helm release name"
  value       = helm_release.prometheus_grafana.name
}

output "jaeger_release_name" {
  description = "Jaeger Helm release name"
  value       = helm_release.jaeger.name
}
