"""
Centralized logging configuration for the AI Writer PRO backend.

This module provides a consistent logging setup using structlog across all services.
"""

import structlog
from app.core.config import settings


def get_logger(name: str):
    """
    Get a structured logger instance for the given module name.
    
    Args:
        name: The module name (typically __name__)
        
    Returns:
        A structlog logger instance
    """
    return structlog.get_logger(name)


# Configure structlog if not already configured
if not structlog.is_configured():
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
