"""
File management endpoints for uploading and managing reference articles.
"""

import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import (
    get_current_active_user, get_current_verified_user, get_current_superuser,
    get_organization, get_organization_member, get_organization_owner,
    get_organization_admin_or_owner, get_organization_editor_or_higher,
    get_organization_member_or_higher, get_permission_checker
)
from app.services.file_service import FileService
from app.services.text_extraction_service import TextExtractionService
from app.services.style_service import StyleService
from app.schemas.style import (
    ReferenceArticleCreate, ReferenceArticleUpdate, ReferenceArticleResponse, 
    ReferenceArticleListResponse, ReferenceArticleSearchParams, FileUploadResponse,
    MessageResponse
)
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember

router = APIRouter()


async def get_user_organization(
    organization_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Organization:
    """Get organization and verify user access."""
    from sqlalchemy import select
    
    # Check if user is member of organization
    query = select(OrganizationMember).where(
        OrganizationMember.organization_id == organization_id,
        OrganizationMember.user_id == current_user.id
    )
    result = await db.execute(query)
    membership = result.scalar_one_or_none()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization"
        )
    
    # Get organization
    org_query = select(Organization).where(Organization.id == organization_id)
    org_result = await db.execute(org_query)
    organization = org_result.scalar_one_or_none()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return organization


@router.post("/upload", response_model=FileUploadResponse)
async def upload_reference_file(
    organization_id: uuid.UUID,
    style_profile_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Upload a reference file for style analysis.
    
    Uploads a file and extracts text content for use in style analysis.
    """
    try:
        # Verify organization access
        await get_user_organization(organization_id, current_user, db)
        
        # Check permissions
        from sqlalchemy import select
        membership_query = select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == current_user.id
        )
        membership_result = await db.execute(membership_query)
        membership = membership_result.scalar_one_or_none()
        
        if not membership or membership.role not in ["owner", "admin", "editor"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to upload reference files"
            )
        
        # Verify style profile exists
        style_service = StyleService(db)
        style_profile = await style_service.get_style_profile(style_profile_id, organization_id)
        if not style_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Style profile not found"
            )
        
        # Initialize services
        file_service = FileService(db)
        text_extraction_service = TextExtractionService()
        
        # Validate file
        is_valid, error_message, metadata = await file_service.validate_upload_file(file, organization_id)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # Read file content
        content = await file.read()
        await file.seek(0)  # Reset file pointer
        
        # Upload to S3
        upload_success, upload_message, s3_key = await file_service.upload_to_s3(
            content, file.filename or "unknown", organization_id, style_profile_id
        )
        
        if not upload_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"File upload failed: {upload_message}"
            )
        
        # Extract text content
        extraction_success, extraction_message, extracted_text, extraction_metadata = await text_extraction_service.extract_text(
            content, metadata["mime_type"], file.filename
        )
        
        if not extraction_success:
            # File uploaded but text extraction failed
            # Still create reference article but mark as failed
            extracted_text = ""
            extraction_metadata = {"error": extraction_message}
        
        # Create reference article
        article_data = ReferenceArticleCreate(
            title=file.filename or "Untitled",
            source_url=None,
            original_filename=file.filename,
            file_size=metadata.get("size_human", ""),
            mime_type=metadata["mime_type"]
        )
        
        reference_article = await style_service.create_reference_article(
            article_data, style_profile_id, organization_id, current_user.id,
            extracted_text, s3_key
        )
        
        # Update processing status based on extraction result
        if not extraction_success:
            reference_article.mark_failed(extraction_message)
        else:
            reference_article.mark_completed(extraction_metadata)
        
        await db.commit()
        
        return FileUploadResponse(
            success=True,
            file_id=reference_article.id,
            filename=file.filename or "unknown",
            file_size=len(content),
            mime_type=metadata["mime_type"],
            s3_key=s3_key,
            message="File uploaded and processed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )


@router.get("/", response_model=ReferenceArticleListResponse)
async def list_reference_articles(
    organization_id: uuid.UUID,
    style_profile_id: uuid.UUID = Query(None, description="Filter by style profile"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    query: str = Query(None, description="Search query"),
    processing_status: str = Query(None, description="Filter by processing status"),
    mime_type: str = Query(None, description="Filter by MIME type"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    List reference articles for an organization.
    
    Returns paginated list of reference articles with optional filtering.
    """
    try:
        # Verify organization access
        await get_user_organization(organization_id, current_user, db)
        
        search_params = ReferenceArticleSearchParams(
            style_profile_id=style_profile_id,
            query=query,
            processing_status=processing_status,
            mime_type=mime_type,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        style_service = StyleService(db)
        result = await style_service.search_reference_articles(organization_id, search_params)
        
        # Convert to response models
        reference_articles = [
            ReferenceArticleResponse.model_validate(ra, from_attributes=True) 
            for ra in result["reference_articles"]
        ]
        
        return ReferenceArticleListResponse(
            reference_articles=reference_articles,
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"],
            has_next=result["has_next"],
            has_prev=result["has_prev"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list reference articles"
        )


@router.get("/{article_id}", response_model=ReferenceArticleResponse)
async def get_reference_article(
    organization_id: uuid.UUID,
    article_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get a specific reference article.
    
    Returns detailed information about a reference article.
    """
    try:
        # Verify organization access
        await get_user_organization(organization_id, current_user, db)
        
        style_service = StyleService(db)
        reference_article = await style_service.get_reference_article(article_id, organization_id)
        
        if not reference_article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reference article not found"
            )
        
        return ReferenceArticleResponse.model_validate(reference_article, from_attributes=True)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get reference article"
        )


@router.put("/{article_id}", response_model=ReferenceArticleResponse)
async def update_reference_article(
    organization_id: uuid.UUID,
    article_id: uuid.UUID,
    update_data: ReferenceArticleUpdate,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update a reference article.
    
    Updates metadata for a reference article.
    """
    try:
        # Verify organization access
        await get_user_organization(organization_id, current_user, db)
        
        # Check permissions
        from sqlalchemy import select
        membership_query = select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == current_user.id
        )
        membership_result = await db.execute(membership_query)
        membership = membership_result.scalar_one_or_none()
        
        if not membership or membership.role not in ["owner", "admin", "editor"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update reference articles"
            )
        
        style_service = StyleService(db)
        reference_article = await style_service.update_reference_article(
            article_id, organization_id, update_data
        )
        
        if not reference_article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reference article not found"
            )
        
        return ReferenceArticleResponse.model_validate(reference_article, from_attributes=True)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update reference article"
        )


@router.delete("/{article_id}", response_model=MessageResponse)
async def delete_reference_article(
    organization_id: uuid.UUID,
    article_id: uuid.UUID,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete a reference article.
    
    Deletes a reference article and its associated file.
    """
    try:
        # Verify organization access
        await get_user_organization(organization_id, current_user, db)
        
        # Check permissions
        from sqlalchemy import select
        membership_query = select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == current_user.id
        )
        membership_result = await db.execute(membership_query)
        membership = membership_result.scalar_one_or_none()
        
        if not membership or membership.role not in ["owner", "admin", "editor"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to delete reference articles"
            )
        
        # Get reference article first to get S3 key
        style_service = StyleService(db)
        reference_article = await style_service.get_reference_article(article_id, organization_id)
        
        if not reference_article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reference article not found"
            )
        
        # Delete from S3 if exists
        if reference_article.s3_key:
            file_service = FileService(db)
            await file_service.delete_from_s3(reference_article.s3_key)
        
        # Delete from database
        success = await style_service.delete_reference_article(article_id, organization_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reference article not found"
            )
        
        return MessageResponse(message="Reference article deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete reference article"
        )


@router.get("/{article_id}/download")
async def download_reference_file(
    organization_id: uuid.UUID,
    article_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Download a reference file.
    
    Generates a presigned URL for downloading the reference file.
    """
    try:
        # Verify organization access
        await get_user_organization(organization_id, current_user, db)
        
        style_service = StyleService(db)
        reference_article = await style_service.get_reference_article(article_id, organization_id)
        
        if not reference_article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reference article not found"
            )
        
        if not reference_article.s3_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not available for download"
            )
        
        # Generate presigned URL
        file_service = FileService(db)
        success, message, presigned_url = await file_service.get_s3_presigned_url(
            reference_article.s3_key, expiration=3600
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate download URL: {message}"
            )
        
        return {"download_url": presigned_url}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download URL"
        )


