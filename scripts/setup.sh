#!/bin/bash

# AI Writer PRO Setup Script
# This script sets up the development environment for the AI Writer PRO project

set -e  # Exit on any error

echo "🚀 Setting up AI Writer PRO development environment..."

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

# Check if required tools are installed
check_requirements() {
    print_status "Checking system requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_warning "Node.js is not installed. Frontend development will not be available."
    else
        NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
        if [ "$NODE_VERSION" -lt 18 ]; then
            print_warning "Node.js version is less than 18. Please upgrade to Node.js 18 or higher."
        fi
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_warning "Python 3 is not installed. Backend development will not be available."
    else
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        print_status "Found Python $PYTHON_VERSION"
    fi
    
    print_success "System requirements check completed"
}

# Setup environment variables
setup_environment() {
    print_status "Setting up environment variables..."
    
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            print_success "Created .env file from .env.example"
            print_warning "Please edit .env file with your actual configuration values"
        else
            print_error ".env.example file not found"
            exit 1
        fi
    else
        print_status ".env file already exists, skipping creation"
    fi
}

# Setup frontend dependencies
setup_frontend() {
    print_status "Setting up frontend dependencies..."
    
    if [ -d "frontend" ]; then
        cd frontend
        
        if [ -f "package.json" ]; then
            if command -v npm &> /dev/null; then
                npm install
                print_success "Frontend dependencies installed"
            else
                print_warning "npm not found, skipping frontend setup"
            fi
        else
            print_warning "package.json not found in frontend directory"
        fi
        
        cd ..
    else
        print_warning "Frontend directory not found"
    fi
}

# Setup backend dependencies
setup_backend() {
    print_status "Setting up backend dependencies..."
    
    if [ -d "backend" ]; then
        cd backend
        
        if [ -f "requirements.txt" ]; then
            if command -v python3 &> /dev/null; then
                # Create virtual environment if it doesn't exist
                if [ ! -d "venv" ]; then
                    python3 -m venv venv
                    print_success "Created Python virtual environment"
                fi
                
                # Activate virtual environment and install dependencies
                source venv/bin/activate
                pip install --upgrade pip
                pip install -r requirements.txt
                print_success "Backend dependencies installed"
                deactivate
            else
                print_warning "Python 3 not found, skipping backend setup"
            fi
        else
            print_warning "requirements.txt not found in backend directory"
        fi
        
        cd ..
    else
        print_warning "Backend directory not found"
    fi
}

# Start Docker services
start_services() {
    print_status "Starting Docker services..."
    
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d postgres redis rabbitmq
    elif docker compose version &> /dev/null; then
        docker compose up -d postgres redis rabbitmq
    else
        print_error "Docker Compose not available"
        exit 1
    fi
    
    print_success "Docker services started"
    print_status "Waiting for services to be ready..."
    sleep 10
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    if [ -d "backend" ] && [ -f "backend/alembic.ini" ]; then
        cd backend
        
        if [ -d "venv" ]; then
            source venv/bin/activate
        fi
        
        # Check if alembic is available
        if command -v alembic &> /dev/null || python -c "import alembic" 2>/dev/null; then
            alembic upgrade head
            print_success "Database migrations completed"
        else
            print_warning "Alembic not found, skipping migrations"
        fi
        
        if [ -d "venv" ]; then
            deactivate
        fi
        
        cd ..
    else
        print_warning "Backend or Alembic configuration not found"
    fi
}

# Main setup function
main() {
    echo "=========================================="
    echo "  AI Writer PRO Development Setup"
    echo "=========================================="
    echo
    
    check_requirements
    setup_environment
    setup_frontend
    setup_backend
    start_services
    run_migrations
    
    echo
    echo "=========================================="
    print_success "Setup completed successfully!"
    echo "=========================================="
    echo
    echo "Next steps:"
    echo "1. Edit .env file with your configuration"
    echo "2. Run './scripts/dev.sh' to start development servers"
    echo "3. Visit http://localhost:3000 for frontend"
    echo "4. Visit http://localhost:8000/docs for API documentation"
    echo
    echo "Services running:"
    echo "- PostgreSQL: localhost:5432"
    echo "- Redis: localhost:6379"
    echo "- RabbitMQ Management: http://localhost:15672"
    echo
}

# Run main function
main "$@"
