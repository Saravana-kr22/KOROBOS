output "kafka_bootstrap_brokers" {
  description = "Kafka bootstrap broker connection string"
  value       = aws_msk_cluster.main.bootstrap_brokers
}

output "kafka_zookeeper_connect" {
  description = "Zookeeper connection string"
  value       = aws_msk_cluster.main.zookeeper_connect_string
}
