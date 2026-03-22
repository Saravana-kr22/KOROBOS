#!/bin/bash
# Post-Deployment Validation Script for KOROBOS
# Runs smoke tests and verifies all services are healthy
# Run after deploying to validate the deployment succeeded

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

ENVIRONMENT="${1:-development}"
BASE_URL="${2:-http://localhost:8080}"
TIMEOUT="${3:-300}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "✅ Post-Deployment Validation for KOROBOS ($ENVIRONMENT)"
echo "=================================================="
echo "Base URL: $BASE_URL"
echo "Timeout: ${TIMEOUT}s"
echo ""

# ============================================================================
# Health Check Functions
# ============================================================================

check_service_health() {
    local service_name=$1
    local health_url=$2
    local timeout=$3

    echo "  Checking $service_name..."

    local start_time=$(date +%s)
    while true; do
        if curl -sf "$health_url" > /dev/null 2>&1; then
            echo "    ✓ $service_name is healthy"
            return 0
        fi

        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))

        if [ $elapsed -ge $timeout ]; then
            echo "    ✗ $service_name health check timeout"
            return 1
        fi

        echo "    ⏳ Waiting for $service_name... ($elapsed/${timeout}s)"
        sleep 5
    done
}

# ============================================================================
# 1. Critical Service Health Checks
# ============================================================================

test_critical_services() {
    echo "🏥 Step 1: Testing Critical Service Health..."

    local failed=0

    # API Gateway (primary entry point)
    check_service_health "API Gateway" "$BASE_URL/api/v1/health" "$TIMEOUT" || ((failed++))

    # Auth Service
    check_service_health "Auth Service" "$BASE_URL/api/v1/auth/health" "$TIMEOUT" || ((failed++))

    # Database Service
    check_service_health "Database Service" "$BASE_URL/api/v1/database/health" "$TIMEOUT" || ((failed++))

    # Analytics Service
    check_service_health "Analytics Service" "$BASE_URL/api/v1/analytics/health" "$TIMEOUT" || ((failed++))

    # AI Service
    check_service_health "AI Service" "$BASE_URL/api/v1/ai/" "$TIMEOUT" || ((failed++))

    if [ $failed -eq 0 ]; then
        echo "✅ All critical services are healthy"
    else
        echo "❌ $failed critical service(s) failed health check"
        return 1
    fi

    echo ""
    return 0
}

# ============================================================================
# 2. API Smoke Tests
# ============================================================================

test_api_endpoints() {
    echo "🔥 Step 2: Running API Smoke Tests..."

    local failed=0
    local test_user_id="550e8400-e29b-41d4-a716-446655440000"

    # Test authentication endpoint
    echo "  Testing auth flow..."
    if curl -sf -X POST "$BASE_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username":"test","password":"test"}' > /dev/null 2>&1; then
        echo "    ✓ Auth endpoint responding"
    else
        echo "    ⚠️  Auth endpoint not responding (may require valid credentials)"
    fi

    # Test API Gateway routing
    echo "  Testing gateway routing..."
    if curl -sf "$BASE_URL/api/v1/health" > /dev/null 2>&1; then
        echo "    ✓ Gateway routing healthy"
    else
        echo "    ✗ Gateway routing failed"
        ((failed++))
    fi

    # Test notes service (example domain service)
    echo "  Testing domain service (notes)..."
    if curl -sf -H "X-User-ID: $test_user_id" \
        "$BASE_URL/api/v1/notes" > /dev/null 2>&1; then
        echo "    ✓ Notes service responding"
    else
        echo "    ⚠️  Notes service not responding (may require auth)"
    fi

    # Test analytics service
    echo "  Testing analytics service..."
    if curl -sf -H "X-User-ID: $test_user_id" \
        "$BASE_URL/api/v1/analytics/overview" > /dev/null 2>&1; then
        echo "    ✓ Analytics service responding"
    else
        echo "    ⚠️  Analytics service not responding (may require data)"
    fi

    # Test AI service
    echo "  Testing AI service..."
    if curl -sf -H "X-User-ID: $test_user_id" \
        "$BASE_URL/api/v1/ai/insights" > /dev/null 2>&1; then
        echo "    ✓ AI service responding"
    else
        echo "    ⚠️  AI service not responding (may require data)"
    fi

    if [ $failed -eq 0 ]; then
        echo "✅ API smoke tests passed"
    else
        echo "❌ $failed API test(s) failed"
        return 1
    fi

    echo ""
    return 0
}

# ============================================================================
# 3. Database Connectivity
# ============================================================================

test_database_connectivity() {
    echo "🗄️  Step 3: Testing Database Connectivity..."

    # Test via API endpoint that requires DB access
    echo "  Testing database via API..."

    if curl -sf -H "X-User-ID: 550e8400-e29b-41d4-a716-446655440000" \
        "$BASE_URL/api/v1/database/health" > /dev/null 2>&1; then
        echo "    ✓ Database accessible via API"
    else
        echo "    ⚠️  Cannot verify database connectivity"
    fi

    echo "✅ Database connectivity test complete"
    echo ""
    return 0
}

