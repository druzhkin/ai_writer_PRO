@echo off
REM AI Writer PRO Development Script for Windows
REM This script starts all development services and servers

echo 🚀 Starting AI Writer PRO development environment...

REM Start Docker services
echo [INFO] Starting Docker services...

docker-compose --version >nul 2>&1
if %errorlevel% equ 0 (
    set DOCKER_COMPOSE_CMD=docker-compose
) else (
    set DOCKER_COMPOSE_CMD=docker compose
)

REM Start infrastructure services
%DOCKER_COMPOSE_CMD% up -d postgres redis rabbitmq

REM Wait for services to be ready
echo [INFO] Waiting for infrastructure services to be ready...
timeout /t 15 /nobreak >nul

REM Check PostgreSQL
%DOCKER_COMPOSE_CMD% exec -T postgres pg_isready -U ai_writer_user -d ai_writer_db >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] PostgreSQL is not ready
    exit /b 1
)
echo [SUCCESS] PostgreSQL is ready

REM Check Redis
%DOCKER_COMPOSE_CMD% exec -T redis redis-cli ping >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Redis is not ready
    exit /b 1
)
echo [SUCCESS] Redis is ready

REM Check RabbitMQ
%DOCKER_COMPOSE_CMD% exec -T rabbitmq rabbitmq-diagnostics ping >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] RabbitMQ is not ready
    exit /b 1
)
echo [SUCCESS] RabbitMQ is ready

REM Run database migrations
echo [INFO] Running database migrations...

if exist backend\alembic.ini (
    %DOCKER_COMPOSE_CMD% exec backend alembic upgrade head
    echo [SUCCESS] Database migrations completed
) else (
    echo [WARNING] Backend or Alembic configuration not found
)

REM Start backend server
echo [INFO] Starting backend server...

if exist backend (
    %DOCKER_COMPOSE_CMD% up -d backend
    echo [SUCCESS] Backend server started in Docker
) else (
    echo [WARNING] Backend directory not found
)

REM Start frontend server
echo [INFO] Starting frontend server...

if exist frontend (
    %DOCKER_COMPOSE_CMD% up -d frontend
    echo [SUCCESS] Frontend server started in Docker
) else (
    echo [WARNING] Frontend directory not found
)

REM Wait a moment for services to start
timeout /t 5 /nobreak >nul

echo.
echo ==========================================
echo [SUCCESS] Development environment is ready!
echo ==========================================
echo.
echo 🌐 Service URLs:
echo    Frontend:     http://localhost:3000
echo    Backend API:  http://localhost:8000
echo    API Docs:     http://localhost:8000/docs
echo    ReDoc:        http://localhost:8000/redoc
echo    RabbitMQ:     http://localhost:15672
echo.
echo 🗄️  Database:
echo    PostgreSQL:   localhost:5432
echo    Redis:        localhost:6379
echo.
echo 📝 Logs:
echo    %DOCKER_COMPOSE_CMD% logs -f
echo.
echo 🛑 To stop all services:
echo    %DOCKER_COMPOSE_CMD% down
echo.
echo [INFO] Press Ctrl+C to stop all services
echo.

REM Keep script running and show logs
%DOCKER_COMPOSE_CMD% logs -f
