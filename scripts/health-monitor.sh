#!/bin/bash

# 2KCompLeague Discord Bot - Health Monitor
# This script continuously monitors the health of the bot and takes action if issues are detected

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
HEALTH_ENDPOINT="http://localhost:8080/health"
CHECK_INTERVAL=60  # Check every 60 seconds
MAX_FAILURES=3     # Maximum consecutive failures before action
LOG_FILE="$PROJECT_DIR/logs/health-monitor.log"
ALERT_SCRIPT="$SCRIPT_DIR/send-alert.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Initialize
FAILURE_COUNT=0
LAST_CHECK_TIME=$(date +%s)

# Logging function
log() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${BLUE}[$timestamp]${NC} $message" | tee -a "$LOG_FILE"
}

error() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${RED}[ERROR][$timestamp]${NC} $message" | tee -a "$LOG_FILE"
}

success() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${GREEN}[SUCCESS][$timestamp]${NC} $message" | tee -a "$LOG_FILE"
}

warning() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${YELLOW}[WARNING][$timestamp]${NC} $message" | tee -a "$LOG_FILE"
}

# Create log directory
mkdir -p "$(dirname "$LOG_FILE")"

# Health check function
check_health() {
    local response
    local status_code
    
    # Make HTTP request to health endpoint
    response=$(curl -s -w "%{http_code}" "$HEALTH_ENDPOINT" 2>/dev/null || echo "000")
    status_code="${response: -3}"
    
    if [[ "$status_code" == "200" ]]; then
        # Parse health status from response
        local health_status
        health_status=$(echo "${response%???}" | jq -r '.status' 2>/dev/null || echo "unknown")
        
        if [[ "$health_status" == "healthy" ]]; then
            success "Health check passed - Status: $health_status"
            FAILURE_COUNT=0
            return 0
        else
            warning "Health check degraded - Status: $health_status"
            FAILURE_COUNT=$((FAILURE_COUNT + 1))
            return 1
        fi
    else
        error "Health check failed - HTTP Status: $status_code"
        FAILURE_COUNT=$((FAILURE_COUNT + 1))
        return 1
    fi
}

# Take action on repeated failures
take_action() {
    local failure_count=$1
    
    log "Taking action after $failure_count consecutive failures"
    
    # Check if containers are running
    if ! docker-compose ps | grep -q "Up"; then
        error "Containers are not running, attempting restart..."
        docker-compose restart
        sleep 30
        return
    fi
    
    # Check container logs for errors
    log "Checking container logs for errors..."
    docker-compose logs --tail=50 discord-bot | grep -i "error\|exception\|traceback" || true
    
    # Attempt container restart
    if [[ $failure_count -ge $MAX_FAILURES ]]; then
        warning "Maximum failures reached, restarting containers..."
        docker-compose restart
        sleep 30
        
        # Check if restart fixed the issue
        if check_health; then
            success "Container restart resolved the issue"
            FAILURE_COUNT=0
        else
            error "Container restart did not resolve the issue"
            send_alert "Critical: Bot health check failed after restart"
        fi
    fi
}

# Send alert function
send_alert() {
    local message="$1"
    
    log "Sending alert: $message"
    
    # Check if alert script exists and is executable
    if [[ -x "$ALERT_SCRIPT" ]]; then
        "$ALERT_SCRIPT" "$message"
    else
        # Fallback: log to syslog
        logger -t "discord-bot-health" "$message"
    fi
}

# Get system metrics
get_system_metrics() {
    local metrics=""
    
    # CPU usage
    local cpu_usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    metrics="$metrics CPU: ${cpu_usage}%"
    
    # Memory usage
    local mem_usage
    mem_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    metrics="$metrics Memory: ${mem_usage}%"
    
    # Disk usage
    local disk_usage
    disk_usage=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
    metrics="$metrics Disk: ${disk_usage}%"
    
    echo "$metrics"
}

# Main monitoring loop
main() {
    log "Starting health monitor for 2KCompLeague Discord Bot"
    log "Health endpoint: $HEALTH_ENDPOINT"
    log "Check interval: ${CHECK_INTERVAL}s"
    log "Max failures: $MAX_FAILURES"
    
    # Trap signals for graceful shutdown
    trap 'log "Health monitor stopped"; exit 0' SIGTERM SIGINT
    
    while true; do
        local current_time=$(date +%s)
        local time_since_last_check=$((current_time - LAST_CHECK_TIME))
        
        # Log system metrics every 5 minutes
        if [[ $time_since_last_check -ge 300 ]]; then
            local system_metrics
            system_metrics=$(get_system_metrics)
            log "System metrics: $system_metrics"
            LAST_CHECK_TIME=$current_time
        fi
        
        # Perform health check
        if check_health; then
            # Health check passed
            if [[ $FAILURE_COUNT -gt 0 ]]; then
                success "Bot recovered after $FAILURE_COUNT failures"
                FAILURE_COUNT=0
            fi
        else
            # Health check failed
            error "Health check failed (consecutive failures: $FAILURE_COUNT)"
            
            # Take action if needed
            take_action $FAILURE_COUNT
        fi
        
        # Sleep until next check
        sleep $CHECK_INTERVAL
    done
}

# Show help
show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    -h, --help          Show this help message
    -e, --endpoint URL  Health check endpoint (default: $HEALTH_ENDPOINT)
    -i, --interval SEC  Check interval in seconds (default: $CHECK_INTERVAL)
    -m, --max-failures  Maximum failures before action (default: $MAX_FAILURES)
    -l, --log-file      Log file path (default: $LOG_FILE)

Examples:
    $0                           # Start monitoring with defaults
    $0 -e http://localhost:9000 # Custom health endpoint
    $0 -i 30                    # Check every 30 seconds
    $0 -m 5                     # Take action after 5 failures

The script will:
1. Continuously monitor the bot's health endpoint
2. Log all health check results
3. Take action on repeated failures (restart containers)
4. Send alerts for critical issues
5. Monitor system resources
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -e|--endpoint)
            HEALTH_ENDPOINT="$2"
            shift 2
            ;;
        -i|--interval)
            CHECK_INTERVAL="$2"
            shift 2
            ;;
        -m|--max-failures)
            MAX_FAILURES="$2"
            shift 2
            ;;
        -l|--log-file)
            LOG_FILE="$2"
            shift 2
            ;;
        *)
            error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Start monitoring
main
