#!/bin/bash

# 2KCompLeague Discord Bot - Alert Script
# This script sends alerts for critical issues

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ALERT_LOG="$PROJECT_DIR/logs/alerts.log"
DISCORD_WEBHOOK_URL="${DISCORD_WEBHOOK_URL:-}"
EMAIL_RECIPIENT="${EMAIL_RECIPIENT:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging function
log() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${BLUE}[$timestamp]${NC} $message" | tee -a "$ALERT_LOG"
}

error() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${RED}[ERROR][$timestamp]${NC} $message" | tee -a "$ALERT_LOG"
}

success() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${GREEN}[SUCCESS][$timestamp]${NC} $message" | tee -a "$ALERT_LOG"
}

# Create log directory
mkdir -p "$(dirname "$ALERT_LOG")"

# Send Discord alert
send_discord_alert() {
    local message="$1"
    
    if [[ -z "$DISCORD_WEBHOOK_URL" ]]; then
        warning "Discord webhook URL not configured, skipping Discord alert"
        return 1
    fi
    
    local payload
    payload=$(cat << EOF
{
    "embeds": [
        {
            "title": "🚨 Bot Alert",
            "description": "$message",
            "color": 15158332,
            "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)",
            "fields": [
                {
                    "name": "Environment",
                    "value": "$(hostname)",
                    "inline": true
                },
                {
                    "name": "Time",
                    "value": "$(date)",
                    "inline": true
                }
            ]
        }
    ]
}
EOF
)
    
    if curl -s -H "Content-Type: application/json" -d "$payload" "$DISCORD_WEBHOOK_URL" > /dev/null; then
        success "Discord alert sent successfully"
        return 0
    else
        error "Failed to send Discord alert"
        return 1
    fi
}

# Send email alert
send_email_alert() {
    local message="$1"
    
    if [[ -z "$EMAIL_RECIPIENT" ]]; then
        warning "Email recipient not configured, skipping email alert"
        return 1
    fi
    
    local subject="[ALERT] 2KCompLeague Discord Bot - $(hostname)"
    local body="
Bot Alert: $message

Time: $(date)
Host: $(hostname)
Environment: $(hostname)

This is an automated alert from the bot health monitoring system.
"
    
    if echo "$body" | mail -s "$subject" "$EMAIL_RECIPIENT" 2>/dev/null; then
        success "Email alert sent successfully"
        return 0
    else
        error "Failed to send email alert"
        return 1
    fi
}

# Send system log alert
send_syslog_alert() {
    local message="$1"
    
    if logger -t "discord-bot-alert" "$message" 2>/dev/null; then
        success "Syslog alert sent successfully"
        return 0
    else
        error "Failed to send syslog alert"
        return 1
    fi
}

# Main alert function
send_alert() {
    local message="$1"
    
    if [[ -z "$message" ]]; then
        error "No message provided for alert"
        exit 1
    fi
    
    log "Sending alert: $message"
    
    # Try different alert methods
    local alert_sent=false
    
    # Try Discord first
    if send_discord_alert "$message"; then
        alert_sent=true
    fi
    
    # Try email
    if send_email_alert "$message"; then
        alert_sent=true
    fi
    
    # Fallback to syslog
    if send_syslog_alert "$message"; then
        alert_sent=true
    fi
    
    if [[ "$alert_sent" == true ]]; then
        success "Alert sent successfully"
    else
        error "Failed to send alert through any method"
        exit 1
    fi
}

# Show help
show_help() {
    cat << EOF
Usage: $0 [OPTIONS] "MESSAGE"

Options:
    -h, --help          Show this help message
    -w, --webhook URL   Discord webhook URL
    -e, --email EMAIL   Email recipient
    -t, --test          Send test alert

Environment Variables:
    DISCORD_WEBHOOK_URL  Discord webhook URL for alerts
    EMAIL_RECIPIENT      Email address for alerts

Examples:
    $0 "Bot is down"                    # Send alert with default methods
    $0 -w "URL" "Test message"         # Send Discord alert
    $0 -e "admin@example.com" "Alert"  # Send email alert
    $0 --test                           # Send test alert

The script will try to send alerts through:
1. Discord webhook (if configured)
2. Email (if configured)
3. System log (fallback)
EOF
}

# Test alert function
send_test_alert() {
    log "Sending test alert..."
    send_alert "This is a test alert from the 2KCompLeague Discord Bot monitoring system."
    success "Test alert sent successfully"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -w|--webhook)
            DISCORD_WEBHOOK_URL="$2"
            shift 2
            ;;
        -e|--email)
            EMAIL_RECIPIENT="$2"
            shift 2
            ;;
        -t|--test)
            send_test_alert
            exit 0
            ;;
        *)
            # Assume this is the message
            MESSAGE="$1"
            shift
            ;;
    esac
done

# Check if message was provided
if [[ -z "$MESSAGE" ]]; then
    error "No message provided. Use -h for help."
    exit 1
fi

# Send the alert
send_alert "$MESSAGE"