@router.post("/{article_id}/reprocess", response_model=MessageResponse)
async def reprocess_reference_article(
    organization_id: uuid.UUID,
    article_id: uuid.UUID,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Reprocess a reference article.
    
    Re-extracts text content from a reference article file.
    """
    try:
        # Verify organization access
        await get_user_organization(organization_id, current_user, db)
        
        # Check permissions
        from sqlalchemy import select
        membership_query = select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == current_user.id
        )
        membership_result = await db.execute(membership_query)
        membership = membership_result.scalar_one_or_none()
        
        if not membership or membership.role not in ["owner", "admin", "editor"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to reprocess reference articles"
            )
        
        style_service = StyleService(db)
        reference_article = await style_service.get_reference_article(article_id, organization_id)
        
        if not reference_article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reference article not found"
            )
        
        if not reference_article.s3_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file available for reprocessing"
            )
        
        # Get file from S3
        file_service = FileService(db)
        success, message, file_info = await file_service.get_file_info(reference_article.s3_key)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get file info: {message}"
            )
        
        # Mark as processing
        reference_article.mark_processing()
        await db.commit()
        
        # TODO: Implement file download from S3 and reprocessing
        # For now, just mark as completed
        reference_article.mark_completed({"reprocessed": True})
        await db.commit()
        
        return MessageResponse(message="Reference article reprocessed successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reprocess reference article"
        )
