#!/bin/bash
# APEX Docker Helper Script
# Usage: bash docker-helper.sh [command]

set -e

COMPOSE_FILE="docker-compose.apex.standalone.yml"
CONTAINER_NAME="apex-api-server"
IMAGE_NAME="apex"
IMAGE_TAG="latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}========================================${NC}\n"
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Build image
build() {
    print_header "Building APEX Docker Image"
    docker build -f Dockerfile.apex.standalone -t ${IMAGE_NAME}:${IMAGE_TAG} .
    print_success "Image built: ${IMAGE_NAME}:${IMAGE_TAG}"
}

# Start with compose
start() {
    print_header "Starting APEX Container with Docker Compose"
    print_info "Using compose file: ${COMPOSE_FILE}"
    
    if [ ! -f ".env" ]; then
        print_info "No .env file found. Copy from .env.example for email support"
        cp .env.example .env
    fi
    
    docker-compose -f ${COMPOSE_FILE} up -d
    print_success "Container started"
    print_info "API available at: http://localhost:8000"
    print_info "Documentation at: http://localhost:8000/docs"
}

# Stop container
stop() {
    print_header "Stopping APEX Container"
    docker-compose -f ${COMPOSE_FILE} down
    print_success "Container stopped"
}

# View logs
logs() {
    print_header "APEX Container Logs (live)"
    docker-compose -f ${COMPOSE_FILE} logs -f ${CONTAINER_NAME}
}

# Health check
health() {
    print_header "APEX Health Check"
    RESPONSE=$(curl -s http://localhost:8000/health)
    echo "Response: $RESPONSE"
    
    if echo "$RESPONSE" | grep -q "healthy"; then
        print_success "Container is healthy"
    else
        print_error "Container health check failed"
    fi
}

# Container stats
stats() {
    print_header "Container Resource Usage"
    docker stats ${CONTAINER_NAME} --no-stream
}

# Shell access
shell() {
    print_header "Opening Container Shell"
    docker-compose -f ${COMPOSE_FILE} exec ${CONTAINER_NAME} /bin/bash
}

# Test email
test_email() {
    print_header "Testing Email Integration"
    
    print_info "Sending test email action..."
    curl -X POST http://localhost:8000/step \
        -H "Content-Type: application/json" \
        -d '{
            "action": {
                "action_type": "email",
                "recipient_id": 1,
                "subject": "Docker Test Email",
                "body": "Testing APEX email integration in Docker",
                "send_real": false
            }
        }'
    print_success "Test email sent"
}

# Reset environment
reset() {
    print_header "Resetting APEX Environment"
    curl -X POST http://localhost:8000/reset \
        -H "Content-Type: application/json" \
        -d '{"seed": 42, "max_episode_steps": 100}'
    print_success "Environment reset"
}

# Full cleanup
clean() {
    print_header "Cleaning Up APEX Docker Setup"
    docker-compose -f ${COMPOSE_FILE} down -v
    print_info "Removing image..."
    docker rmi ${IMAGE_NAME}:${IMAGE_TAG}
    print_success "Cleanup complete"
}

# Rebuild and restart
rebuild() {
    print_header "Rebuilding and Restarting APEX"
    stop
    build
    start
}

# Show status
status() {
    print_header "APEX Docker Status"
    docker-compose -f ${COMPOSE_FILE} ps
}

# Show help
help() {
    cat << EOF
APEX Docker Helper Script

Usage: bash docker-helper.sh [command]

Commands:
  build       - Build APEX Docker image
  start       - Start APEX container (builds if needed)
  stop        - Stop APEX container
  restart     - Restart APEX container
  rebuild     - Rebuild image and restart container
  status      - Show container status
  logs        - View live container logs
  health      - Check container health
  stats       - Show container resource usage
  shell       - Open shell in container
  test-email  - Test email integration
  reset       - Reset APEX environment
  clean       - Stop and remove everything
  help        - Show this help message

Examples:
  bash docker-helper.sh build      # Build image
  bash docker-helper.sh start      # Start container
  bash docker-helper.sh logs       # View logs
  bash docker-helper.sh status     # Check status

EOF
}

# Main
case "${1:-help}" in
    build)      build ;;
    start)      build && start ;;
    stop)       stop ;;
    restart)    stop && start ;;
    rebuild)    rebuild ;;
    status)     status ;;
    logs)       logs ;;
    health)     health ;;
    stats)      stats ;;
    shell)      shell ;;
    test-email) test_email ;;
    reset)      reset ;;
    clean)      clean ;;
    help)       help ;;
    *)
        print_error "Unknown command: $1"
        help
        exit 1
        ;;
esac
