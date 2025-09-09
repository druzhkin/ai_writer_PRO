#!/bin/bash

# AI Writer PRO Backup Script
# This script handles database backup, log rotation, and system maintenance

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/ai-writer-pro}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
ENVIRONMENT="${ENVIRONMENT:-production}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Create backup directory
create_backup_dir() {
    log_info "Creating backup directory: $BACKUP_DIR"
    
    mkdir -p "$BACKUP_DIR"/{database,logs,files,config}
    
    log_success "Backup directory created"
}

# Backup database
backup_database() {
    log_info "Starting database backup..."
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="$BACKUP_DIR/database/ai_writer_pro_${timestamp}.sql"
    
    # Create database backup
    if [ -n "$DATABASE_URL" ]; then
        # Extract database connection details
        local db_host=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
        local db_port=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
        local db_name=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
        local db_user=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
        local db_password=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
        
        # Set password environment variable
        export PGPASSWORD="$db_password"
        
        # Create backup
        pg_dump -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" \
            --verbose --clean --no-owner --no-privileges > "$backup_file"
        
        # Compress backup
        gzip "$backup_file"
        
        log_success "Database backup completed: ${backup_file}.gz"
    else
        log_error "DATABASE_URL not set"
        exit 1
    fi
}

# Backup application logs
backup_logs() {
    log_info "Starting log backup..."
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local log_backup_dir="$BACKUP_DIR/logs/logs_${timestamp}"
    
    mkdir -p "$log_backup_dir"
    
    # Copy application logs
    if [ -d "/var/log/ai-writer-pro" ]; then
        cp -r /var/log/ai-writer-pro/* "$log_backup_dir/"
    fi
    
    # Copy Docker logs
    if command -v docker &> /dev/null; then
        docker logs ai-writer-pro-backend > "$log_backup_dir/backend.log" 2>&1 || true
        docker logs ai-writer-pro-frontend > "$log_backup_dir/frontend.log" 2>&1 || true
        docker logs ai-writer-pro-celery-worker > "$log_backup_dir/celery-worker.log" 2>&1 || true
    fi
    
    # Compress logs
    tar -czf "${log_backup_dir}.tar.gz" -C "$BACKUP_DIR/logs" "logs_${timestamp}"
    rm -rf "$log_backup_dir"
    
    log_success "Log backup completed: ${log_backup_dir}.tar.gz"
}

# Backup uploaded files
backup_files() {
    log_info "Starting file backup..."
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local file_backup_dir="$BACKUP_DIR/files/files_${timestamp}"
    
    mkdir -p "$file_backup_dir"
    
    # Backup uploaded files
    if [ -d "/var/uploads/ai-writer-pro" ]; then
        cp -r /var/uploads/ai-writer-pro/* "$file_backup_dir/"
    fi
    
    # Backup configuration files
    if [ -d "$PROJECT_ROOT/config" ]; then
        cp -r "$PROJECT_ROOT/config" "$file_backup_dir/"
    fi
    
    # Compress files
    tar -czf "${file_backup_dir}.tar.gz" -C "$BACKUP_DIR/files" "files_${timestamp}"
    rm -rf "$file_backup_dir"
    
    log_success "File backup completed: ${file_backup_dir}.tar.gz"
}

# Backup to S3
backup_to_s3() {
    log_info "Uploading backups to S3..."
    
    if [ -n "$AWS_S3_BUCKET" ] && [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
        local timestamp=$(date +"%Y%m%d_%H%M%S")
        local s3_path="s3://$AWS_S3_BUCKET/backups/$ENVIRONMENT/$timestamp/"
        
        # Upload database backups
        aws s3 sync "$BACKUP_DIR/database/" "$s3_path/database/"
        
        # Upload log backups
        aws s3 sync "$BACKUP_DIR/logs/" "$s3_path/logs/"
        
        # Upload file backups
        aws s3 sync "$BACKUP_DIR/files/" "$s3_path/files/"
        
        log_success "Backups uploaded to S3: $s3_path"
    else
        log_warning "S3 credentials not configured, skipping S3 upload"
    fi
}

# Cleanup old backups
cleanup_old_backups() {
    log_info "Cleaning up old backups (older than $RETENTION_DAYS days)..."
    
    # Cleanup local backups
    find "$BACKUP_DIR" -type f -name "*.gz" -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -type f -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
    
    # Cleanup S3 backups
    if [ -n "$AWS_S3_BUCKET" ]; then
        aws s3 ls "s3://$AWS_S3_BUCKET/backups/$ENVIRONMENT/" --recursive | \
        awk '$1 < "'$(date -d "$RETENTION_DAYS days ago" +%Y-%m-%d)'" {print $4}' | \
        xargs -r aws s3 rm "s3://$AWS_S3_BUCKET/"
    fi
    
    log_success "Old backups cleaned up"
}

# Rotate logs
rotate_logs() {
    log_info "Rotating application logs..."
    
    # Rotate application logs
    if [ -d "/var/log/ai-writer-pro" ]; then
        find /var/log/ai-writer-pro -name "*.log" -size +100M -exec mv {} {}.old \;
        find /var/log/ai-writer-pro -name "*.log.old" -mtime +7 -delete
    fi
    
    # Rotate Docker logs
    if command -v docker &> /dev/null; then
        # Truncate Docker logs
        docker exec ai-writer-pro-backend sh -c 'echo "" > /var/log/app.log' || true
        docker exec ai-writer-pro-frontend sh -c 'echo "" > /var/log/app.log' || true
    fi
    
    log_success "Log rotation completed"
}

# System maintenance
system_maintenance() {
    log_info "Performing system maintenance..."
    
    # Update package lists
    if command -v apt-get &> /dev/null; then
        apt-get update
    fi
    
    # Clean package cache
    if command -v apt-get &> /dev/null; then
        apt-get clean
    fi
    
    # Clean Docker
    if command -v docker &> /dev/null; then
        docker system prune -f
        docker volume prune -f
    fi
    
    # Clean temporary files
    find /tmp -type f -mtime +7 -delete
    
    log_success "System maintenance completed"
}

# Health check
health_check() {
    log_info "Performing health check..."
    
    # Check disk space
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ $disk_usage -gt 90 ]; then
        log_warning "Disk usage is high: ${disk_usage}%"
    fi
    
    # Check memory usage
    local memory_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ $memory_usage -gt 90 ]; then
        log_warning "Memory usage is high: ${memory_usage}%"
    fi
    
    # Check application health
    if [ -n "$BACKEND_URL" ]; then
        if curl -f -s "$BACKEND_URL/health" > /dev/null; then
            log_success "Backend is healthy"
        else
            log_error "Backend health check failed"
        fi
    fi
    
    log_success "Health check completed"
}

# Send backup notification
send_notification() {
    log_info "Sending backup notification..."
    
    local status="$1"
    local message="Backup $status for $ENVIRONMENT environment"
    
    # Send to Slack (if configured)
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\"}" \
            "$SLACK_WEBHOOK_URL"
    fi
    
    # Send to email (if configured)
    if [ -n "$NOTIFICATION_EMAIL" ]; then
        echo "$message" | mail -s "Backup Notification" "$NOTIFICATION_EMAIL"
    fi
    
    log_success "Notification sent"
}

# Restore from backup
restore_backup() {
    log_info "Restoring from backup..."
    
    local backup_file="$1"
    
    if [ -z "$backup_file" ]; then
        log_error "Backup file not specified"
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        exit 1
    fi
    
    # Extract database connection details
    local db_host=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
    local db_port=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    local db_name=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
    local db_user=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
    local db_password=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
    
    # Set password environment variable
    export PGPASSWORD="$db_password"
    
    # Restore database
    if [[ "$backup_file" == *.gz ]]; then
        gunzip -c "$backup_file" | psql -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name"
    else
        psql -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" < "$backup_file"
    fi
    
    log_success "Database restored from: $backup_file"
}

# Main backup function
main() {
    log_info "Starting backup process for $ENVIRONMENT environment"
    
    # Create backup directory
    create_backup_dir
    
    # Perform backups
    backup_database
    backup_logs
    backup_files
    
    # Upload to S3
    backup_to_s3
    
    # Cleanup old backups
    cleanup_old_backups
    
    # Rotate logs
    rotate_logs
    
    # System maintenance
    system_maintenance
    
    # Health check
    health_check
    
    # Send notification
    send_notification "completed successfully"
    
    log_success "Backup process completed successfully!"
}

# Handle script arguments
case "${1:-}" in
    "restore")
        restore_backup "$2"
        ;;
    "cleanup")
        cleanup_old_backups
        ;;
    "health")
        health_check
        ;;
    "maintenance")
        system_maintenance
        ;;
    *)
        main
        ;;
esac
