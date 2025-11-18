#!/bin/bash

# =============================================================================
# Local Docker Testing Script
# =============================================================================
# Tests the production Docker setup on your Mac before deploying to NAS
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log() {
    echo -e "${GREEN}[TEST]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

fail() {
    echo -e "${RED}✗${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi
    success "Docker is installed"
    
    if ! command -v docker-compose &> /dev/null; then
        error "docker-compose is not installed"
    fi
    success "docker-compose is installed"
    
    if [ ! -f ".env.test" ]; then
        error ".env.test file not found. Please create it first."
    fi
    success ".env.test file exists"
}

# Copy local env to .env for Docker
setup_env() {
    log "Setting up local test environment..."
    
    if [ -f ".env.local" ]; then
        cp .env.local .env
        success "Copied .env.local to .env"
    else
        cp .env.test .env
        warning "No .env.local found, using .env.test"
    fi
    
    info "Using local test configuration (HTTP-friendly, not for production!)"
}

# Clean up any existing containers
cleanup() {
    log "Cleaning up existing containers..."
    
    docker-compose -f docker-compose.prod.yml down -v 2>/dev/null || true
    success "Cleaned up existing containers"
}

# Build frontend locally
build_frontend() {
    log "Building frontend locally..."
    
    cd frontend
    if npm run build; then
        success "Frontend built successfully"
        cd ..
    else
        fail "Frontend build failed"
        cd ..
        error "Frontend build failed. Check the output above for errors."
    fi
}

# Build images
build_images() {
    log "Building Docker images..."
    info "This may take 5-10 minutes..."
    
    if docker-compose -f docker-compose.prod.yml build --no-cache; then
        success "Images built successfully"
    else
        fail "Image build failed"
        error "Build failed. Check the output above for errors."
    fi
}

# Start services
start_services() {
    log "Starting services..."
    
    if docker-compose -f docker-compose.prod.yml up -d; then
        success "Services started"
    else
        fail "Failed to start services"
        error "Startup failed. Check logs with: docker-compose -f docker-compose.prod.yml logs"
    fi
}

# Wait for services
wait_for_services() {
    log "Waiting for services to be ready..."
    
    info "Waiting for MongoDB (30 seconds)..."
    sleep 30
    
    # Check MongoDB
    if docker-compose -f docker-compose.prod.yml exec -T mongodb mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
        success "MongoDB is ready"
    else
        fail "MongoDB is not responding"
        warning "This might be normal if it's still starting. Check logs."
    fi
    
    info "Waiting for services to stabilize (10 seconds)..."
    sleep 10
}

# Test MongoDB
test_mongodb() {
    log "Testing MongoDB..."
    
    if docker-compose -f docker-compose.prod.yml exec -T mongodb mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
        success "MongoDB connection successful"
    else
        fail "MongoDB connection failed"
        return 1
    fi
}

# Test Redis
test_redis() {
    log "Testing Redis..."
    
    if docker-compose -f docker-compose.prod.yml exec -T redis redis-cli -a test-redis-password-123 PING 2>/dev/null | grep -q "PONG"; then
        success "Redis connection successful"
    else
        fail "Redis connection failed"
        return 1
    fi
}

# Test Django
test_django() {
    log "Testing Django API..."
    
    # Wait a bit more for Django
    sleep 5
    
    if curl -f -s http://localhost:8000/api/v1/health/ &> /dev/null; then
        success "Django API is responding"
    else
        fail "Django API is not responding"
        info "Checking if Django is still starting..."
        docker-compose -f docker-compose.prod.yml logs django | tail -20
        return 1
    fi
}

# Test Frontend
test_frontend() {
    log "Testing Frontend..."
    
    if curl -f -s http://localhost:8080/ &> /dev/null; then
        success "Frontend is responding"
    else
        fail "Frontend is not responding"
        info "Checking frontend logs..."
        docker-compose -f docker-compose.prod.yml logs frontend | tail -20
        return 1
    fi
    
    # Test frontend health endpoint
    if curl -f -s http://localhost:8080/health &> /dev/null; then
        success "Frontend health check passed"
    else
        warning "Frontend health endpoint not responding"
    fi
}

# Check all containers
check_containers() {
    log "Checking container status..."
    
    echo ""
    docker-compose -f docker-compose.prod.yml ps
    echo ""
    
    RUNNING=$(docker-compose -f docker-compose.prod.yml ps -q | wc -l)
    EXPECTED=6
    
    if [ "$RUNNING" -eq "$EXPECTED" ]; then
        success "All $EXPECTED containers are running"
    else
        warning "Expected $EXPECTED containers, but only $RUNNING are running"
    fi
}

# Show logs summary
show_logs() {
    log "Recent logs from services..."
    echo ""
    
    info "Django logs:"
    docker-compose -f docker-compose.prod.yml logs --tail=10 django
    
    echo ""
    info "Frontend logs:"
    docker-compose -f docker-compose.prod.yml logs --tail=10 frontend
}

# Run all tests
run_tests() {
    log "========================================="
    log "Running Production Docker Tests"
    log "========================================="
    echo ""
    
    check_prerequisites
    echo ""
    
    read -p "This will stop any running containers. Continue? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        error "Test cancelled by user"
    fi
    
    setup_env
    cleanup
    build_images
    start_services
    wait_for_services
    
    echo ""
    log "Running health checks..."
    echo ""
    
    FAILED=0
    
    test_mongodb || FAILED=$((FAILED + 1))
    test_redis || FAILED=$((FAILED + 1))
    test_django || FAILED=$((FAILED + 1))
    test_frontend || FAILED=$((FAILED + 1))
    
    echo ""
    check_containers
    echo ""
    
    if [ $FAILED -eq 0 ]; then
        log "========================================="
        success "All tests passed! ✓"
        log "========================================="
        echo ""
        info "Services are running:"
        echo "  - Frontend: http://localhost:8080"
        echo "  - Django API: http://localhost:8000"
        echo "  - Django Admin: http://localhost:8000/admin"
        echo ""
        info "Next steps:"
        echo "  1. Open http://localhost:8080 in your browser"
        echo "  2. Verify the frontend loads"
        echo "  3. Check the browser console for errors"
        echo "  4. Try logging in (create superuser first)"
        echo ""
        info "To create a superuser:"
        echo "  docker-compose -f docker-compose.prod.yml exec django python manage.py createsuperuser"
        echo ""
        info "To stop services:"
        echo "  docker-compose -f docker-compose.prod.yml down"
        echo ""
        info "To view logs:"
        echo "  docker-compose -f docker-compose.prod.yml logs -f [service]"
    else
        log "========================================="
        fail "$FAILED test(s) failed"
        log "========================================="
        echo ""
        show_logs
        echo ""
        warning "Some services failed. Check logs above for details."
        info "Common issues:"
        echo "  - Services still starting (wait a bit longer)"
        echo "  - Port conflicts (check if ports 8000, 8080 are in use)"
        echo "  - Build errors (check build output above)"
        echo ""
        info "To debug:"
        echo "  docker-compose -f docker-compose.prod.yml logs [service]"
    fi
}

# Cleanup function
cleanup_and_exit() {
    echo ""
    read -p "Stop all containers and clean up? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Stopping containers..."
        docker-compose -f docker-compose.prod.yml down
        success "Containers stopped"
        
        # Remove test .env
        if [ -f ".env" ]; then
            rm .env
            info "Removed test .env file"
        fi
    else
        info "Containers left running. Stop manually with:"
        echo "  docker-compose -f docker-compose.prod.yml down"
    fi
}

# Main execution
main() {
    run_tests
    
    echo ""
    cleanup_and_exit
}

# Run main function
main
