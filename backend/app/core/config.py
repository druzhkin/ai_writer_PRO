"""
Application configuration using Pydantic settings.
"""

from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str = "postgresql://ai_writer_user:ai_writer_password@localhost:5432/ai_writer_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # RabbitMQ
    RABBITMQ_URL: str = "amqp://ai_writer_user:ai_writer_password@localhost:5672/"
    
    # JWT
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    OAUTH_REDIRECT_URI: str = "http://localhost:8000/api/v1/oauth/callback"
    
    # Session
    SESSION_SECRET_KEY: str = "your-super-secret-session-key-change-in-production"
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    
    # AWS S3
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_S3_BUCKET: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_STYLES_PREFIX: str = "styles"
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # File Upload
    MAX_FILE_SIZE: int = 52428800  # 50MB
    ALLOWED_FILE_TYPES: List[str] = [
        "image/jpeg",
        "image/png", 
        "image/gif",
        "text/plain",
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"  # .docx
    ]
    
    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    EMAIL_FROM: str = "noreply@aiwriter.com"
    EMAIL_FROM_NAME: str = "AI Writer"
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "development"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    SENTRY_PROFILES_SAMPLE_RATE: float = 0.1
    GOOGLE_ANALYTICS_ID: Optional[str] = None
    
    # Health Checks
    HEALTH_CHECK_ENABLED: bool = True
    HEALTH_CHECK_INTERVAL: int = 30  # seconds
    
    # Development Tools
    ENABLE_SWAGGER_UI: bool = True
    ENABLE_REDOC: bool = True
    
    # Style Analysis
    MAX_REFERENCE_ARTICLES_PER_STYLE: int = 50
    
    # Content Generation
    # Token costs per 1K tokens (in USD)
    OPENAI_GPT4_INPUT_COST_PER_1K: float = 0.01
    OPENAI_GPT4_OUTPUT_COST_PER_1K: float = 0.03
    OPENAI_GPT4_TURBO_INPUT_COST_PER_1K: float = 0.005
    OPENAI_GPT4_TURBO_OUTPUT_COST_PER_1K: float = 0.015
    
    # Content generation limits per plan
    FREE_PLAN_DAILY_TOKENS: int = 10000
    BASIC_PLAN_DAILY_TOKENS: int = 100000
    PRO_PLAN_DAILY_TOKENS: int = 1000000
    ENTERPRISE_PLAN_DAILY_TOKENS: int = 10000000
    
    # Content generation settings
    MAX_CONTENT_LENGTH: int = 50000  # characters
    MIN_CONTENT_LENGTH: int = 100    # characters
    MAX_TARGET_WORDS: int = 5000     # words
    MIN_TARGET_WORDS: int = 100      # words
    CONTENT_GENERATION_TIMEOUT: int = 300  # seconds
    MAX_CONTENT_ITERATIONS: int = 50
    
    # Usage tracking
    USAGE_TRACKING_ENABLED: bool = True
    USAGE_ANALYTICS_RETENTION_DAYS: int = 365
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @field_validator("ALLOWED_FILE_TYPES", mode="before")
    @classmethod
    def assemble_file_types(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v):
        allowed_envs = ["development", "staging", "production", "testing"]
        if v not in allowed_envs:
            raise ValueError(f"ENVIRONMENT must be one of {allowed_envs}")
        return v
    
    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v):
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")
        return v
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }


# Create global settings instance
settings = Settings()
