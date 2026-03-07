# Terraform Module: Monitoring
# CortexOS Observability Stack
# Implements §12: Prometheus, Grafana, OpenTelemetry, Jaeger, ELK
#
# This module deploys the observability stack using Helm charts
# into the Kubernetes cluster managed by the kubernetes module.

terraform {
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
}

# ── Monitoring Namespace ──

resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = "cortexos-monitoring"
    labels = {
      environment = var.environment
      project     = "cortexos"
    }
  }
}

# ── Prometheus + Grafana (via kube-prometheus-stack) ──

resource "helm_release" "prometheus_grafana" {
  name       = "prometheus"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = "55.0.0"

  set {
    name  = "grafana.enabled"
    value = "true"
  }

  set {
    name  = "grafana.adminPassword"
    value = var.grafana_admin_password
  }

  set {
    name  = "prometheus.prometheusSpec.retention"
    value = var.environment == "production" ? "30d" : "7d"
  }

  # Metrics: API latency, CPU, memory, event queue depth, DB latency
  set {
    name  = "prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues"
    value = "false"
  }
}

# ── Jaeger (Distributed Tracing) ──

resource "helm_release" "jaeger" {
  name       = "jaeger"
  repository = "https://jaegertracing.github.io/helm-charts"
  chart      = "jaeger"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = "0.73.0"

  set {
    name  = "provisionDataStore.cassandra"
    value = "false"
  }

  set {
    name  = "allInOne.enabled"
    value = var.environment == "dev" ? "true" : "false"
  }

  set {
    name  = "storage.type"
    value = "elasticsearch"
  }
}

# ── OpenTelemetry Collector ──

resource "helm_release" "otel_collector" {
  name       = "otel-collector"
  repository = "https://open-telemetry.github.io/opentelemetry-helm-charts"
  chart      = "opentelemetry-collector"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = "0.73.0"

  set {
    name  = "mode"
    value = "deployment"
  }
}

# ── ELK Stack (Elasticsearch + Logstash + Kibana) ──

resource "helm_release" "elasticsearch" {
  name       = "elasticsearch"
  repository = "https://helm.elastic.co"
  chart      = "elasticsearch"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = "8.5.1"

  set {
    name  = "replicas"
    value = var.environment == "production" ? "3" : "1"
  }

  set {
    name  = "resources.requests.memory"
    value = var.environment == "production" ? "4Gi" : "1Gi"
  }
}

resource "helm_release" "logstash" {
  name       = "logstash"
  repository = "https://helm.elastic.co"
  chart      = "logstash"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = "8.5.1"

  depends_on = [helm_release.elasticsearch]
}

resource "helm_release" "kibana" {
  name       = "kibana"
  repository = "https://helm.elastic.co"
  chart      = "kibana"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = "8.5.1"

  depends_on = [helm_release.elasticsearch]
}
