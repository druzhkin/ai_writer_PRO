"""
Health monitoring service for comprehensive application health checks.
"""

import asyncio
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
import psutil
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import httpx

from app.core.config import settings
from app.core.database import engine
from app.core.logging import get_logger

logger = get_logger(__name__)


class HealthService:
    """
    Service for monitoring application health and dependencies.
    """
    
    def __init__(self):
        self.redis_client = None
        self.last_check = None
        self.health_cache = {}
        self.cache_ttl = 30  # seconds
    
    async def get_redis_client(self) -> redis.Redis:
        """Get Redis client connection."""
        if not self.redis_client:
            self.redis_client = redis.from_url(settings.REDIS_URL)
        return self.redis_client
    
    async def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            start_time = time.time()
            
            async with engine.begin() as conn:
                # Test basic connectivity
                result = await conn.execute(text("SELECT 1"))
                result.scalar()
                
                # Test database performance
                result = await conn.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.scalar()
                
                # Check for long-running queries (PostgreSQL specific)
                long_queries = 0
                if engine.dialect.name == 'postgresql':
                    try:
                        result = await conn.execute(text("""
                            SELECT COUNT(*) FROM pg_stat_activity 
                            WHERE state = 'active' AND query_start < NOW() - INTERVAL '30 seconds'
                        """))
                        long_queries = result.scalar()
                    except Exception as e:
                        logger.warning("Could not check long-running queries", error=str(e))
                        long_queries = 0
                else:
                    # For other databases, we can't easily check long-running queries
                    # This is a limitation of the health check for non-PostgreSQL databases
                    long_queries = None
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "user_count": user_count,
                "long_running_queries": long_queries,
                "connection_pool_size": engine.pool.size(),
                "database_type": engine.dialect.name,
                "checked_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "checked_at": datetime.utcnow().isoformat()
            }
    
    async def check_redis_health(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance."""
        try:
            start_time = time.time()
            redis_client = await self.get_redis_client()
            
            # Test basic connectivity
            await redis_client.ping()
            
            # Test set/get operations
            test_key = "health_check_test"
            test_value = f"test_{int(time.time())}"
            await redis_client.set(test_key, test_value, ex=60)
            retrieved_value = await redis_client.get(test_key)
            await redis_client.delete(test_key)
            
            # Get Redis info
            info = await redis_client.info()
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "checked_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error("Redis health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "checked_at": datetime.utcnow().isoformat()
            }
    
    async def check_celery_health(self) -> Dict[str, Any]:
        """Check Celery worker health and queue status."""
        try:
            from celery import Celery
            from app.tasks import celery_app
            
            # Get active workers
            inspect = celery_app.control.inspect()
            active_workers = inspect.active()
            registered_tasks = inspect.registered()
            
            # Get queue lengths
            queue_lengths = {}
            for queue_name in ['default', 'content_generation', 'style_analysis']:
                try:
                    queue_length = celery_app.control.inspect().active_queues()
                    queue_lengths[queue_name] = len(queue_length.get(queue_name, []))
                except:
                    queue_lengths[queue_name] = 0
            
            return {
                "status": "healthy",
                "active_workers": len(active_workers) if active_workers else 0,
                "registered_tasks": len(registered_tasks) if registered_tasks else 0,
                "queue_lengths": queue_lengths,
                "checked_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error("Celery health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "checked_at": datetime.utcnow().isoformat()
            }
    
    async def check_external_apis(self) -> Dict[str, Any]:
        """Check external API dependencies."""
        external_apis = {
            "openai": {
                "url": "https://api.openai.com/v1/models",
                "timeout": 10,
                "headers": {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"} if settings.OPENAI_API_KEY else {}
            },
            "aws_s3": {
                "url": f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/",
                "timeout": 10
            }
        }
        
        results = {}
        
        async with httpx.AsyncClient() as client:
            for api_name, config in external_apis.items():
                try:
                    start_time = time.time()
                    response = await client.get(
                        config["url"],
                        headers=config.get("headers", {}),
                        timeout=config["timeout"]
                    )
                    response_time = (time.time() - start_time) * 1000
                    
                    results[api_name] = {
                        "status": "healthy" if response.status_code < 400 else "unhealthy",
                        "response_time_ms": round(response_time, 2),
                        "status_code": response.status_code,
                        "checked_at": datetime.utcnow().isoformat()
                    }
                except Exception as e:
                    results[api_name] = {
                        "status": "unhealthy",
                        "error": str(e),
                        "checked_at": datetime.utcnow().isoformat()
                    }
        
        return results
    
    async def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available = memory.available / (1024**3)  # GB
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free = disk.free / (1024**3)  # GB
            
            # Load average (Unix only)
            try:
                load_avg = psutil.getloadavg()
            except AttributeError:
                load_avg = [0, 0, 0]
            
            return {
                "status": "healthy",
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": cpu_count,
                    "load_average": load_avg
                },
                "memory": {
                    "usage_percent": memory_percent,
                    "available_gb": round(memory_available, 2)
                },
                "disk": {
                    "usage_percent": disk_percent,
                    "free_gb": round(disk_free, 2)
                },
                "checked_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error("System resources health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "checked_at": datetime.utcnow().isoformat()
            }
    
    async def get_comprehensive_health(self) -> Dict[str, Any]:
        """Get comprehensive health status of all components."""
        # Check if we have cached results
        if (self.last_check and 
            datetime.utcnow() - self.last_check < timedelta(seconds=self.cache_ttl) and
            self.health_cache):
            return self.health_cache
        
        logger.info("Running comprehensive health check")
        
        # Run all health checks concurrently
        tasks = [
            self.check_database_health(),
            self.check_redis_health(),
            self.check_celery_health(),
            self.check_external_apis(),
            self.check_system_resources()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        health_status = {
            "overall_status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "0.1.0",
            "environment": settings.ENVIRONMENT,
            "components": {
                "database": results[0] if not isinstance(results[0], Exception) else {"status": "unhealthy", "error": str(results[0])},
                "redis": results[1] if not isinstance(results[1], Exception) else {"status": "unhealthy", "error": str(results[1])},
                "celery": results[2] if not isinstance(results[2], Exception) else {"status": "unhealthy", "error": str(results[2])},
                "external_apis": results[3] if not isinstance(results[3], Exception) else {"status": "unhealthy", "error": str(results[3])},
                "system_resources": results[4] if not isinstance(results[4], Exception) else {"status": "unhealthy", "error": str(results[4])}
            }
        }
        
        # Determine overall status
        unhealthy_components = [
            name for name, status in health_status["components"].items()
            if status.get("status") == "unhealthy"
        ]
        
        if unhealthy_components:
            health_status["overall_status"] = "unhealthy"
            health_status["unhealthy_components"] = unhealthy_components
        
        # Cache results
        self.health_cache = health_status
        self.last_check = datetime.utcnow()
        
        return health_status
    
    async def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of health status for quick checks."""
        comprehensive_health = await self.get_comprehensive_health()
        
        return {
            "status": comprehensive_health["overall_status"],
            "timestamp": comprehensive_health["timestamp"],
            "unhealthy_components": comprehensive_health.get("unhealthy_components", []),
            "response_time_ms": 0  # This would be calculated based on the check duration
        }
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.redis_client:
            await self.redis_client.close()


# Global health service instance
health_service = HealthService()
