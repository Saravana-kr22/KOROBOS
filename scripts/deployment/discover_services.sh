#!/bin/bash
# Dynamic Service Discovery for KOROBOS
# Discovers all services in the codebase and generates deployment lists
# Used by CI/CD pipelines to maintain dynamic service dependencies

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Output format: json, yaml, or shell
OUTPUT_FORMAT="${1:-json}"

# ============================================================================
# Service Discovery Functions
# ============================================================================

discover_backend_services() {
    """Find all backend services from directory structure"""
    local services=()
    for service_dir in "$PROJECT_ROOT"/backend/services/*/; do
        if [ -d "$service_dir" ]; then
            local service_name=$(basename "$service_dir")
            services+=("$service_name")
        fi
    done
    echo "${services[@]}"
}

discover_workers() {
    """Check if workers directory exists"""
    if [ -d "$PROJECT_ROOT/backend/workers" ]; then
        echo "workers"
    fi
}

discover_infrastructure_services() {
    """Detect infrastructure services (postgres, redis, kafka, etc.)"""
    local services=()

    # Check docker-compose for service definitions
    if [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        # Extract service names from docker-compose
        services=$(grep "^  [a-z-]*:$" "$PROJECT_ROOT/docker-compose.yml" | sed 's/:$//' | xargs)
    fi

    echo "$services"
}

discover_frontend() {
    """Check if frontend exists"""
    if [ -d "$PROJECT_ROOT/frontend" ] && [ -f "$PROJECT_ROOT/frontend/package.json" ]; then
        echo "frontend"
    fi
}

discover_mobile() {
    """Check if mobile app exists"""
    if [ -d "$PROJECT_ROOT/mobile" ] && [ -f "$PROJECT_ROOT/mobile/package.json" ]; then
        echo "mobile"
    fi
}

get_service_health_endpoint() {
    """Return health endpoint for a service"""
    local service=$1
    case "$service" in
        postgres|redis|kafka|zookeeper)
            echo "none"  # Infrastructure services don't have HTTP endpoints
            ;;
        api-gateway)
            echo "/api/v1/health"
            ;;
        *)
            echo "/health"
            ;;
    esac
}

# ============================================================================
# Output Formatters
# ============================================================================

output_json() {
    """Output discovered services as JSON"""
    local backend_svcs=$(discover_backend_services)
    local workers=$(discover_workers)
    local infra_svcs=$(discover_infrastructure_services)
    local frontend=$(discover_frontend)
    local mobile=$(discover_mobile)

    cat <<EOF
{
  "backend_services": [$(echo "$backend_svcs" | sed 's/ /", "/g; s/^/"/; s/$/"/')],
  "workers": [$([ -z "$workers" ] && echo "" || echo "\"$workers\"")],
  "infrastructure_services": [$(echo "$infra_svcs" | sed 's/ /", "/g; s/^/"/; s/$/"/')],
  "frontend": "$([ -z "$frontend" ] && echo "" || echo "$frontend")",
  "mobile": "$([ -z "$mobile" ] && echo "" || echo "$mobile")",
  "all_services": [
    $(echo "$infra_svcs $backend_svcs $workers $frontend $mobile" | tr ' ' '\n' | grep -v '^$' | sort -u | sed 's/^/"/; s/$/"/' | paste -sd, -)
  ]
}
EOF
}

output_yaml() {
    """Output discovered services as YAML"""
    local backend_svcs=$(discover_backend_services)
    local workers=$(discover_workers)
    local infra_svcs=$(discover_infrastructure_services)
    local frontend=$(discover_frontend)
    local mobile=$(discover_mobile)

    cat <<EOF
services:
  backend:
$(echo "$backend_svcs" | tr ' ' '\n' | grep -v '^$' | sed 's/^/    - /')
  infrastructure:
$(echo "$infra_svcs" | tr ' ' '\n' | grep -v '^$' | sed 's/^/    - /')
  workers:
$([ -z "$workers" ] && echo "    []" || echo "$workers" | tr ' ' '\n' | sed 's/^/    - /')
  frontend: $frontend
  mobile: $mobile

all_services:
$(echo "$infra_svcs $backend_svcs $workers $frontend $mobile" | tr ' ' '\n' | grep -v '^$' | sort -u | sed 's/^/  - /')
EOF
}

output_shell() {
    """Output as shell environment variables"""
    local backend_svcs=$(discover_backend_services)
    local workers=$(discover_workers)
    local infra_svcs=$(discover_infrastructure_services)
    local frontend=$(discover_frontend)
    local mobile=$(discover_mobile)

    echo "BACKEND_SERVICES=\"$backend_svcs\""
    echo "WORKERS=\"$workers\""
    echo "INFRASTRUCTURE_SERVICES=\"$infra_svcs\""
    echo "FRONTEND=\"$frontend\""
    echo "MOBILE=\"$mobile\""

    # All services in a single space-separated list
    local all_svcs=$(echo "$infra_svcs $backend_svcs $workers $frontend $mobile" | tr ' ' '\n' | grep -v '^$' | sort -u | tr '\n' ' ' | xargs)
    echo "ALL_SERVICES=\"$all_svcs\""
}

output_github_matrix() {
    """Output as GitHub Actions matrix format"""
    local all_svcs=$(echo "$(discover_infrastructure_services) $(discover_backend_services) $(discover_workers) $(discover_frontend) $(discover_mobile)" | tr ' ' '\n' | grep -v '^$' | sort -u | sed 's/^/"/; s/$/"/' | paste -sd, -)
    echo "service=[$all_svcs]"
}

# ============================================================================
# Main
# ============================================================================

case "$OUTPUT_FORMAT" in
    json)
        output_json
        ;;
    yaml)
        output_yaml
        ;;
    shell)
        output_shell
        ;;
    matrix)
        output_github_matrix
        ;;
    *)
        echo "Unknown output format: $OUTPUT_FORMAT"
        echo "Supported: json, yaml, shell, matrix"
        exit 1
        ;;
esac
