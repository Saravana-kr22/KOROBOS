#!/usr/bin/env bash

set -euo pipefail

bootstrap_server="${KAFKA_BOOTSTRAP_SERVER:-kafka:29093}"
client_config="${KAFKA_CLIENT_CONFIG:-}"

command_config_args=()
if [[ -n "${client_config}" ]]; then
  command_config_args+=(--command-config "${client_config}")
fi

topics=(
  "note.created"
  "note.updated"
  "note.link.created"
  "habit.created"
  "habit.completed"
  "learning.session.logged"
  "meal.logged"
  "workout.logged"
  "user.registered"
  "user.login"
  "ai.interaction.completed"
)

dlq_topics=(
  "note.created.dlq"
  "note.updated.dlq"
  "note.link.created.dlq"
  "habit.created.dlq"
  "habit.completed.dlq"
  "learning.session.logged.dlq"
  "meal.logged.dlq"
  "workout.logged.dlq"
  "user.registered.dlq"
  "user.login.dlq"
  "ai.interaction.completed.dlq"
)

echo "Waiting for Kafka at ${bootstrap_server}..."
for _ in {1..30}; do
  if kafka-topics \
    --bootstrap-server "${bootstrap_server}" \
    "${command_config_args[@]}" \
    --list >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

for topic in "${topics[@]}"; do
  kafka-topics \
    --bootstrap-server "${bootstrap_server}" \
    "${command_config_args[@]}" \
    --create \
    --if-not-exists \
    --topic "${topic}" \
    --partitions 3 \
    --replication-factor 1
done

for topic in "${dlq_topics[@]}"; do
  kafka-topics \
    --bootstrap-server "${bootstrap_server}" \
    "${command_config_args[@]}" \
    --create \
    --if-not-exists \
    --topic "${topic}" \
    --partitions 1 \
    --replication-factor 1
done

echo "Kafka topic bootstrap complete."
