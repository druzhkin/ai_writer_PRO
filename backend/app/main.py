"""
AI Writer PRO Backend Application

FastAPI application with CORS middleware, health checks, and proper error handling.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import JSONResponse
import structlog
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.core.database import engine
from app.api.v1.api import api_router
from app.core.oauth import oauth_service
from sqlalchemy import text

# Initialize Sentry for error tracking and performance monitoring
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        integrations=[
            FastApiIntegration(auto_enabling_instrumentations=True),
            SqlalchemyIntegration(),
            RedisIntegration(),
            CeleryIntegration(),
        ],
        traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
        profiles_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
        send_default_pii=False,
        attach_stacktrace=True,
        release=f"ai-writer-pro@{settings.ENVIRONMENT}",
    )

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting AI Writer PRO Backend", version="0.1.0")
    
    # Initialize database connection
    try:
        # Test database connection
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection established")
    except Exception as e:
        logger.error("Failed to connect to database", error=str(e))
        raise
    
    # Initialize OAuth clients
    try:
        configured_providers = oauth_service.get_configured_providers()
        logger.info("OAuth providers configured", providers=configured_providers)
    except Exception as e:
        logger.warning("OAuth initialization failed", error=str(e))
    
    # Create default admin user if none exists
    try:
        from app.core.database import get_db
        from app.services.auth_service import AuthService
        from app.models.user import User
        from sqlalchemy import select
        
        async for db in get_db():
            result = await db.execute(select(User).where(User.is_superuser == True))
            admin_user = result.scalar_one_or_none()
            
            if not admin_user:
                # Create default admin user
                auth_service = AuthService(db)
                from app.schemas.auth import UserCreate
                admin_data = UserCreate(
                    email="admin@aiwriter.com",
                    username="admin",
                    password="admin123456",
                    first_name="Admin",
                    last_name="User"
                )
                
                try:
                    user, organization = await auth_service.create_user(admin_data)
                    user.is_superuser = True
                    user.is_verified = True
                    await db.commit()
                    logger.info("Default admin user created", email=user.email)
                except Exception as e:
                    logger.warning("Failed to create default admin user", error=str(e))
            break
    except Exception as e:
        logger.warning("Failed to check/create default admin user", error=str(e))
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Writer PRO Backend")
    await engine.dispose()


# Create FastAPI application
app = FastAPI(
    title="AI Writer PRO API",
    description="AI-powered article generation service",
    version="0.1.0",
    docs_url="/docs" if settings.ENABLE_SWAGGER_UI else None,
    redoc_url="/redoc" if settings.ENABLE_REDOC else None,
    openapi_url="/openapi.json" if settings.ENABLE_SWAGGER_UI else None,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.aiwriterpro.com", "aiwriterpro.com"]
    )

# Add session middleware for OAuth support
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
    max_age=3600  # 1 hour
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all HTTP requests with structured logging.
    """
    start_time = time.time()
    
    # Log request
    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(
        "Request completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time,
    )
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.
    """
    logger.error(
        "Unhandled exception",
        method=request.method,
        url=str(request.url),
        error=str(exc),
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR"
        }
    )


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    """
    return {
        "status": "healthy",
        "service": "AI Writer PRO Backend",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT
    }


@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "AI Writer PRO API",
        "version": "0.1.0",
        "docs": "/docs" if settings.ENABLE_SWAGGER_UI else None,
        "health": "/health"
    }


# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Add Prometheus instrumentation
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)


if __name__ == "__main__":
    import uvicorn
    import time
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
