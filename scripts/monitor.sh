#!/bin/bash

# Monitoring Script for Sistema de Registro de Patrimonio
# This script monitors system health and sends alerts

set -e

# Configuration
ALERT_EMAIL=${ALERT_EMAIL:-"admin@your-domain.com"}
LOG_FILE="./logs/monitor.log"
HEALTH_URL="http://localhost/health/detailed/"

# Create log file if it doesn't exist
mkdir -p logs
touch $LOG_FILE

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a $LOG_FILE
}

# Function to send alert email
send_alert() {
    local subject="$1"
    local message="$2"
    
    if command -v mail &> /dev/null; then
        echo "$message" | mail -s "$subject" $ALERT_EMAIL
        log_message "Alert sent: $subject"
    else
        log_message "Cannot send alert - mail command not available: $subject"
    fi
}

# Check Docker containers
check_containers() {
    log_message "Checking Docker containers..."
    
    local containers=("patrimonio_web_1" "patrimonio_db_1" "patrimonio_redis_1" "patrimonio_nginx_1" "patrimonio_celery_1")
    local failed_containers=()
    
    for container in "${containers[@]}"; do
        if ! docker ps --format "table {{.Names}}" | grep -q "$container"; then
            failed_containers+=("$container")
        fi
    done
    
    if [ ${#failed_containers[@]} -gt 0 ]; then
        local message="The following containers are not running: ${failed_containers[*]}"
        log_message "ERROR: $message"
        send_alert "Container Alert - Sistema Patrimonio" "$message"
        return 1
    else
        log_message "All containers are running"
        return 0
    fi
}

# Check application health
check_health() {
    log_message "Checking application health..."
    
    local response=$(curl -s -w "%{http_code}" -o /tmp/health_response.json "$HEALTH_URL" || echo "000")
    
    if [ "$response" = "200" ]; then
        log_message "Health check passed"
        return 0
    else
        local message="Health check failed with status: $response"
        log_message "ERROR: $message"
        
        if [ -f /tmp/health_response.json ]; then
            local details=$(cat /tmp/health_response.json)
            message="$message\nDetails: $details"
        fi
        
        send_alert "Health Check Alert - Sistema Patrimonio" "$message"
        return 1
    fi
}

# Check disk space
check_disk_space() {
    log_message "Checking disk space..."
    
    local usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$usage" -gt 90 ]; then
        local message="Disk usage is at ${usage}% - critically high!"
        log_message "ERROR: $message"
        send_alert "Disk Space Alert - Sistema Patrimonio" "$message"
        return 1
    elif [ "$usage" -gt 80 ]; then
        local message="Disk usage is at ${usage}% - warning level"
        log_message "WARNING: $message"
        send_alert "Disk Space Warning - Sistema Patrimonio" "$message"
        return 1
    else
        log_message "Disk usage is at ${usage}% - normal"
        return 0
    fi
}

# Check memory usage
check_memory() {
    log_message "Checking memory usage..."
    
    local memory_info=$(free | grep Mem)
    local total=$(echo $memory_info | awk '{print $2}')
    local used=$(echo $memory_info | awk '{print $3}')
    local usage=$((used * 100 / total))
    
    if [ "$usage" -gt 90 ]; then
        local message="Memory usage is at ${usage}% - critically high!"
        log_message "ERROR: $message"
        send_alert "Memory Alert - Sistema Patrimonio" "$message"
        return 1
    elif [ "$usage" -gt 80 ]; then
        local message="Memory usage is at ${usage}% - warning level"
        log_message "WARNING: $message"
        return 1
    else
        log_message "Memory usage is at ${usage}% - normal"
        return 0
    fi
}

# Check SSL certificate expiration
check_ssl_certificate() {
    log_message "Checking SSL certificate..."
    
    if [ -f "./certbot/conf/live/your-domain.com/fullchain.pem" ]; then
        local expiry_date=$(openssl x509 -enddate -noout -in "./certbot/conf/live/your-domain.com/fullchain.pem" | cut -d= -f2)
        local expiry_timestamp=$(date -d "$expiry_date" +%s)
        local current_timestamp=$(date +%s)
        local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
        
        if [ "$days_until_expiry" -lt 7 ]; then
            local message="SSL certificate expires in $days_until_expiry days!"
            log_message "ERROR: $message"
            send_alert "SSL Certificate Alert - Sistema Patrimonio" "$message"
            return 1
        elif [ "$days_until_expiry" -lt 30 ]; then
            local message="SSL certificate expires in $days_until_expiry days"
            log_message "WARNING: $message"
            return 1
        else
            log_message "SSL certificate expires in $days_until_expiry days - normal"
            return 0
        fi
    else
        log_message "SSL certificate not found - skipping check"
        return 0
    fi
}

# Check backup files
check_backups() {
    log_message "Checking recent backups..."
    
    local backup_dir="./backups"
    local latest_backup=$(find $backup_dir -name "db_backup_*.sql.gz" -mtime -1 | head -1)
    
    if [ -z "$latest_backup" ]; then
        local message="No recent database backup found (within 24 hours)"
        log_message "WARNING: $message"
        send_alert "Backup Warning - Sistema Patrimonio" "$message"
        return 1
    else
        log_message "Recent backup found: $(basename $latest_backup)"
        return 0
    fi
}

# Main monitoring function
main() {
    log_message "Starting system monitoring..."
    
    local checks_passed=0
    local total_checks=6
    
    check_containers && ((checks_passed++))
    check_health && ((checks_passed++))
    check_disk_space && ((checks_passed++))
    check_memory && ((checks_passed++))
    check_ssl_certificate && ((checks_passed++))
    check_backups && ((checks_passed++))
    
    log_message "Monitoring completed: $checks_passed/$total_checks checks passed"
    
    if [ "$checks_passed" -eq "$total_checks" ]; then
        log_message "All systems operational"
        exit 0
    else
        log_message "Some checks failed - see alerts"
        exit 1
    fi
}

# Run monitoring
main