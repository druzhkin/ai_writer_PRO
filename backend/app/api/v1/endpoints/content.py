"""
Content generation endpoints for AI-generated content management.
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_active_user, get_current_verified_user
from app.services.content_service import ContentService
from app.schemas.content import (
    ContentGenerationRequest, ContentGenerationResponse, ContentUpdateRequest,
    ContentEditRequest, ContentEditResponse, ContentSearchParams, ContentSearchResponse,
    ContentDetailResponse, ContentListResponse, ContentStatsResponse, ContentBulkAction,
    ContentExportRequest, ContentExportResponse, ContentIterationResponse
)
from app.models.user import User

router = APIRouter()


@router.post("/generate", response_model=ContentGenerationResponse, status_code=status.HTTP_201_CREATED)
async def generate_content(
    organization_id: uuid.UUID,
    request: ContentGenerationRequest,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Generate new content using AI.
    
    Creates new AI-generated content based on the provided request parameters.
    Supports different content types, style profiles, and custom instructions.
    """
    try:
        content_service = ContentService()
        
        success, error_msg, response = await content_service.generate_content(
            db=db,
            request=request,
            organization_id=organization_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content generation failed: {str(e)}"
        )


@router.get("/", response_model=ContentSearchResponse)
async def list_content(
    organization_id: uuid.UUID,
    query: str = Query(None, description="Search query for title and content"),
    content_type: str = Query(None, description="Filter by content type"),
    status: str = Query(None, description="Filter by status"),
    style_profile_id: uuid.UUID = Query(None, description="Filter by style profile"),
    created_by_id: uuid.UUID = Query(None, description="Filter by creator"),
    is_archived: bool = Query(None, description="Filter by archived status"),
    min_word_count: int = Query(None, ge=0, description="Minimum word count"),
    max_word_count: int = Query(None, ge=0, description="Maximum word count"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    List content with filtering and pagination.
    
    Returns a paginated list of content with optional filtering by various criteria.
    """
    try:
        content_service = ContentService()
        
        search_params = ContentSearchParams(
            query=query,
            content_type=content_type,
            status=status,
            style_profile_id=style_profile_id,
            created_by_id=created_by_id,
            is_archived=is_archived,
            min_word_count=min_word_count,
            max_word_count=max_word_count,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        response = await content_service.list_content(
            db=db,
            organization_id=organization_id,
            search_params=search_params
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list content: {str(e)}"
        )


@router.get("/{content_id}", response_model=ContentDetailResponse)
async def get_content(
    organization_id: uuid.UUID,
    content_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get content by ID with full details.
    
    Returns detailed information about a specific content piece including
    all iterations and metadata.
    """
    try:
        content_service = ContentService()
        
        response = await content_service.get_content(
            db=db,
            content_id=content_id,
            organization_id=organization_id
        )
        
        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get content: {str(e)}"
        )


@router.put("/{content_id}", response_model=ContentGenerationResponse)
async def update_content(
    organization_id: uuid.UUID,
    content_id: uuid.UUID,
    request: ContentUpdateRequest,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update content metadata.
    
    Updates the title, brief, or archived status of existing content.
    """
    try:
        content_service = ContentService()
        
        success, error_msg, response = await content_service.update_content(
            db=db,
            content_id=content_id,
            request=request,
            organization_id=organization_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update content: {str(e)}"
        )


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    organization_id: uuid.UUID,
    content_id: uuid.UUID,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete content.
    
    Permanently deletes content and all its iterations.
    """
    try:
        content_service = ContentService()
        
        success, error_msg = await content_service.delete_content(
            db=db,
            content_id=content_id,
            organization_id=organization_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete content: {str(e)}"
        )


@router.post("/{content_id}/edit", response_model=ContentEditResponse, status_code=status.HTTP_201_CREATED)
async def edit_content(
    organization_id: uuid.UUID,
    content_id: uuid.UUID,
    request: ContentEditRequest,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Edit existing content using AI.
    
    Creates a new iteration of the content with AI-powered edits based on the provided prompt.
    """
    try:
        content_service = ContentService()
        
        success, error_msg, response = await content_service.edit_content(
            db=db,
            content_id=content_id,
            request=request,
            organization_id=organization_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content editing failed: {str(e)}"
        )


@router.get("/{content_id}/iterations", response_model=List[ContentIterationResponse])
async def get_content_iterations(
    organization_id: uuid.UUID,
    content_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get all iterations for a content piece.
    
    Returns a list of all editing iterations for the specified content.
    """
    try:
        content_service = ContentService()
        
        iterations = await content_service.get_content_iterations(
            db=db,
            content_id=content_id,
            organization_id=organization_id
        )
        
        return iterations
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get content iterations: {str(e)}"
        )


@router.get("/stats/overview", response_model=ContentStatsResponse)
async def get_content_stats(
    organization_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get content statistics for organization.
    
    Returns comprehensive statistics about content generation, usage, and performance.
    """
    try:
        content_service = ContentService()
        
        stats = await content_service.get_content_stats(
            db=db,
            organization_id=organization_id
        )
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get content stats: {str(e)}"
        )


@router.post("/bulk-action", status_code=status.HTTP_200_OK)
async def bulk_content_action(
    organization_id: uuid.UUID,
    request: ContentBulkAction,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Perform bulk actions on multiple content pieces.
    
    Supports bulk archive, unarchive, and delete operations.
    """
    try:
        content_service = ContentService()
        
        # This would be implemented in the content service
        # For now, return a placeholder response
        return {
            "message": f"Bulk {request.action} action completed",
            "affected_count": len(request.content_ids),
            "action": request.action
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk action failed: {str(e)}"
        )


@router.post("/export", response_model=ContentExportResponse, status_code=status.HTTP_202_ACCEPTED)
async def export_content(
    organization_id: uuid.UUID,
    request: ContentExportRequest,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Export content in various formats.
    
    Initiates an export job for content in JSON, Markdown, or HTML format.
    Returns an export job ID for tracking progress.
    """
    try:
        # This would be implemented as a background task
        # For now, return a placeholder response
        export_id = uuid.uuid4()
        
        return ContentExportResponse(
            export_id=export_id,
            status="pending",
            download_url=None,
            expires_at=datetime.utcnow() + timedelta(hours=24),
            created_at=datetime.utcnow(),
            content_count=0
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.get("/export/{export_id}", response_model=ContentExportResponse)
async def get_export_status(
    organization_id: uuid.UUID,
    export_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get export job status.
    
    Returns the current status of an export job and download URL when ready.
    """
    try:
        # This would check the actual export job status
        # For now, return a placeholder response
        return ContentExportResponse(
            export_id=export_id,
            status="completed",
            download_url="https://example.com/exports/sample-export.json",
            expires_at=datetime.utcnow() + timedelta(hours=24),
            created_at=datetime.utcnow(),
            content_count=10
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get export status: {str(e)}"
        )
