#!/usr/bin/env bash

set -euo pipefail

secrets_dir="${KAFKA_SECRETS_DIR:-/etc/kafka/secrets}"
storepass="${KAFKA_STORE_PASSWORD:-changeit}"
keypass="${KAFKA_KEY_PASSWORD:-changeit}"

mkdir -p "${secrets_dir}"

if [[ \
  -f "${secrets_dir}/ca.crt" \
  && -f "${secrets_dir}/server.keystore.jks" \
  && -f "${secrets_dir}/server.truststore.jks" \
]]; then
  echo "Kafka TLS key material already exists in ${secrets_dir}"
else
  openssl req \
    -new \
    -x509 \
    -nodes \
    -newkey rsa:4096 \
    -keyout "${secrets_dir}/ca.key" \
    -out "${secrets_dir}/ca.crt" \
    -days 3650 \
    -subj "/CN=CortexOS Kafka Dev CA"

  cat > "${secrets_dir}/server-ext.cnf" <<'EOF'
subjectAltName=DNS:kafka,DNS:localhost,IP:127.0.0.1
extendedKeyUsage=serverAuth
EOF

  keytool \
    -genkeypair \
    -alias kafka-broker \
    -keystore "${secrets_dir}/server.keystore.jks" \
    -storepass "${storepass}" \
    -storetype JKS \
    -keypass "${keypass}" \
    -keyalg RSA \
    -validity 3650 \
    -dname "CN=kafka" \
    -ext SAN=DNS:kafka,DNS:localhost,IP:127.0.0.1

  keytool \
    -certreq \
    -alias kafka-broker \
    -keystore "${secrets_dir}/server.keystore.jks" \
    -storepass "${storepass}" \
    -file "${secrets_dir}/server.csr" \
    -ext SAN=DNS:kafka,DNS:localhost,IP:127.0.0.1

  openssl x509 \
    -req \
    -CA "${secrets_dir}/ca.crt" \
    -CAkey "${secrets_dir}/ca.key" \
    -in "${secrets_dir}/server.csr" \
    -out "${secrets_dir}/server-signed.crt" \
    -days 3650 \
    -CAcreateserial \
    -extfile "${secrets_dir}/server-ext.cnf"

  keytool \
    -import \
    -alias CARoot \
    -file "${secrets_dir}/ca.crt" \
    -keystore "${secrets_dir}/server.keystore.jks" \
    -storepass "${storepass}" \
    -noprompt

  keytool \
    -import \
    -alias kafka-broker \
    -file "${secrets_dir}/server-signed.crt" \
    -keystore "${secrets_dir}/server.keystore.jks" \
    -storepass "${storepass}" \
    -noprompt

  keytool \
    -import \
    -alias CARoot \
    -file "${secrets_dir}/ca.crt" \
    -keystore "${secrets_dir}/server.truststore.jks" \
    -storepass "${storepass}" \
    -storetype JKS \
    -noprompt
fi

printf '%s' "${storepass}" > "${secrets_dir}/keystore_creds"
printf '%s' "${keypass}" > "${secrets_dir}/key_creds"
printf '%s' "${storepass}" > "${secrets_dir}/truststore_creds"

cat > "${secrets_dir}/client.properties" <<EOF
security.protocol=SASL_SSL
sasl.mechanism=PLAIN
sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required username="cortexos" password="cortexos-secret";
ssl.truststore.location=${secrets_dir}/server.truststore.jks
ssl.truststore.password=${storepass}
EOF

cat > "${secrets_dir}/kafka_server_jaas.conf" <<'EOF'
KafkaServer {
  org.apache.kafka.common.security.plain.PlainLoginModule required
  username="cortexos"
  password="cortexos-secret"
  user_cortexos="cortexos-secret";
};

Client {
  org.apache.kafka.common.security.plain.PlainLoginModule required
  username="cortexos"
  password="cortexos-secret";
};
EOF

chmod 600 \
  "${secrets_dir}/keystore_creds" \
  "${secrets_dir}/key_creds" \
  "${secrets_dir}/truststore_creds" \
  "${secrets_dir}/kafka_server_jaas.conf"

echo "Kafka TLS and SASL assets generated in ${secrets_dir}"
