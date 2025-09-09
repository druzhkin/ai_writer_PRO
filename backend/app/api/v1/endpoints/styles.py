"""
Style management endpoints for creating and managing writing styles.
"""

import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import (
    get_current_active_user, get_current_verified_user, get_current_superuser,
    get_organization, get_organization_member, get_organization_owner,
    get_organization_admin_or_owner, get_organization_editor_or_higher,
    get_organization_member_or_higher, get_permission_checker
)
from app.services.style_service import StyleService
from app.schemas.style import (
    StyleProfileCreate, StyleProfileUpdate, StyleProfileResponse, StyleProfileListResponse,
    StyleSearchParams, AnalysisRequest, AnalysisResponse, StyleStatsResponse,
    BulkStyleAction, MessageResponse
)
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember

router = APIRouter()


# Use existing auth dependency functions for consistency


@router.post("/", response_model=StyleProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_style_profile(
    organization_id: uuid.UUID,
    style_data: StyleProfileCreate,
    current_user: User = Depends(get_current_verified_user),
    organization: Organization = Depends(get_organization),
    membership: OrganizationMember = Depends(get_organization_editor_or_higher),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a new style profile.
    
    Creates a new writing style profile for the organization.
    """
    try:
        style_service = StyleService(db)
        style_profile = await style_service.create_style_profile(
            style_data, organization_id, current_user.id
        )
        
        return StyleProfileResponse.model_validate(style_profile, from_attributes=True)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create style profile"
        )


@router.get("/", response_model=StyleProfileListResponse)
async def list_style_profiles(
    organization_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    query: str = Query(None, description="Search query"),
    tags: List[str] = Query(None, description="Filter by tags"),
    is_public: bool = Query(None, description="Filter by public status"),
    is_analyzed: bool = Query(None, description="Filter by analysis status"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order"),
    current_user: User = Depends(get_current_active_user),
    organization: Organization = Depends(get_organization),
    membership: OrganizationMember = Depends(get_organization_member_or_higher),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    List style profiles for an organization.
    
    Returns paginated list of style profiles with optional filtering.
    """
    try:
        search_params = StyleSearchParams(
            query=query,
            tags=tags,
            is_public=is_public,
            is_analyzed=is_analyzed,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        style_service = StyleService(db)
        result = await style_service.search_style_profiles(organization_id, search_params)
        
        # Convert to response models
        style_profiles = [
            StyleProfileResponse.model_validate(sp, from_attributes=True) 
            for sp in result["style_profiles"]
        ]
        
        return StyleProfileListResponse(
            style_profiles=style_profiles,
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
            detail="Failed to list style profiles"
        )


@router.get("/{style_profile_id}", response_model=StyleProfileResponse)
async def get_style_profile(
    organization_id: uuid.UUID,
    style_profile_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get a specific style profile.
    
    Returns detailed information about a style profile.
    """
    try:
        # Verify organization access
        await get_user_organization(organization_id, current_user, db)
        
        style_service = StyleService(db)
        style_profile = await style_service.get_style_profile(style_profile_id, organization_id)
        
        if not style_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Style profile not found"
            )
        
        return StyleProfileResponse.model_validate(style_profile, from_attributes=True)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get style profile"
        )


@router.put("/{style_profile_id}", response_model=StyleProfileResponse)
async def update_style_profile(
    organization_id: uuid.UUID,
    style_profile_id: uuid.UUID,
    update_data: StyleProfileUpdate,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update a style profile.
    
    Updates an existing style profile.
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
                detail="Insufficient permissions to update style profiles"
            )
        
        style_service = StyleService(db)
        style_profile = await style_service.update_style_profile(
            style_profile_id, organization_id, update_data
        )
        
        if not style_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Style profile not found"
            )
        
        return StyleProfileResponse.model_validate(style_profile, from_attributes=True)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update style profile"
        )


@router.delete("/{style_profile_id}", response_model=MessageResponse)
async def delete_style_profile(
    organization_id: uuid.UUID,
    style_profile_id: uuid.UUID,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete a style profile.
    
    Deletes a style profile and all associated reference articles.
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
        
        if not membership or membership.role not in ["owner", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to delete style profiles"
            )
        
        style_service = StyleService(db)
        success = await style_service.delete_style_profile(style_profile_id, organization_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Style profile not found"
            )
        
        return MessageResponse(message="Style profile deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete style profile"
        )


@router.post("/{style_profile_id}/analyze", response_model=AnalysisResponse)
async def analyze_style_profile(
    organization_id: uuid.UUID,
    style_profile_id: uuid.UUID,
    analysis_request: AnalysisRequest,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Analyze a style profile.
    
    Triggers AI analysis of the style profile using reference articles.
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
                detail="Insufficient permissions to analyze style profiles"
            )
        
        style_service = StyleService(db)
        success, message, analysis_result = await style_service.analyze_style_profile(
            style_profile_id, organization_id, analysis_request.force_reanalysis
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        return AnalysisResponse(
            success=True,
            analysis_result=analysis_result,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze style profile"
        )


@router.get("/stats/overview", response_model=StyleStatsResponse)
async def get_style_stats(
    organization_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get style profile statistics.
    
    Returns statistics about style profiles and reference articles.
    """
    try:
        # Verify organization access
        await get_user_organization(organization_id, current_user, db)
        
        style_service = StyleService(db)
        stats = await style_service.get_style_profile_stats(organization_id)
        
        # Add placeholder data for missing fields
        stats.update({
            "total_tags": 0,  # TODO: Calculate from all style profiles
            "most_used_tags": [],  # TODO: Calculate from all style profiles
            "recent_activity": []  # TODO: Get recent activity
        })
        
        return StyleStatsResponse(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get style statistics"
        )


@router.post("/bulk-action", response_model=MessageResponse)
async def bulk_style_action(
    organization_id: uuid.UUID,
    action_data: BulkStyleAction,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Perform bulk action on style profiles.
    
    Performs bulk operations on multiple style profiles.
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
        
        if not membership or membership.role not in ["owner", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for bulk actions"
            )
        
        style_service = StyleService(db)
        success_count = 0
        
        for style_profile_id in action_data.style_profile_ids:
            try:
                if action_data.action == "activate":
                    style_profile = await style_service.get_style_profile(style_profile_id, organization_id)
                    if style_profile:
                        style_profile.is_active = True
                        success_count += 1
                elif action_data.action == "deactivate":
                    style_profile = await style_service.get_style_profile(style_profile_id, organization_id)
                    if style_profile:
                        style_profile.is_active = False
                        success_count += 1
                elif action_data.action == "delete":
                    if await style_service.delete_style_profile(style_profile_id, organization_id):
                        success_count += 1
                elif action_data.action == "analyze":
                    success, _, _ = await style_service.analyze_style_profile(style_profile_id, organization_id)
                    if success:
                        success_count += 1
            except Exception:
                continue  # Skip failed items
        
        await db.commit()
        
        return MessageResponse(
            message=f"Bulk action '{action_data.action}' completed on {success_count} style profiles"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk action"
        )
