# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo "Cleaning up existing processes on KOROBOS ports..."
if command_exists fuser; then
    fuser -k 8000/tcp 8001/tcp 8002/tcp 8003/tcp 8004/tcp 8005/tcp 8006/tcp 8007/tcp 9000/tcp 3000/tcp 2>/dev/null || true
fi
sleep 1

# Cleanup function to kill all background processes
cleanup() {
    echo ""
    echo "Stopping KOROBOS development servers..."
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null
        fi
    done
    exit 0
}

# Set up trap for cleanup
trap cleanup SIGINT SIGTERM

echo "Starting KOROBOS development servers..."

# Ensure poetry is in PATH if installed in default local location
export PATH="$HOME/.local/bin:$PATH"

# Start Everything via Docker Compose
echo "Starting all KOROBOS services and infrastructure..."
docker compose up -d --build

echo ""
echo "=================================================="
echo "🚀 KOROBOS is fully containerized and running!"
echo "=================================================="
echo "📦 Infrastructure:"
echo "  - Postgres: localhost:5432"
echo "  - Redis: localhost:6379"
echo "  - Kafka (TLS/SASL): localhost:9093"
echo "  - Kafka Exporter: http://localhost:9308/metrics"
echo "  - Meilisearch: localhost:7700"
echo "  - MinIO: localhost:9000 (UI: 9001)"
echo ""
echo "🌐 Applications:"
echo "  - Frontend UI    : http://localhost:3000"
echo "  - API Gateway    : http://localhost:8080/health"
echo "  - Auth Docs      : http://localhost:8000/docs"
echo "  - Workers        : analytics, notification, search, ai"
echo "=================================================="
echo "Run 'make stop' to gracefully shut down the environment."

# Wait forever (or until Ctrl+C)
tail -f /dev/null
