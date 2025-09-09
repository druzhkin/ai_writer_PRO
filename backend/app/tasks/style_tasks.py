"""
Celery tasks for style processing and analysis.
"""

import uuid
from typing import Dict, Any, Optional
from celery import Celery
from celery.exceptions import Retry
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.services.text_extraction_service import TextExtractionService
from app.services.openai_service import OpenAIService
from app.services.file_service import FileService
from app.services.style_service import StyleService
from app.core.database import get_async_session


# Initialize Celery
celery_app = Celery(
    "ai_writer",
    broker=settings.RABBITMQ_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.style_tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
)


@celery_app.task(bind=True, max_retries=3)
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def process_reference_article_task(
    self, 
    article_id: str, 
    organization_id: str,
    s3_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process a reference article: extract text and update database.
    
    Args:
        article_id: UUID of the reference article
        organization_id: UUID of the organization
        s3_key: Optional S3 key for file location
        
    Returns:
        Processing result dictionary
    """
    try:
        # Convert string UUIDs to UUID objects
        article_uuid = uuid.UUID(article_id)
        org_uuid = uuid.UUID(organization_id)
        
        # Get database session
        async def process_article():
            async with get_async_session() as db:
                # Get services
                style_service = StyleService(db)
                text_extraction_service = TextExtractionService()
                file_service = FileService(db)
                
                # Get reference article
                reference_article = await style_service.get_reference_article(article_uuid, org_uuid)
                if not reference_article:
                    return {"success": False, "error": "Reference article not found"}
                
                # Mark as processing
                reference_article.mark_processing()
                await db.commit()
                
                try:
                    # If we have S3 key, download file
                    if s3_key:
                        # TODO: Implement S3 file download
                        # For now, assume content is already in the database
                        content = reference_article.content.encode('utf-8') if reference_article.content else b""
                    else:
                        content = reference_article.content.encode('utf-8') if reference_article.content else b""
                    
                    # Extract text if not already extracted
                    if not reference_article.content and content:
                        success, message, extracted_text, metadata = await text_extraction_service.extract_text(
                            content, reference_article.mime_type or "text/plain", reference_article.original_filename
                        )
                        
                        if success and extracted_text:
                            reference_article.content = extracted_text
                            reference_article.mark_completed(metadata)
                        else:
                            reference_article.mark_failed(message)
                    else:
                        # Content already exists, mark as completed
                        reference_article.mark_completed({"already_processed": True})
                    
                    await db.commit()
                    
                    return {
                        "success": True,
                        "article_id": str(article_uuid),
                        "processing_status": reference_article.processing_status,
                        "content_length": len(reference_article.content) if reference_article.content else 0
                    }
                    
                except Exception as e:
                    reference_article.mark_failed(str(e))
                    await db.commit()
                    raise e
        
        # Run async function
        import asyncio
        return asyncio.run(process_article())
        
    except Exception as e:
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            "success": False,
            "error": f"Processing failed after {self.max_retries} retries: {str(e)}",
            "article_id": article_id
        }


@celery_app.task(bind=True, max_retries=2)
@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=5, max=15)
)
def analyze_style_profile_task(
    self, 
    style_profile_id: str, 
    organization_id: str,
    force_reanalysis: bool = False
) -> Dict[str, Any]:
    """
    Analyze a style profile using reference articles.
    
    Args:
        style_profile_id: UUID of the style profile
        organization_id: UUID of the organization
        force_reanalysis: Whether to force reanalysis
        
    Returns:
        Analysis result dictionary
    """
    try:
        # Convert string UUIDs to UUID objects
        style_uuid = uuid.UUID(style_profile_id)
        org_uuid = uuid.UUID(organization_id)
        
        # Get database session
        async def analyze_style():
            async with get_async_session() as db:
                style_service = StyleService(db)
                
                # Perform analysis
                success, message, analysis_result = await style_service.analyze_style_profile(
                    style_uuid, org_uuid, force_reanalysis
                )
                
                if success:
                    return {
                        "success": True,
                        "style_profile_id": str(style_uuid),
                        "analysis_completed": True,
                        "analysis_keys": list(analysis_result.keys()) if analysis_result else [],
                        "message": message
                    }
                else:
                    return {
                        "success": False,
                        "error": message,
                        "style_profile_id": str(style_uuid)
                    }
        
        # Run async function
        import asyncio
        return asyncio.run(analyze_style())
        
    except Exception as e:
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=120 * (2 ** self.request.retries))
        
        return {
            "success": False,
            "error": f"Analysis failed after {self.max_retries} retries: {str(e)}",
            "style_profile_id": style_profile_id
        }


@celery_app.task(bind=True)
def cleanup_failed_uploads_task(self, organization_id: str) -> Dict[str, Any]:
    """
    Clean up failed uploads and orphaned files.
    
    Args:
        organization_id: UUID of the organization
        
    Returns:
        Cleanup result dictionary
    """
    try:
        # Convert string UUID to UUID object
        org_uuid = uuid.UUID(organization_id)
        
        # Get database session
        async def cleanup():
            async with get_async_session() as db:
                from sqlalchemy import select
                from app.models.reference_article import ReferenceArticle
                
                # Find failed uploads older than 24 hours
                from datetime import datetime, timedelta
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                
                query = select(ReferenceArticle).where(
                    ReferenceArticle.organization_id == org_uuid,
                    ReferenceArticle.processing_status == "failed",
                    ReferenceArticle.created_at < cutoff_time
                )
                
                result = await db.execute(query)
                failed_articles = result.scalars().all()
                
                cleanup_count = 0
                for article in failed_articles:
                    try:
                        # Delete from S3 if exists
                        if article.s3_key:
                            file_service = FileService(db)
                            await file_service.delete_from_s3(article.s3_key)
                        
                        # Delete from database
                        await db.delete(article)
                        cleanup_count += 1
                    except Exception as e:
                        print(f"Failed to cleanup article {article.id}: {e}")
                        continue
                
                await db.commit()
                
                return {
                    "success": True,
                    "organization_id": str(org_uuid),
                    "cleanup_count": cleanup_count,
                    "message": f"Cleaned up {cleanup_count} failed uploads"
                }
        
        # Run async function
        import asyncio
        return asyncio.run(cleanup())
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Cleanup failed: {str(e)}",
            "organization_id": organization_id
        }


@celery_app.task(bind=True)
def generate_style_guidelines_task(
    self, 
    style_profile_id: str, 
    organization_id: str
) -> Dict[str, Any]:
    """
    Generate style guidelines from analysis.
    
    Args:
        style_profile_id: UUID of the style profile
        organization_id: UUID of the organization
        
    Returns:
        Guidelines generation result
    """
    try:
        # Convert string UUIDs to UUID objects
        style_uuid = uuid.UUID(style_profile_id)
        org_uuid = uuid.UUID(organization_id)
        
        # Get database session
        async def generate_guidelines():
            async with get_async_session() as db:
                style_service = StyleService(db)
                openai_service = OpenAIService()
                
                # Get style profile
                style_profile = await style_service.get_style_profile(style_uuid, org_uuid)
                if not style_profile:
                    return {"success": False, "error": "Style profile not found"}
                
                if not style_profile.analysis:
                    return {"success": False, "error": "Style profile not analyzed"}
                
                # Generate guidelines
                success, message, guidelines = await openai_service.generate_style_guidelines(
                    style_profile.analysis, style_profile.name
                )
                
                if success:
                    # Store guidelines in analysis data
                    if not style_profile.analysis:
                        style_profile.analysis = {}
                    
                    style_profile.analysis["guidelines"] = guidelines
                    await db.commit()
                    
                    return {
                        "success": True,
                        "style_profile_id": str(style_uuid),
                        "guidelines_generated": True,
                        "message": "Style guidelines generated successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": message,
                        "style_profile_id": str(style_uuid)
                    }
        
        # Run async function
        import asyncio
        return asyncio.run(generate_guidelines())
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Guidelines generation failed: {str(e)}",
            "style_profile_id": style_profile_id
        }


@celery_app.task(bind=True)
def bulk_analyze_style_profiles_task(
    self, 
    style_profile_ids: list, 
    organization_id: str
) -> Dict[str, Any]:
    """
    Analyze multiple style profiles in bulk.
    
    Args:
        style_profile_ids: List of style profile UUIDs
        organization_id: UUID of the organization
        
    Returns:
        Bulk analysis result
    """
    try:
        # Convert string UUIDs to UUID objects
        style_uuids = [uuid.UUID(sid) for sid in style_profile_ids]
        org_uuid = uuid.UUID(organization_id)
        
        # Get database session
        async def bulk_analyze():
            async with get_async_session() as db:
                style_service = StyleService(db)
                
                results = []
                success_count = 0
                
                for style_uuid in style_uuids:
                    try:
                        success, message, analysis_result = await style_service.analyze_style_profile(
                            style_uuid, org_uuid, force_reanalysis=False
                        )
                        
                        results.append({
                            "style_profile_id": str(style_uuid),
                            "success": success,
                            "message": message
                        })
                        
                        if success:
                            success_count += 1
                            
                    except Exception as e:
                        results.append({
                            "style_profile_id": str(style_uuid),
                            "success": False,
                            "error": str(e)
                        })
                
                return {
                    "success": True,
                    "organization_id": str(org_uuid),
                    "total_processed": len(style_uuids),
                    "successful_analyses": success_count,
                    "failed_analyses": len(style_uuids) - success_count,
                    "results": results
                }
        
        # Run async function
        import asyncio
        return asyncio.run(bulk_analyze())
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Bulk analysis failed: {str(e)}",
            "organization_id": organization_id
        }
