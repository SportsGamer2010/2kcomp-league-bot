#!/bin/bash

# 2KCompLeague Discord Bot Deployment Script
# This script handles the deployment of the Discord bot to production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="2kcomp-league-bot"
DOCKER_IMAGE="2kcomp-league-bot"
CONTAINER_NAME="2kcomp-league-bot-prod"
COMPOSE_FILE="docker-compose.prod.yml"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    log_success "Docker is running"
}

# Check if required files exist
check_files() {
    local required_files=(".env" "Dockerfile" "$COMPOSE_FILE")
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "Required file $file not found"
            exit 1
        fi
    done
    log_success "All required files found"
}

# Backup existing data
backup_data() {
    if [ -d "data" ]; then
        log_info "Creating backup of existing data..."
        timestamp=$(date +%Y%m%d_%H%M%S)
        tar -czf "backup_${timestamp}.tar.gz" data/
        log_success "Backup created: backup_${timestamp}.tar.gz"
    fi
}

# Pull latest changes
pull_changes() {
    log_info "Pulling latest changes from Git..."
    git pull origin main
    log_success "Latest changes pulled"
}

# Build Docker image
build_image() {
    log_info "Building Docker image..."
    docker build -t "$DOCKER_IMAGE:latest" .
    log_success "Docker image built successfully"
}

# Stop existing containers
stop_containers() {
    log_info "Stopping existing containers..."
    docker-compose -f "$COMPOSE_FILE" down || true
    log_success "Existing containers stopped"
}

# Start new containers
start_containers() {
    log_info "Starting new containers..."
    docker-compose -f "$COMPOSE_FILE" up -d
    log_success "Containers started successfully"
}

# Wait for health check
wait_for_health() {
    log_info "Waiting for bot to be healthy..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f "$COMPOSE_FILE" ps | grep -q "healthy"; then
            log_success "Bot is healthy and ready"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts - Bot not ready yet, waiting..."
        sleep 10
        ((attempt++))
    done
    
    log_warning "Bot health check timed out, but deployment may still be successful"
}

# Show logs
show_logs() {
    log_info "Showing recent logs..."
    docker-compose -f "$COMPOSE_FILE" logs --tail=50
}

# Cleanup old images
cleanup() {
    log_info "Cleaning up old Docker images..."
    docker image prune -f
    log_success "Cleanup completed"
}

# Main deployment function
deploy() {
    log_info "Starting deployment of $PROJECT_NAME..."
    
    check_docker
    check_files
    backup_data
    pull_changes
    build_image
    stop_containers
    start_containers
    wait_for_health
    show_logs
    cleanup
    
    log_success "Deployment completed successfully!"
    log_info "Bot should be running and ready to use"
}

# Rollback function
rollback() {
    log_info "Rolling back to previous version..."
    
    # Find the most recent backup
    local latest_backup=$(ls -t backup_*.tar.gz 2>/dev/null | head -n1)
    
    if [ -z "$latest_backup" ]; then
        log_error "No backup files found for rollback"
        exit 1
    fi
    
    log_info "Using backup: $latest_backup"
    
    # Stop current containers
    stop_containers
    
    # Restore data
    if [ -d "data" ]; then
        rm -rf data
    fi
    tar -xzf "$latest_backup"
    
    # Start containers with previous version
    start_containers
    wait_for_health
    
    log_success "Rollback completed successfully"
}

# Show usage
usage() {
    echo "Usage: $0 [deploy|rollback|status|logs]"
    echo ""
    echo "Commands:"
    echo "  deploy   - Deploy the bot to production"
    echo "  rollback - Rollback to previous version"
    echo "  status   - Show deployment status"
    echo "  logs     - Show bot logs"
    echo ""
}

# Show status
show_status() {
    log_info "Deployment Status:"
    docker-compose -f "$COMPOSE_FILE" ps
}

# Show logs
show_logs_only() {
    docker-compose -f "$COMPOSE_FILE" logs -f
}

# Main script logic
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    rollback)
        rollback
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs_only
        ;;
    *)
        usage
        exit 1
        ;;
esac
