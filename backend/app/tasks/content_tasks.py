"""
Celery tasks for content generation and processing.
"""

import uuid
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from celery import Celery
from celery.exceptions import Retry
# Removed tenacity imports as we're using Celery's built-in retry mechanism

from app.core.config import settings
from app.services.content_service import ContentService
from app.services.usage_service import UsageService
from app.services.openai_service import OpenAIService
from app.core.database import get_async_session
from app.schemas.content import ContentGenerationRequest, ContentEditRequest, ContentType, EditType


# Initialize Celery
celery_app = Celery(
    "ai_writer",
    broker=settings.RABBITMQ_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.content_tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.CONTENT_GENERATION_TIMEOUT,
    task_soft_time_limit=settings.CONTENT_GENERATION_TIMEOUT - 30,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
)


def run_async_in_celery(async_func):
    """
    Helper function to run async functions in Celery tasks without blocking.
    Uses the current event loop if available, otherwise creates a new one.
    """
    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, we need to use a different approach
            # Create a new task in the current loop
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, async_func())
                return future.result()
        else:
            # No running loop, we can use asyncio.run safely
            return asyncio.run(async_func())
    except RuntimeError:
        # No event loop exists, create a new one
        return asyncio.run(async_func())


@celery_app.task(bind=True, max_retries=3)
def generate_content_task(
    self,
    request_data: Dict[str, Any],
    organization_id: str,
    user_id: str
) -> Dict[str, Any]:
    """
    Background task for content generation.
    
    Args:
        request_data: Content generation request data
        organization_id: Organization ID
        user_id: User ID
        
    Returns:
        Dictionary with generation result
    """
    try:
        # Convert string IDs to UUIDs
        org_id = uuid.UUID(organization_id)
        user_uuid = uuid.UUID(user_id)
        
        # Create request object
        request = ContentGenerationRequest(**request_data)
        
        # Get database session
        async def _generate():
            async with get_async_session() as db:
                content_service = ContentService()
                
                success, error_msg, response = await content_service.generate_content(
                    db=db,
                    request=request,
                    organization_id=org_id,
                    user_id=user_uuid
                )
                
                return success, error_msg, response
        
        # Run async function using helper
        success, error_msg, response = run_async_in_celery(_generate)
        
        if not success:
            raise Exception(f"Content generation failed: {error_msg}")
        
        return {
            "success": True,
            "content_id": str(response.id),
            "title": response.title,
            "word_count": response.word_count,
            "estimated_cost": response.estimated_cost,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        # Log error and retry if possible
        self.retry(countdown=60, exc=e)


@celery_app.task(bind=True, max_retries=3)
def edit_content_task(
    self,
    content_id: str,
    request_data: Dict[str, Any],
    organization_id: str,
    user_id: str
) -> Dict[str, Any]:
    """
    Background task for content editing.
    
    Args:
        content_id: Content ID to edit
        request_data: Content edit request data
        organization_id: Organization ID
        user_id: User ID
        
    Returns:
        Dictionary with edit result
    """
    try:
        # Convert string IDs to UUIDs
        content_uuid = uuid.UUID(content_id)
        org_id = uuid.UUID(organization_id)
        user_uuid = uuid.UUID(user_id)
        
        # Create request object
        request = ContentEditRequest(**request_data)
        
        # Get database session
        async def _edit():
            async with get_async_session() as db:
                content_service = ContentService()
                
                success, error_msg, response = await content_service.edit_content(
                    db=db,
                    content_id=content_uuid,
                    request=request,
                    organization_id=org_id,
                    user_id=user_uuid
                )
                
                return success, error_msg, response
        
        # Run async function using helper
        success, error_msg, response = run_async_in_celery(_edit)
        
        if not success:
            raise Exception(f"Content editing failed: {error_msg}")
        
        return {
            "success": True,
            "iteration_id": str(response.id),
            "iteration_number": response.iteration_number,
            "word_count_change": response.word_count_change,
            "estimated_cost": response.estimated_cost,
            "edited_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        # Log error and retry if possible
        self.retry(countdown=60, exc=e)


@celery_app.task(bind=True, max_retries=2)
def batch_content_generation_task(
    self,
    batch_requests: List[Dict[str, Any]],
    organization_id: str,
    user_id: str
) -> Dict[str, Any]:
    """
    Background task for batch content generation.
    
    Args:
        batch_requests: List of content generation requests
        organization_id: Organization ID
        user_id: User ID
        
    Returns:
        Dictionary with batch generation results
    """
    try:
        results = []
        successful_count = 0
        failed_count = 0
        
        for i, request_data in enumerate(batch_requests):
            try:
                # Update task progress
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "current": i + 1,
                        "total": len(batch_requests),
                        "status": f"Processing request {i + 1} of {len(batch_requests)}"
                    }
                )
                
                # Generate content
                result = generate_content_task.apply_async(
                    args=[request_data, organization_id, user_id],
                    countdown=i * 5  # Stagger requests by 5 seconds
                ).get()
                
                if result.get("success"):
                    successful_count += 1
                    results.append({
                        "index": i,
                        "success": True,
                        "content_id": result["content_id"],
                        "title": result["title"]
                    })
                else:
                    failed_count += 1
                    results.append({
                        "index": i,
                        "success": False,
                        "error": result.get("error", "Unknown error")
                    })
                    
            except Exception as e:
                failed_count += 1
                results.append({
                    "index": i,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "total_requests": len(batch_requests),
            "successful_count": successful_count,
            "failed_count": failed_count,
            "results": results,
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "total_requests": len(batch_requests),
            "successful_count": successful_count,
            "failed_count": failed_count,
            "results": results
        }


@celery_app.task(bind=True, max_retries=2)
def cleanup_old_content_task(
    self,
    organization_id: Optional[str] = None,
    days_old: int = 90
) -> Dict[str, Any]:
    """
    Background task for cleaning up old content.
    
    Args:
        organization_id: Optional organization ID to limit cleanup
        days_old: Number of days old content to clean up
        
    Returns:
        Dictionary with cleanup results
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        async def _cleanup():
            async with get_async_session() as db:
                from app.models.generated_content import GeneratedContent
                from sqlalchemy import select, and_
                
                # Build query
                query = select(GeneratedContent).where(
                    and_(
                        GeneratedContent.created_at < cutoff_date,
                        GeneratedContent.is_archived == True
                    )
                )
                
                if organization_id:
                    org_id = uuid.UUID(organization_id)
                    query = query.where(GeneratedContent.organization_id == org_id)
                
                # Execute query
                result = await db.execute(query)
                old_content = result.scalars().all()
                
                # Delete old content
                deleted_count = 0
                for content in old_content:
                    await db.delete(content)
                    deleted_count += 1
                
                await db.commit()
                return deleted_count
        
        # Run async function using helper
        deleted_count = run_async_in_celery(_cleanup)
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
            "cleaned_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "deleted_count": 0
        }


@celery_app.task(bind=True, max_retries=2)
def generate_usage_analytics_task(
    self,
    organization_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Background task for generating usage analytics.
    
    Args:
        organization_id: Organization ID
        start_date: Start date for analytics (ISO format)
        end_date: End date for analytics (ISO format)
        
    Returns:
        Dictionary with analytics results
    """
    try:
        org_id = uuid.UUID(organization_id)
        
        # Parse dates
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        async def _generate_analytics():
            async with get_async_session() as db:
                usage_service = UsageService()
                
                analytics = await usage_service.get_usage_analytics(
                    db=db,
                    organization_id=org_id,
                    start_date=start_dt.date() if start_dt else None,
                    end_date=end_dt.date() if end_dt else None
                )
                
                return analytics
        
        # Run async function using helper
        analytics = run_async_in_celery(_generate_analytics)
        
        return {
            "success": True,
            "analytics": analytics,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "analytics": None
        }


@celery_app.task(bind=True, max_retries=2)
def export_content_task(
    self,
    content_ids: List[str],
    organization_id: str,
    export_format: str = "json",
    include_iterations: bool = True
) -> Dict[str, Any]:
    """
    Background task for content export.
    
    Args:
        content_ids: List of content IDs to export
        organization_id: Organization ID
        export_format: Export format (json, markdown, html)
        include_iterations: Whether to include iterations
        
    Returns:
        Dictionary with export results
    """
    try:
        org_id = uuid.UUID(organization_id)
        content_uuids = [uuid.UUID(cid) for cid in content_ids]
        
        async def _export():
            async with get_async_session() as db:
                content_service = ContentService()
                
                # Get content details
                exported_content = []
                for content_id in content_uuids:
                    content = await content_service.get_content(
                        db=db,
                        content_id=content_id,
                        organization_id=org_id
                    )
                    
                    if content:
                        content_data = {
                            "id": str(content.id),
                            "title": content.title,
                            "brief": content.brief,
                            "content_type": content.content_type,
                            "generated_text": content.generated_text,
                            "word_count": content.word_count,
                            "created_at": content.created_at.isoformat(),
                            "updated_at": content.updated_at.isoformat()
                        }
                        
                        if include_iterations:
                            iterations = await content_service.get_content_iterations(
                                db=db,
                                content_id=content_id,
                                organization_id=org_id
                            )
                            content_data["iterations"] = [
                                {
                                    "iteration_number": iter.iteration_number,
                                    "edit_prompt": iter.edit_prompt,
                                    "edit_type": iter.edit_type,
                                    "word_count_change": iter.word_count_change,
                                    "created_at": iter.created_at.isoformat()
                                }
                                for iter in iterations
                            ]
                        
                        exported_content.append(content_data)
                
                return exported_content
        
        # Run async function using helper
        exported_content = run_async_in_celery(_export)
        
        # Generate export file (simplified - in real implementation, save to S3)
        export_id = str(uuid.uuid4())
        export_data = {
            "export_id": export_id,
            "exported_at": datetime.utcnow().isoformat(),
            "format": export_format,
            "content_count": len(exported_content),
            "content": exported_content
        }
        
        return {
            "success": True,
            "export_id": export_id,
            "export_data": export_data,
            "download_url": f"https://example.com/exports/{export_id}.{export_format}",
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "export_id": None
        }


@celery_app.task(bind=True, max_retries=1)
def send_content_notification_task(
    self,
    content_id: str,
    organization_id: str,
    user_id: str,
    notification_type: str = "generation_complete"
) -> Dict[str, Any]:
    """
    Background task for sending content notifications.
    
    Args:
        content_id: Content ID
        organization_id: Organization ID
        user_id: User ID
        notification_type: Type of notification
        
    Returns:
        Dictionary with notification result
    """
    try:
        # This would integrate with email service or push notifications
        # For now, just return success
        
        return {
            "success": True,
            "content_id": content_id,
            "notification_type": notification_type,
            "sent_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "content_id": content_id
        }


@celery_app.task(bind=True, max_retries=1)
def update_content_metrics_task(
    self,
    content_id: str,
    organization_id: str
) -> Dict[str, Any]:
    """
    Background task for updating content metrics.
    
    Args:
        content_id: Content ID
        organization_id: Organization ID
        
    Returns:
        Dictionary with metrics update result
    """
    try:
        content_uuid = uuid.UUID(content_id)
        org_id = uuid.UUID(organization_id)
        
        async def _update_metrics():
            async with get_async_session() as db:
                from app.models.generated_content import GeneratedContent
                from app.utils.content_utils import calculate_content_metrics
                from sqlalchemy import select, and_
                
                # Get content
                result = await db.execute(
                    select(GeneratedContent).where(
                        and_(
                            GeneratedContent.id == content_uuid,
                            GeneratedContent.organization_id == org_id
                        )
                    )
                )
                content = result.scalar_one_or_none()
                
                if not content:
                    return False
                
                # Calculate updated metrics
                metrics = calculate_content_metrics(content.generated_text)
                
                # Update content
                content.word_count = metrics.word_count
                content.character_count = metrics.character_count
                content.updated_at = datetime.utcnow()
                
                await db.commit()
                return True
        
        # Run async function using helper
        success = run_async_in_celery(_update_metrics)
        
        return {
            "success": success,
            "content_id": content_id,
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "content_id": content_id
        }
