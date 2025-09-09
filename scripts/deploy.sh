#!/bin/bash

# AI Writer PRO Deployment Script
# This script handles deployment to different environments

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-staging}"
VERSION="${2:-latest}"

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

# Check if required tools are installed
check_dependencies() {
    log_info "Checking dependencies..."
    
    local missing_deps=()
    
    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        missing_deps+=("docker-compose")
    fi
    
    if ! command -v kubectl &> /dev/null; then
        missing_deps+=("kubectl")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_error "Please install the missing dependencies and try again."
        exit 1
    fi
    
    log_success "All dependencies are installed"
}

# Validate environment
validate_environment() {
    log_info "Validating environment: $ENVIRONMENT"
    
    case $ENVIRONMENT in
        "development"|"staging"|"production")
            log_success "Environment $ENVIRONMENT is valid"
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT"
            log_error "Valid environments are: development, staging, production"
            exit 1
            ;;
    esac
}

# Load environment variables
load_environment() {
    log_info "Loading environment variables for $ENVIRONMENT"
    
    local env_file="$PROJECT_ROOT/.env.$ENVIRONMENT"
    
    if [ ! -f "$env_file" ]; then
        log_error "Environment file not found: $env_file"
        exit 1
    fi
    
    # Load environment variables
    set -a
    source "$env_file"
    set +a
    
    log_success "Environment variables loaded"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    cd "$PROJECT_ROOT/backend"
    
    # Run migrations
    alembic upgrade head
    
    log_success "Database migrations completed"
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    
    cd "$PROJECT_ROOT"
    
    # Build backend image
    log_info "Building backend image..."
    docker build -t ai-writer-pro-backend:$VERSION ./backend
    
    # Build frontend image
    log_info "Building frontend image..."
    docker build -t ai-writer-pro-frontend:$VERSION ./frontend
    
    log_success "Docker images built successfully"
}

# Run tests
run_tests() {
    log_info "Running tests..."
    
    cd "$PROJECT_ROOT"
    
    # Run backend tests
    log_info "Running backend tests..."
    cd backend
    pytest --cov=app --cov-report=xml --cov-fail-under=80 -v
    
    # Run frontend tests
    log_info "Running frontend tests..."
    cd ../frontend
    npm run test:ci
    
    # Run E2E tests
    log_info "Running E2E tests..."
    npm run test:e2e:ci
    
    cd "$PROJECT_ROOT"
    log_success "All tests passed"
}

# Deploy to Docker Compose
deploy_docker_compose() {
    log_info "Deploying with Docker Compose..."
    
    cd "$PROJECT_ROOT"
    
    # Stop existing containers
    log_info "Stopping existing containers..."
    docker-compose -f docker-compose.prod.yml down
    
    # Start new containers
    log_info "Starting new containers..."
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 30
    
    # Check health
    check_health
    
    log_success "Deployment completed successfully"
}

# Deploy to Kubernetes
deploy_kubernetes() {
    log_info "Deploying to Kubernetes..."
    
    cd "$PROJECT_ROOT"
    
    # Apply Kubernetes manifests
    log_info "Applying Kubernetes manifests..."
    kubectl apply -f k8s/$ENVIRONMENT/
    
    # Wait for deployment to be ready
    log_info "Waiting for deployment to be ready..."
    kubectl rollout status deployment/ai-writer-pro-backend -n ai-writer-pro
    kubectl rollout status deployment/ai-writer-pro-frontend -n ai-writer-pro
    
    # Check health
    check_health
    
    log_success "Kubernetes deployment completed successfully"
}

# Check application health
check_health() {
    log_info "Checking application health..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log_info "Health check attempt $attempt/$max_attempts"
        
        # Check backend health
        if curl -f -s "$BACKEND_URL/health" > /dev/null; then
            log_success "Backend is healthy"
        else
            log_warning "Backend health check failed"
        fi
        
        # Check frontend health
        if curl -f -s "$FRONTEND_URL" > /dev/null; then
            log_success "Frontend is healthy"
        else
            log_warning "Frontend health check failed"
        fi
        
        # If both are healthy, break
        if curl -f -s "$BACKEND_URL/health" > /dev/null && curl -f -s "$FRONTEND_URL" > /dev/null; then
            log_success "All services are healthy"
            break
        fi
        
        # Wait before next attempt
        sleep 10
        attempt=$((attempt + 1))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "Health check failed after $max_attempts attempts"
        exit 1
    fi
}

# Rollback deployment
rollback() {
    log_info "Rolling back deployment..."
    
    case $ENVIRONMENT in
        "staging"|"production")
            # Rollback Kubernetes deployment
            kubectl rollout undo deployment/ai-writer-pro-backend -n ai-writer-pro
            kubectl rollout undo deployment/ai-writer-pro-frontend -n ai-writer-pro
            ;;
        "development")
            # Rollback Docker Compose deployment
            cd "$PROJECT_ROOT"
            docker-compose -f docker-compose.prod.yml down
            docker-compose -f docker-compose.prod.yml up -d
            ;;
    esac
    
    log_success "Rollback completed"
}

# Cleanup old images
cleanup() {
    log_info "Cleaning up old Docker images..."
    
    # Remove unused images
    docker image prune -f
    
    # Remove old versions
    docker images | grep ai-writer-pro | grep -v $VERSION | awk '{print $3}' | xargs -r docker rmi
    
    log_success "Cleanup completed"
}

# Send deployment notification
send_notification() {
    log_info "Sending deployment notification..."
    
    local status="$1"
    local message="Deployment to $ENVIRONMENT $status"
    
    # Send to Slack (if configured)
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\"}" \
            "$SLACK_WEBHOOK_URL"
    fi
    
    # Send to email (if configured)
    if [ -n "$NOTIFICATION_EMAIL" ]; then
        echo "$message" | mail -s "Deployment Notification" "$NOTIFICATION_EMAIL"
    fi
    
    log_success "Notification sent"
}

# Main deployment function
main() {
    log_info "Starting deployment to $ENVIRONMENT environment"
    
    # Check dependencies
    check_dependencies
    
    # Validate environment
    validate_environment
    
    # Load environment variables
    load_environment
    
    # Run tests (skip for development)
    if [ "$ENVIRONMENT" != "development" ]; then
        run_tests
    fi
    
    # Run database migrations
    run_migrations
    
    # Build images
    build_images
    
    # Deploy based on environment
    case $ENVIRONMENT in
        "development")
            deploy_docker_compose
            ;;
        "staging"|"production")
            deploy_kubernetes
            ;;
    esac
    
    # Cleanup
    cleanup
    
    # Send notification
    send_notification "completed successfully"
    
    log_success "Deployment to $ENVIRONMENT completed successfully!"
}

# Handle script arguments
case "${1:-}" in
    "rollback")
        load_environment
        rollback
        send_notification "rolled back"
        ;;
    "health")
        load_environment
        check_health
        ;;
    "cleanup")
        cleanup
        ;;
    *)
        main
        ;;
esac
