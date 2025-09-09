@echo off
REM AI Writer PRO Setup Script for Windows
REM This script sets up the development environment for the AI Writer PRO project

echo 🚀 Setting up AI Writer PRO development environment...

REM Check if required tools are installed
echo [INFO] Checking system requirements...

REM Check Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop first.
    exit /b 1
)

REM Check Docker Compose
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    docker compose version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Docker Compose is not installed. Please install Docker Compose first.
        exit /b 1
    )
)

REM Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Node.js is not installed. Frontend development will not be available.
) else (
    echo [INFO] Found Node.js
)

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Python is not installed. Backend development will not be available.
) else (
    echo [INFO] Found Python
)

echo [SUCCESS] System requirements check completed

REM Setup environment variables
echo [INFO] Setting up environment variables...

if not exist .env (
    if exist env.example (
        copy env.example .env >nul
        echo [SUCCESS] Created .env file from env.example
        echo [WARNING] Please edit .env file with your actual configuration values
    ) else (
        echo [ERROR] env.example file not found
        exit /b 1
    )
) else (
    echo [INFO] .env file already exists, skipping creation
)

REM Setup frontend dependencies
echo [INFO] Setting up frontend dependencies...

if exist frontend (
    cd frontend
    
    if exist package.json (
        npm --version >nul 2>&1
        if %errorlevel% equ 0 (
            npm install
            echo [SUCCESS] Frontend dependencies installed
        ) else (
            echo [WARNING] npm not found, skipping frontend setup
        )
    ) else (
        echo [WARNING] package.json not found in frontend directory
    )
    
    cd ..
) else (
    echo [WARNING] Frontend directory not found
)

REM Setup backend dependencies
echo [INFO] Setting up backend dependencies...

if exist backend (
    cd backend
    
    if exist requirements.txt (
        python --version >nul 2>&1
        if %errorlevel% equ 0 (
            REM Create virtual environment if it doesn't exist
            if not exist venv (
                python -m venv venv
                echo [SUCCESS] Created Python virtual environment
            )
            
            REM Activate virtual environment and install dependencies
            call venv\Scripts\activate.bat
            python -m pip install --upgrade pip
            pip install -r requirements.txt
            echo [SUCCESS] Backend dependencies installed
            call venv\Scripts\deactivate.bat
        ) else (
            echo [WARNING] Python not found, skipping backend setup
        )
    ) else (
        echo [WARNING] requirements.txt not found in backend directory
    )
    
    cd ..
) else (
    echo [WARNING] Backend directory not found
)

REM Start Docker services
echo [INFO] Starting Docker services...

docker-compose --version >nul 2>&1
if %errorlevel% equ 0 (
    docker-compose up -d postgres redis rabbitmq
) else (
    docker compose up -d postgres redis rabbitmq
)

echo [SUCCESS] Docker services started
echo [INFO] Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Run database migrations
echo [INFO] Running database migrations...

if exist backend\alembic.ini (
    cd backend
    
    if exist venv (
        call venv\Scripts\activate.bat
    )
    
    REM Check if alembic is available
    alembic --version >nul 2>&1
    if %errorlevel% equ 0 (
        alembic upgrade head
        echo [SUCCESS] Database migrations completed
    ) else (
        echo [WARNING] Alembic not found, skipping migrations
    )
    
    if exist venv (
        call venv\Scripts\deactivate.bat
    )
    
    cd ..
) else (
    echo [WARNING] Backend or Alembic configuration not found
)

echo.
echo ==========================================
echo [SUCCESS] Setup completed successfully!
echo ==========================================
echo.
echo Next steps:
echo 1. Edit .env file with your configuration
echo 2. Run 'scripts\dev.bat' to start development servers
echo 3. Visit http://localhost:3000 for frontend
echo 4. Visit http://localhost:8000/docs for API documentation
echo.
echo Services running:
echo - PostgreSQL: localhost:5432
echo - Redis: localhost:6379
echo - RabbitMQ Management: http://localhost:15672
echo.

pause
