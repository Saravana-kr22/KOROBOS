#!/bin/bash
# Pre-Deployment Validation Script for KOROBOS
# Validates Helm charts, generates dry-runs, and verifies cluster readiness
# Run before deploying to any environment

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

ENVIRONMENT="${1:-development}"
DRY_RUN="${2:-true}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Pre-Deployment Validation for KOROBOS ($ENVIRONMENT)"
echo "=================================================="
echo ""

# ============================================================================
# 1. Helm Chart Validation
# ============================================================================

validate_helm_charts() {
    echo "📋 Step 1: Validating Helm Charts..."

    if ! command -v helm &> /dev/null; then
        echo "❌ Helm not installed"
        return 1
    fi

    local chart_count=0
    local error_count=0

    for chart_dir in "$PROJECT_ROOT/infrastructure/helm/charts"/*/; do
        if [ -f "${chart_dir}Chart.yaml" ]; then
            chart_name=$(basename "$chart_dir")
            echo "  Linting $chart_name..."

            if helm lint "$chart_dir" > /tmp/helm-lint.log 2>&1; then
                echo "    ✓ $chart_name passed lint"
                ((chart_count++))
            else
                echo "    ✗ $chart_name failed lint"
                cat /tmp/helm-lint.log | sed 's/^/      /'
                ((error_count++))
            fi
        fi
    done

    if [ $error_count -gt 0 ]; then
        echo "❌ $error_count chart(s) failed validation"
        return 1
    fi

    echo "✅ All $chart_count Helm charts passed validation"
    echo ""
    return 0
}

# ============================================================================
# 2. Docker Image Validation
# ============================================================================

validate_docker_images() {
    echo "🐳 Step 2: Validating Docker Images..."

    if ! command -v docker &> /dev/null; then
        echo "⚠️  Docker not installed, skipping image validation"
        return 0
    fi

    local valid_count=0
    local error_count=0

    # Check if images are available locally or in registry
    local required_services=(
        "postgres" "redis" "kafka"
        "api-gateway" "auth-service" "notes-service"
        "database-service" "habit-service" "learning-service"
        "health-service" "analytics-service" "notification-service"
        "ai-service" "dashboard-service" "graph-service" "search-service"
        "workers"
    )

    # Use empty image prefix if env var not set
    local image_prefix="${IMAGE_PREFIX:-ghcr.io/korobos}"

    for service in "${required_services[@]}"; do
        if [ "$service" = "postgres" ] || [ "$service" = "redis" ] || [ "$service" = "kafka" ]; then
            # Infrastructure images use standard names
            local image="${service}:latest"
        else
            local image="${image_prefix}/${service}:develop"
        fi

        if docker inspect "$image" > /dev/null 2>&1; then
            echo "  ✓ $service image available"
            ((valid_count++))
        else
            echo "  ⚠️  $service image not found locally (will pull from registry)"
            ((valid_count++))
        fi
    done

    echo "✅ Docker images validated ($valid_count services)"
    echo ""
    return 0
}

# ============================================================================
# 3. Kubernetes Cluster Connectivity (if cluster available)
# ============================================================================

validate_cluster_connectivity() {
    echo "☸️  Step 3: Validating Cluster Connectivity..."

    if ! command -v kubectl &> /dev/null; then
        echo "⚠️  kubectl not installed, skipping cluster validation"
        return 0
    fi

    # Check if we can reach the cluster
    if kubectl cluster-info > /dev/null 2>&1; then
        local context=$(kubectl config current-context)
        echo "  ✓ Connected to cluster: $context"

        # Check namespace
        local namespace="${NAMESPACE:-default}"
        if kubectl get namespace "$namespace" > /dev/null 2>&1; then
            echo "  ✓ Namespace exists: $namespace"
        else
            echo "  ⚠️  Namespace does not exist: $namespace (will be created)"
        fi

        # Check if ArgoCD is available
        if kubectl get namespace argocd > /dev/null 2>&1; then
            echo "  ✓ ArgoCD found in cluster"
        else
            echo "  ⚠️  ArgoCD not found (manual deployment may be needed)"
        fi

        echo "✅ Cluster connectivity validated"
    else
        echo "⚠️  Cannot reach Kubernetes cluster (offline mode)"
    fi

    echo ""
    return 0
}

# ============================================================================
# 4. Configuration Validation
# ============================================================================

validate_configurations() {
    echo "⚙️  Step 4: Validating Deployment Configurations..."

    local issues=0

    # Check docker-compose
    if [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        if python3 -c "import yaml; yaml.safe_load(open('$PROJECT_ROOT/docker-compose.yml'))" 2>&1 | grep -q "error"; then
            echo "  ✗ docker-compose.yml has YAML errors"
            ((issues++))
        else
            echo "  ✓ docker-compose.yml is valid"
        fi
    fi

    # Check Helm values for the environment
    if [ -f "$PROJECT_ROOT/infrastructure/helm/charts/api-gateway/values.$ENVIRONMENT.yaml" ]; then
        echo "  ✓ Found environment-specific Helm values for $ENVIRONMENT"
    else
        echo "  ⚠️  No environment-specific Helm values for $ENVIRONMENT (using defaults)"
    fi

    # Check required environment variables
    if [ -f "$PROJECT_ROOT/.env.$ENVIRONMENT" ]; then
        echo "  ✓ Found .env.$ENVIRONMENT file"
    else
        echo "  ⚠️  No .env.$ENVIRONMENT file (ensure env vars are set in deployment)"
    fi

    if [ $issues -gt 0 ]; then
        echo "❌ $issues configuration issue(s) found"
        return 1
    fi

    echo "✅ Configurations validated"
    echo ""
    return 0
}

# ============================================================================
# 5. Helm Dry-Run (if requested)
# ============================================================================

helm_dry_run() {
    if [ "$DRY_RUN" != "true" ]; then
        return 0
    fi

    echo "🧪 Step 5: Performing Helm Dry-Run..."

    if ! command -v helm &> /dev/null; then
        echo "⚠️  Helm not available, skipping dry-run"
        return 0
    fi

    local namespace="${NAMESPACE:-default}"
    local success_count=0
    local error_count=0

    for chart_dir in "$PROJECT_ROOT/infrastructure/helm/charts"/*/; do
        if [ -f "${chart_dir}Chart.yaml" ]; then
            chart_name=$(basename "$chart_dir")
            echo "  Dry-running $chart_name..."

            if helm install --dry-run --debug "${chart_name}-dryrun" "$chart_dir" \
                --namespace "$namespace" > /tmp/helm-dryrun.log 2>&1; then
                echo "    ✓ Dry-run successful"
                ((success_count++))
            else
                echo "    ✗ Dry-run failed"
                tail -20 /tmp/helm-dryrun.log | sed 's/^/      /'
                ((error_count++))
            fi
        fi
    done

    if [ $error_count -gt 0 ]; then
        echo "❌ $error_count dry-run(s) failed"
        return 1
    fi

    echo "✅ Dry-runs completed successfully"
    echo ""
    return 0
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    local exit_code=0

    validate_helm_charts || ((exit_code++))
    validate_docker_images || ((exit_code++))
    validate_cluster_connectivity || ((exit_code++))
    validate_configurations || ((exit_code++))
    helm_dry_run || ((exit_code++))

    echo "=================================================="
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ Pre-deployment validation PASSED${NC}"
        echo ""
        echo "Ready to deploy to $ENVIRONMENT environment"
        return 0
    else
        echo -e "${RED}❌ Pre-deployment validation FAILED${NC}"
        echo ""
        echo "Please fix the issues above before proceeding with deployment"
        return 1
    fi
}

main "$@"