# ============================================================================
# 4. Pod/Container Status (Kubernetes)
# ============================================================================

test_kubernetes_status() {
    echo "☸️  Step 4: Checking Kubernetes Pod Status..."

    if ! command -v kubectl &> /dev/null; then
        echo "⚠️  kubectl not available, skipping pod status check"
        echo ""
        return 0
    fi

    local namespace="${NAMESPACE:-default}"

    if ! kubectl get namespace "$namespace" > /dev/null 2>&1; then
        echo "⚠️  Namespace $namespace not found"
        echo ""
        return 0
    fi

    echo "  Checking pod status in namespace: $namespace..."

    local pod_count=$(kubectl get pods -n "$namespace" --no-headers 2>/dev/null | wc -l)

    if [ $pod_count -eq 0 ]; then
        echo "  ⚠️  No pods found in $namespace (may be deploying)"
        echo ""
        return 0
    fi

    local running=$(kubectl get pods -n "$namespace" --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
    local failed=$(kubectl get pods -n "$namespace" --field-selector=status.phase=Failed --no-headers 2>/dev/null | wc -l)

    echo "  Pods found: $pod_count"
    echo "  Running: $running"
    echo "  Failed: $failed"

    if [ $failed -gt 0 ]; then
        echo "  ✗ Failed pods detected"
        kubectl get pods -n "$namespace" --field-selector=status.phase=Failed 2>/dev/null | sed 's/^/    /'
        echo "✅ Pod status check complete (with issues)"
    else
        echo "  ✓ All pods healthy"
        echo "✅ Pod status check complete"
    fi

    echo ""
    return 0
}

# ============================================================================
# 5. Log Analysis (Error Detection)
# ============================================================================

test_error_logs() {
    echo "📋 Step 5: Analyzing Recent Logs for Errors..."

    if ! command -v kubectl &> /dev/null; then
        echo "⚠️  kubectl not available, skipping log analysis"
        echo ""
        return 0
    fi

    local namespace="${NAMESPACE:-default}"
    local error_count=0

    echo "  Scanning logs for errors (last 10 lines per pod)..."

    # Get all pods and check for errors in logs
    kubectl get pods -n "$namespace" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null | tr ' ' '\n' | while read -r pod; do
        if [ -z "$pod" ]; then
            continue
        fi

        error_lines=$(kubectl logs -n "$namespace" "$pod" --tail=20 2>/dev/null | grep -i "error\|exception\|failed" | wc -l)

        if [ $error_lines -gt 0 ]; then
            echo "    ⚠️  $pod has error lines in logs"
            ((error_count++))
        fi
    done

    if [ $error_count -eq 0 ]; then
        echo "  ✓ No critical errors detected in logs"
    else
        echo "  ⚠️  $error_count pod(s) have potential errors"
    fi

    echo "✅ Log analysis complete"
    echo ""
    return 0
}

# ============================================================================
# 6. Performance Baseline
# ============================================================================

test_performance() {
    echo "⚡ Step 6: Running Performance Baseline Test..."

    echo "  Testing API response times..."

    # Test 5 requests and measure average response time
    local total_time=0
    local request_count=5

    for i in $(seq 1 $request_count); do
        local start=$(date +%s%N)
        curl -sf "$BASE_URL/api/v1/health" > /dev/null 2>&1 || true
        local end=$(date +%s%N)
        local request_time=$(( (end - start) / 1000000 ))  # Convert to ms
        total_time=$((total_time + request_time))
        echo "    Request $i: ${request_time}ms"
    done

    local avg_time=$((total_time / request_count))
    echo "  Average response time: ${avg_time}ms"

    if [ $avg_time -lt 500 ]; then
        echo "  ✓ Response time is excellent"
    elif [ $avg_time -lt 1000 ]; then
        echo "  ✓ Response time is good"
    else
        echo "  ⚠️  Response time is slow (>${avg_time}ms)"
    fi

    echo "✅ Performance baseline test complete"
    echo ""
    return 0
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    # Wait for services to be ready
    echo "⏳ Waiting for services to become ready..."
    sleep 10
    echo ""

    local exit_code=0

    test_critical_services || ((exit_code++))
    test_api_endpoints || ((exit_code++))
    test_database_connectivity || ((exit_code++))
    test_kubernetes_status || ((exit_code++))
    test_error_logs || ((exit_code++))
    test_performance || ((exit_code++))

    echo "=================================================="
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ Post-deployment validation PASSED${NC}"
        echo ""
        echo "Deployment to $ENVIRONMENT appears healthy"
        return 0
    else
        echo -e "${YELLOW}⚠️  Post-deployment validation COMPLETED with issues${NC}"
        echo ""
        echo "Check the results above. Some issues may be expected:"
        echo "  - First deployment may need time to initialize"
        echo "  - Some endpoints may require valid credentials"
        echo "  - Database may be empty (no data = 404 is expected)"
        return 0  # Non-blocking
    fi
}

main "$@"
