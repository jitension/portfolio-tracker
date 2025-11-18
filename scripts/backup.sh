#!/bin/bash

# =============================================================================
# Portfolio Tracker - Backup Script
# =============================================================================
# This script creates a complete backup of the application and database
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/volume1/docker/portfolio"
BACKUP_DIR="/volume1/backups/portfolio"
RETENTION_DAYS=30
LOG_FILE="$PROJECT_DIR/logs/backup.log"

# Functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

# Create backup directory
prepare_backup() {
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_NAME="portfolio_backup_$TIMESTAMP"
    BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
    
    mkdir -p "$BACKUP_PATH"
    
    log "Backup directory created: $BACKUP_PATH"
}

# Backup MongoDB
backup_mongodb() {
    log "Backing up MongoDB..."
    
    # Source environment variables
    if [ -f "$PROJECT_DIR/.env" ]; then
        set -a
        source "$PROJECT_DIR/.env"
        set +a
    else
        error ".env file not found"
    fi
    
    # Create MongoDB dump
    docker-compose -f "$PROJECT_DIR/docker-compose.prod.yml" exec -T mongodb mongodump \
        --uri="mongodb://${MONGO_ROOT_USER}:${MONGO_ROOT_PASSWORD}@localhost:27017/portfolio?authSource=admin" \
        --out="/tmp/backup_$TIMESTAMP" \
        --gzip
    
    # Copy from container to host
    docker cp portfolio_mongodb:/tmp/backup_$TIMESTAMP "$BACKUP_PATH/mongodb"
    
    # Cleanup inside container
    docker-compose -f "$PROJECT_DIR/docker-compose.prod.yml" exec -T mongodb rm -rf /tmp/backup_$TIMESTAMP
    
    log "MongoDB backup completed ✓"
}

# Backup .env file
backup_env() {
    log "Backing up environment configuration..."
    
    if [ -f "$PROJECT_DIR/.env" ]; then
        cp "$PROJECT_DIR/.env" "$BACKUP_PATH/.env.bak"
        chmod 600 "$BACKUP_PATH/.env.bak"
        log "Environment file backed up ✓"
    else
        warning ".env file not found, skipping"
    fi
}

# Backup docker-compose configuration
backup_config() {
    log "Backing up Docker configuration..."
    
    cp "$PROJECT_DIR/docker-compose.prod.yml" "$BACKUP_PATH/docker-compose.prod.yml.bak"
    
    log "Docker configuration backed up ✓"
}

# Compress backup
compress_backup() {
    log "Compressing backup..."
    
    cd "$BACKUP_DIR"
    tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
    
    # Remove uncompressed directory
    rm -rf "$BACKUP_NAME"
    
    BACKUP_SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
    log "Backup compressed: ${BACKUP_NAME}.tar.gz ($BACKUP_SIZE) ✓"
}

# Cleanup old backups
cleanup_old_backups() {
    log "Cleaning up backups older than $RETENTION_DAYS days..."
    
    DELETED_COUNT=$(find "$BACKUP_DIR" -name "portfolio_backup_*.tar.gz" -mtime +$RETENTION_DAYS -type f | wc -l)
    
    if [ "$DELETED_COUNT" -gt 0 ]; then
        find "$BACKUP_DIR" -name "portfolio_backup_*.tar.gz" -mtime +$RETENTION_DAYS -type f -delete
        log "Deleted $DELETED_COUNT old backup(s) ✓"
    else
        log "No old backups to clean up"
    fi
}

# Verify backup
verify_backup() {
    log "Verifying backup integrity..."
    
    cd "$BACKUP_DIR"
    if tar -tzf "${BACKUP_NAME}.tar.gz" > /dev/null 2>&1; then
        log "Backup verification passed ✓"
    else
        error "Backup verification failed - archive may be corrupted"
    fi
}

# List recent backups
list_backups() {
    log "Recent backups:"
    echo ""
    ls -lh "$BACKUP_DIR"/portfolio_backup_*.tar.gz 2>/dev/null | tail -10 || info "No backups found"
    echo ""
    
    TOTAL_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)
    info "Total backup size: $TOTAL_SIZE"
}

# Main backup flow
main() {
    log "========================================="
    log "Portfolio Tracker - Backup"
    log "========================================="
    
    prepare_backup
    backup_mongodb
    backup_env
    backup_config
    compress_backup
    verify_backup
    cleanup_old_backups
    
    echo ""
    list_backups
    
    log "========================================="
    log "Backup completed successfully! ✓"
    log "========================================="
    
    info "Backup location: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
    info "To restore this backup:"
    echo "  1. Extract: tar -xzf ${BACKUP_NAME}.tar.gz"
    echo "  2. Stop services: docker-compose -f docker-compose.prod.yml down"
    echo "  3. Restore MongoDB data"
    echo "  4. Restart services: docker-compose -f docker-compose.prod.yml up -d"
}

# Run main function
main
