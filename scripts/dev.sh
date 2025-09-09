#!/bin/bash

# AI Writer PRO Development Script
# This script starts all development services and servers

set -e  # Exit on any error

echo "🚀 Starting AI Writer PRO development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a service is healthy
check_service_health() {
    local service_name=$1
    local health_url=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$health_url" > /dev/null 2>&1; then
            print_success "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within expected time"
    return 1
}

# Function to start Docker services
start_docker_services() {
    print_status "Starting Docker services..."
    
    # Determine which docker-compose command to use
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker compose"
    else
        print_error "Docker Compose not available"
        exit 1
    fi
    
    # Start infrastructure services
    $DOCKER_COMPOSE_CMD up -d postgres redis rabbitmq
    
    # Wait for services to be ready
    print_status "Waiting for infrastructure services to be ready..."
    sleep 15
    
    # Check PostgreSQL
    if ! $DOCKER_COMPOSE_CMD exec -T postgres pg_isready -U ai_writer_user -d ai_writer_db > /dev/null 2>&1; then
        print_error "PostgreSQL is not ready"
        exit 1
    fi
    print_success "PostgreSQL is ready"
    
    # Check Redis
    if ! $DOCKER_COMPOSE_CMD exec -T redis redis-cli ping > /dev/null 2>&1; then
        print_error "Redis is not ready"
        exit 1
    fi
    print_success "Redis is ready"
    
    # Check RabbitMQ
    if ! $DOCKER_COMPOSE_CMD exec -T rabbitmq rabbitmq-diagnostics ping > /dev/null 2>&1; then
        print_error "RabbitMQ is not ready"
        exit 1
    fi
    print_success "RabbitMQ is ready"
}

# Function to run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    if [ -d "backend" ] && [ -f "backend/alembic.ini" ]; then
        cd backend
        
        # Use Docker to run migrations if available
        if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
            if command -v docker-compose &> /dev/null; then
                docker-compose exec backend alembic upgrade head
            else
                docker compose exec backend alembic upgrade head
            fi
            print_success "Database migrations completed"
        else
            # Fallback to local Python environment
            if [ -d "venv" ]; then
                source venv/bin/activate
            fi
            
            if command -v alembic &> /dev/null || python -c "import alembic" 2>/dev/null; then
                alembic upgrade head
                print_success "Database migrations completed"
            else
                print_warning "Alembic not found, skipping migrations"
            fi
            
            if [ -d "venv" ]; then
                deactivate
            fi
        fi
    else
        print_warning "Backend or Alembic configuration not found"
    fi
}

# Function to start backend server
start_backend() {
    print_status "Starting backend server..."
    
    if [ -d "backend" ]; then
        cd backend
        
        # Use Docker if available
        if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
            cd ..
            if command -v docker-compose &> /dev/null; then
                docker-compose up -d backend
            else
                docker compose up -d backend
            fi
            print_success "Backend server started in Docker"
        else
            # Fallback to local Python environment
            if [ -d "venv" ]; then
                source venv/bin/activate
            fi
            
            if command -v uvicorn &> /dev/null || python -c "import uvicorn" 2>/dev/null; then
                uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
                BACKEND_PID=$!
                print_success "Backend server started locally (PID: $BACKEND_PID)"
            else
                print_warning "Uvicorn not found, skipping backend startup"
            fi
        fi
        
        cd ..
    else
        print_warning "Backend directory not found"
    fi
}

# Function to start frontend server
start_frontend() {
    print_status "Starting frontend server..."
    
    if [ -d "frontend" ]; then
        cd frontend
        
        # Use Docker if available
        if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
            cd ..
            if command -v docker-compose &> /dev/null; then
                docker-compose up -d frontend
            else
                docker compose up -d frontend
            fi
            print_success "Frontend server started in Docker"
        else
            # Fallback to local Node.js environment
            if command -v npm &> /dev/null; then
                if [ -f "package.json" ]; then
                    npm run dev &
                    FRONTEND_PID=$!
                    print_success "Frontend server started locally (PID: $FRONTEND_PID)"
                else
                    print_warning "package.json not found in frontend directory"
                fi
            else
                print_warning "npm not found, skipping frontend startup"
            fi
        fi
        
        cd ..
    else
        print_warning "Frontend directory not found"
    fi
}

# Function to display service URLs
show_service_urls() {
    echo
    echo "=========================================="
    print_success "Development environment is ready!"
    echo "=========================================="
    echo
    echo "🌐 Service URLs:"
    echo "   Frontend:     http://localhost:3000"
    echo "   Backend API:  http://localhost:8000"
    echo "   API Docs:     http://localhost:8000/docs"
    echo "   ReDoc:        http://localhost:8000/redoc"
    echo "   RabbitMQ:     http://localhost:15672"
    echo
    echo "🗄️  Database:"
    echo "   PostgreSQL:   localhost:5432"
    echo "   Redis:        localhost:6379"
    echo
    echo "📝 Logs:"
    if command -v docker-compose &> /dev/null; then
        echo "   docker-compose logs -f"
    elif docker compose version &> /dev/null; then
        echo "   docker compose logs -f"
    fi
    echo
    echo "🛑 To stop all services:"
    if command -v docker-compose &> /dev/null; then
        echo "   docker-compose down"
    elif docker compose version &> /dev/null; then
        echo "   docker compose down"
    fi
    echo
}

# Function to handle cleanup on exit
cleanup() {
    echo
    print_status "Shutting down development environment..."
    
    # Kill local processes if they exist
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    print_success "Cleanup completed"
}

# Set up signal handlers
trap cleanup EXIT INT TERM

# Main function
main() {
    echo "=========================================="
    echo "  AI Writer PRO Development Environment"
    echo "=========================================="
    echo
    
    start_docker_services
    run_migrations
    start_backend
    start_frontend
    
    # Wait a moment for services to start
    sleep 5
    
    show_service_urls
    
    # Keep script running and show logs
    print_status "Press Ctrl+C to stop all services"
    echo
    
    if command -v docker-compose &> /dev/null; then
        docker-compose logs -f
    elif docker compose version &> /dev/null; then
        docker compose logs -f
    else
        # If no Docker Compose, just wait
        while true; do
            sleep 1
        done
    fi
}

# Run main function
main "$@"
