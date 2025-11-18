#!/bin/bash

# =============================================================================
# Portfolio Tracker - Health Check Script
# =============================================================================
# This script checks the health status of all services
# =============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/volume1/docker/portfolio"

# Functions
success() {
    echo -e "${GREEN}✓${NC} $1"
}

fail() {
    echo -e "${RED}✗${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check Docker
check_docker() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Docker Status"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if command -v docker &> /dev/null; then
        success "Docker is installed"
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | sed 's/,//')
        info "Version: $DOCKER_VERSION"
    else
        fail "Docker is not installed"
        return 1
    fi
}

# Check containers
check_containers() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Container Status"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    cd "$PROJECT_DIR"
    
    CONTAINERS=("portfolio_mongodb" "portfolio_redis" "portfolio_django" "portfolio_celery_worker" "portfolio_celery_beat" "portfolio_frontend")
    
    RUNNING_COUNT=0
    for container in "${CONTAINERS[@]}"; do
        if docker ps | grep -q "$container"; then
            success "$container is running"
            RUNNING_COUNT=$((RUNNING_COUNT + 1))
        else
            fail "$container is not running"
        fi
    done
    
    echo ""
    info "Running containers: $RUNNING_COUNT/${#CONTAINERS[@]}"
}

# Check MongoDB
check_mongodb() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  MongoDB Health"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    cd "$PROJECT_DIR"
    
    if docker-compose -f docker-compose.prod.yml exec -T mongodb mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
        success "MongoDB is responding"
        
        # Get database stats
        DB_SIZE=$(docker-compose -f docker-compose.prod.yml exec -T mongodb mongosh --quiet --eval "db.stats().dataSize" portfolio 2>/dev/null | tail -1)
        if [ ! -z "$DB_SIZE" ]; then
            DB_SIZE_MB=$((DB_SIZE / 1024 / 1024))
            info "Database size: ${DB_SIZE_MB}MB"
        fi
    else
        fail "MongoDB is not responding"
    fi
}

# Check Redis
check_redis() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Redis Health"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    cd "$PROJECT_DIR"
    
    # Source .env for password
    if [ -f "$PROJECT_DIR/.env" ]; then
        set -a
        source "$PROJECT_DIR/.env"
        set +a
    fi
    
    if docker-compose -f docker-compose.prod.yml exec -T redis redis-cli -a "$REDIS_PASSWORD" PING 2>/dev/null | grep -q "PONG"; then
        success "Redis is responding"
        
        # Get memory usage
        MEMORY=$(docker-compose -f docker-compose.prod.yml exec -T redis redis-cli -a "$REDIS_PASSWORD" INFO memory 2>/dev/null | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')
        if [ ! -z "$MEMORY" ]; then
            info "Memory usage: $MEMORY"
        fi
    else
        fail "Redis is not responding"
    fi
}

# Check Django
check_django() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Django API Health"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if curl -f -s http://localhost:8000/api/v1/health/ &> /dev/null; then
        success "Django API is responding"
        
        RESPONSE=$(curl -s http://localhost:8000/api/v1/health/)
        echo "$RESPONSE" | grep -q '"status":"healthy"' && info "Health check: healthy"
    else
        fail "Django API is not responding"
        warning "API may still be starting up"
    fi
}

# Check Celery
check_celery() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Celery Worker Health"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    cd "$PROJECT_DIR"
    
    if docker logs portfolio_celery_worker 2>&1 | tail -20 | grep -q "ready"; then
        success "Celery worker is running"
    else
        warning "Celery worker status unclear"
    fi
    
    if docker logs portfolio_celery_beat 2>&1 | tail -20 | grep -q "beat"; then
        success "Celery beat scheduler is running"
    else
        warning "Celery beat status unclear"
    fi
}

# Check Frontend
check_frontend() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Frontend Health"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if curl -f -s http://localhost:8080/health &> /dev/null; then
        success "Frontend is responding"
    else
        fail "Frontend is not responding"
    fi
    
    if curl -f -s http://localhost:8080/ &> /dev/null; then
        success "React app is accessible"
    else
        fail "React app is not accessible"
    fi
}

# Check disk space
check_disk_space() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Disk Space"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    DISK_USAGE=$(df -h /volume1 | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$DISK_USAGE" -lt 80 ]; then
        success "Disk usage: ${DISK_USAGE}%"
    elif [ "$DISK_USAGE" -lt 90 ]; then
        warning "Disk usage: ${DISK_USAGE}% (consider cleanup)"
    else
        fail "Disk usage: ${DISK_USAGE}% (critical - cleanup required)"
    fi
    
    # Show Docker volumes
    echo ""
    info "Docker volumes:"
    docker volume ls | grep portfolio
}

# Check memory
check_memory() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Memory Usage"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep portfolio
}

# Check recent logs for errors
check_errors() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Recent Errors"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    cd "$PROJECT_DIR"
    
    ERROR_COUNT=$(docker-compose -f docker-compose.prod.yml logs --tail=100 2>&1 | grep -i "error" | wc -l)
    
    if [ "$ERROR_COUNT" -eq 0 ]; then
        success "No recent errors found"
    else
        warning "$ERROR_COUNT error(s) found in recent logs"
        echo ""
        info "Last 5 errors:"
        docker-compose -f docker-compose.prod.yml logs --tail=100 2>&1 | grep -i "error" | tail -5
    fi
}

# Summary
show_summary() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Quick Commands"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    info "View logs:"
    echo "  docker-compose -f docker-compose.prod.yml logs -f [service]"
    echo ""
    info "Restart service:"
    echo "  docker-compose -f docker-compose.prod.yml restart [service]"
    echo ""
    info "Access application:"
    echo "  https://portfolio.jitension.synology.me"
    echo ""
}

# Main health check
main() {
    clear
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Portfolio Tracker - Health Check"
    echo "  $(date '+%Y-%m-%d %H:%M:%S')"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    check_docker
    check_containers
    check_mongodb
    check_redis
    check_django
    check_celery
    check_frontend
    check_disk_space
    check_memory
    check_errors
    show_summary
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Health check completed"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

# Run main function
main
