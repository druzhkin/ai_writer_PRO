"""
Development script for running database migrations, initializing test data, and starting the development server.
"""

import asyncio
import sys
import os
import subprocess
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import structlog

logger = structlog.get_logger()


def run_command(command: str, description: str) -> bool:
    """Run a shell command and return success status."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e.stderr}")
        return False


def check_environment():
    """Check if required environment variables are set."""
    print("🔍 Checking environment...")
    
    required_vars = [
        "DATABASE_URL",
        "JWT_SECRET_KEY",
        "SESSION_SECRET_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please create a .env file with the required variables.")
        return False
    
    print("✅ Environment check passed")
    return True


def install_dependencies():
    """Install Python dependencies."""
    return run_command(
        "pip install -r requirements.txt",
        "Installing Python dependencies"
    )


def run_database_migrations():
    """Run database migrations."""
    return run_command(
        "alembic upgrade head",
        "Running database migrations"
    )


async def initialize_database():
    """Initialize database with default data."""
    print("🔄 Initializing database with default data...")
    try:
        from scripts.init_db import initialize_database as init_db
        await init_db()
        print("✅ Database initialization completed")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False


def run_tests():
    """Run the test suite."""
    return run_command(
        "pytest tests/ -v --tb=short",
        "Running test suite"
    )


def start_development_server():
    """Start the development server."""
    print("🚀 Starting development server...")
    try:
        subprocess.run([
            "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload",
            "--log-level", "info"
        ], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Development server stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start development server: {e}")


def show_help():
    """Show help message."""
    print("""
AI Writer PRO - Development Script

Usage: python scripts/dev.py [command]

Commands:
  setup     - Full setup (install deps, run migrations, init db)
  migrate   - Run database migrations only
  init      - Initialize database with default data only
  test      - Run test suite
  server    - Start development server
  help      - Show this help message

Examples:
  python scripts/dev.py setup    # Full setup for first time
  python scripts/dev.py server   # Start development server
  python scripts/dev.py test     # Run tests
""")


async def main():
    """Main function."""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "help":
        show_help()
        return
    
    if command == "setup":
        print("🚀 Starting full development setup...")
        
        if not check_environment():
            return
        
        if not install_dependencies():
            return
        
        if not run_database_migrations():
            return
        
        if not await initialize_database():
            return
        
        print("\n✅ Full setup completed successfully!")
        print("\nNext steps:")
        print("1. Start the development server: python scripts/dev.py server")
        print("2. Open http://localhost:8000/docs to view the API documentation")
        print("3. Login with admin@aiwriter.com / admin123456")
        
    elif command == "migrate":
        if not check_environment():
            return
        run_database_migrations()
        
    elif command == "init":
        if not check_environment():
            return
        await initialize_database()
        
    elif command == "test":
        if not check_environment():
            return
        run_tests()
        
    elif command == "server":
        if not check_environment():
            return
        start_development_server()
        
    else:
        print(f"❌ Unknown command: {command}")
        show_help()


if __name__ == "__main__":
    asyncio.run(main())
