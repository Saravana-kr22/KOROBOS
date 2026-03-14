# Kafka Dev Assets

This directory contains local-development Kafka bootstrap assets used by
`docker-compose.yml`.

Files:

- `generate-certs.sh`: creates a development CA, broker keystore and
  truststore, and the Kafka client properties used by bootstrap jobs.
- `create-topics.sh`: creates the KOROBOS event topics and their DLQ topics
  against the local broker.

Notes:

- The local Compose stack now uses self-signed TLS plus SASL/PLAIN.
- This remains a dev bootstrap path; staged or production deployments should
  use managed certificates, stronger secret distribution, and ACL hardening.
