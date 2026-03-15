#!/usr/bin/env bash
# KOROBOS — Second Brain Operating System
# Copyright (c) 2026 Saravana Perumal K
# Licensed under the GNU Affero General Public License v3.
#
# setup_meilisearch.sh — Sprint 6 §15
#
# Initialises the Meilisearch "notes" index with the correct settings
# for the KOROBOS Notes & Knowledge Service.
#
# Usage:
#   ./scripts/setup_meilisearch.sh [MEILISEARCH_URL] [API_KEY]
#
# Defaults match the docker-compose.yml values.

set -euo pipefail

MEILI_URL="${1:-http://localhost:7700}"
MEILI_KEY="${2:-masterKey}"
INDEX="notes"

AUTH_HEADER=""
if [[ -n "$MEILI_KEY" ]]; then
  AUTH_HEADER="Authorization: Bearer ${MEILI_KEY}"
fi

curl_meili() {
  local method="$1"
  local path="$2"
  local body="${3:-}"
  local args=(-s -o /dev/null -w "%{http_code}" -X "$method" "${MEILI_URL}${path}")
  [[ -n "$AUTH_HEADER" ]] && args+=(-H "$AUTH_HEADER")
  if [[ -n "$body" ]]; then
    args+=(-H "Content-Type: application/json" -d "$body")
  fi
  curl "${args[@]}"
}

echo "→ Waiting for Meilisearch at ${MEILI_URL} ..."
for i in $(seq 1 30); do
  status=$(curl -s -o /dev/null -w "%{http_code}" "${MEILI_URL}/health" || true)
  [[ "$status" == "200" ]] && break
  echo "  attempt ${i}/30 — not ready yet, sleeping 2s"
  sleep 2
done
echo "✓ Meilisearch is ready."

# ── Create (or update) the notes index ──────────────────────────────────────
echo "→ Creating index '${INDEX}' ..."
code=$(curl_meili POST "/indexes" "{\"uid\":\"${INDEX}\",\"primaryKey\":\"id\"}")
if [[ "$code" == "201" || "$code" == "202" ]]; then
  echo "✓ Index created (HTTP ${code})."
elif [[ "$code" == "400" ]]; then
  echo "  Index already exists — continuing."
else
  echo "✗ Unexpected response creating index: HTTP ${code}" && exit 1
fi

# ── Searchable attributes ────────────────────────────────────────────────────
echo "→ Configuring searchable attributes ..."
curl_meili PUT "/indexes/${INDEX}/settings/searchable-attributes" \
  '["title","content_md","tags"]' > /dev/null
echo "✓ Searchable: title, content_md, tags"

# ── Filterable attributes (for per-user scoping) ─────────────────────────────
echo "→ Configuring filterable attributes ..."
curl_meili PUT "/indexes/${INDEX}/settings/filterable-attributes" \
  '["user_id","tags"]' > /dev/null
echo "✓ Filterable: user_id, tags"

# ── Sortable attributes ───────────────────────────────────────────────────────
echo "→ Configuring sortable attributes ..."
curl_meili PUT "/indexes/${INDEX}/settings/sortable-attributes" \
  '["created_at","updated_at","title"]' > /dev/null
echo "✓ Sortable: created_at, updated_at, title"

# ── Ranking rules ─────────────────────────────────────────────────────────────
echo "→ Configuring ranking rules ..."
curl_meili PUT "/indexes/${INDEX}/settings/ranking-rules" \
  '["words","typo","proximity","attribute","sort","exactness"]' > /dev/null
echo "✓ Ranking rules set."

# ── Displayed attributes ──────────────────────────────────────────────────────
echo "→ Configuring displayed attributes ..."
curl_meili PUT "/indexes/${INDEX}/settings/displayed-attributes" \
  '["id","note_id","user_id","title","content_md","tags"]' > /dev/null
echo "✓ Displayed attributes set."

echo ""
echo "✅  Meilisearch '${INDEX}' index is ready for KOROBOS Sprint 6."
