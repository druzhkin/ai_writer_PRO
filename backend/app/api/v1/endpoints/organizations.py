"""
Organization management endpoints for creating, updating, and managing organizations.
"""

import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import (
    get_current_active_user, get_current_verified_user, get_current_superuser,
    get_organization, get_organization_member, get_organization_owner,
    get_organization_admin_or_owner, get_organization_editor_or_higher,
    get_organization_member_or_higher, get_permission_checker
)
from app.services.user_service import UserService
from app.services.email_service import EmailService
from app.schemas.auth import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    OrganizationMemberResponse, OrganizationMemberUpdate, OrganizationInvite,
    OrganizationInviteResponse, OrganizationInviteAccept, UserRole
)
from app.schemas.user import (
    OrganizationSearchResponse, OrganizationSearchParams, OrganizationStatsResponse,
    OrganizationSettings, OrganizationSettingsUpdate, OrganizationBilling,
    OrganizationBillingUpdate, BulkOrganizationAction, MessageResponse
)
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember

router = APIRouter()


@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a new organization.
    
    Creates a new organization with the current user as owner.
    """
    try:
        user_service = UserService(db)
        organization = await user_service.create_organization(current_user, org_data)
        
        return OrganizationResponse.model_validate(organization, from_attributes=True)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create organization"
        )


@router.get("/", response_model=List[OrganizationResponse])
async def get_my_organizations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get current user's organizations.
    
    Returns all organizations the current user belongs to.
    """
    try:
        user_service = UserService(db)
        organizations = await user_service.get_user_organizations(current_user)
        
        return [OrganizationResponse.model_validate(org, from_attributes=True) for org in organizations]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get organizations"
        )


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization_by_id(
    organization: Organization = Depends(get_organization_member_or_higher)
) -> Any:
    """
    Get organization by ID.
    
    Returns organization details for members.
    """
    return OrganizationResponse.model_validate(organization, from_attributes=True)


@router.put("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: uuid.UUID,
    update_data: OrganizationUpdate,
    organization: Organization = Depends(get_organization_admin_or_owner),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update organization.
    
    Updates organization information (admin/owner only).
    """
    try:
        user_service = UserService(db)
        updated_organization = await user_service.update_organization(organization, update_data)
        
        return OrganizationResponse.model_validate(updated_organization, from_attributes=True)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update organization"
        )


@router.delete("/{organization_id}", response_model=MessageResponse)
async def delete_organization(
    organization: Organization = Depends(get_organization_owner),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete organization.
    
    Deletes organization (owner only).
    """
    try:
        # Soft delete by deactivating
        organization.is_active = False
        await db.commit()
        
        return MessageResponse(message="Organization deleted successfully")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete organization"
        )


@router.get("/{organization_id}/members", response_model=List[OrganizationMemberResponse])
async def get_organization_members(
    organization: Organization = Depends(get_organization_member_or_higher),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get organization members.
    
    Returns all members of the organization.
    """
    try:
        # Get organization with members using ORM
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(OrganizationMember)
            .options(selectinload(OrganizationMember.user))
            .where(OrganizationMember.organization_id == organization.id)
        )
        members = result.scalars().all()
        
        return [OrganizationMemberResponse.model_validate(member, from_attributes=True) for member in members]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get organization members"
        )


@router.post("/{organization_id}/invite", response_model=OrganizationInviteResponse)
async def invite_user_to_organization(
    organization_id: uuid.UUID,
    invite_data: OrganizationInvite,
    organization: Organization = Depends(get_organization_admin_or_owner),
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Invite user to organization.
    
    Sends invitation email to user (admin/owner only).
    """
    try:
        user_service = UserService(db)
        email_service = EmailService()
        
        # Invite user
        membership = await user_service.invite_user_to_organization(
            organization, current_user, invite_data.email, invite_data.role, invite_data.message
        )
        
        # Send invitation email
        invitation_url = f"{settings.FRONTEND_URL}/auth/invite?token={membership.invitation_token}"
        email_service.send_organization_invitation_email(
            invite_data.email,
            current_user.full_name,
            organization.name,
            invite_data.role,
            invitation_url,
            invite_data.message
        )
        
        return OrganizationInviteResponse.model_validate(membership, from_attributes=True)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to invite user"
        )


@router.post("/invite/accept", response_model=MessageResponse)
async def accept_organization_invitation(
    accept_data: OrganizationInviteAccept,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Accept organization invitation.
    
    Accepts invitation using invitation token.
    """
    try:
        user_service = UserService(db)
        membership = await user_service.accept_organization_invitation(
            accept_data.token, accept_data.password
        )
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired invitation token"
            )
        
        return MessageResponse(message="Invitation accepted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to accept invitation"
        )


@router.put("/{organization_id}/members/{user_id}", response_model=OrganizationMemberResponse)
async def update_member_role(
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    update_data: OrganizationMemberUpdate,
    organization: Organization = Depends(get_organization_admin_or_owner),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update member role.
    
    Updates member's role in organization (admin/owner only).
    """
    try:
        # Get membership
        result = await db.execute(
            "SELECT * FROM organization_members WHERE organization_id = :org_id AND user_id = :user_id",
            {"org_id": organization_id, "user_id": user_id}
        )
        membership = result.fetchone()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        
        # Update role
        if update_data.role:
            membership.role = update_data.role.value
        
        if update_data.is_active:
            membership.is_active = update_data.is_active
        
        await db.commit()
        
        return OrganizationMemberResponse.model_validate(membership, from_attributes=True)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update member role"
        )


@router.delete("/{organization_id}/members/{user_id}", response_model=MessageResponse)
async def remove_member_from_organization(
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    organization: Organization = Depends(get_organization_admin_or_owner),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Remove member from organization.
    
    Removes member from organization (admin/owner only).
    """
    try:
        # Get membership
        result = await db.execute(
            "SELECT * FROM organization_members WHERE organization_id = :org_id AND user_id = :user_id",
            {"org_id": organization_id, "user_id": user_id}
        )
        membership = result.fetchone()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        
        # Remove membership
        await db.execute(
            "DELETE FROM organization_members WHERE organization_id = :org_id AND user_id = :user_id",
            {"org_id": organization_id, "user_id": user_id}
        )
        await db.commit()
        
        return MessageResponse(message="Member removed successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove member"
        )


@router.get("/{organization_id}/stats", response_model=OrganizationStatsResponse)
async def get_organization_stats(
    organization: Organization = Depends(get_organization_member_or_higher),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get organization statistics.
    
    Returns organization statistics and usage information.
    """
    try:
        # Get member count
        result = await db.execute(
            "SELECT COUNT(*) FROM organization_members WHERE organization_id = :org_id AND is_active = 'active'",
            {"org_id": organization.id}
        )
        member_count = result.scalar()
        
        return OrganizationStatsResponse(
            total_members=member_count,
            total_articles=0,  # Placeholder for future implementation
            total_styles=0,    # Placeholder for future implementation
            storage_used=0,    # Placeholder for future implementation
            api_calls_this_month=0  # Placeholder for future implementation
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get organization statistics"
        )


@router.get("/{organization_id}/settings", response_model=OrganizationSettings)
async def get_organization_settings(
    organization: Organization = Depends(get_organization_admin_or_owner)
) -> Any:
    """
    Get organization settings.
    
    Returns organization settings and configuration.
    """
    # For now, return default settings
    # In the future, this would be stored in the organization.settings field
    return OrganizationSettings()


@router.put("/{organization_id}/settings", response_model=OrganizationSettings)
async def update_organization_settings(
    organization_id: uuid.UUID,
    settings_data: OrganizationSettingsUpdate,
    organization: Organization = Depends(get_organization_admin_or_owner),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update organization settings.
    
    Updates organization settings and configuration (admin/owner only).
    """
    try:
        # Update settings
        current_settings = organization.settings or {}
        updated_settings = {**current_settings, **settings_data.dict(exclude_unset=True)}
        organization.settings = updated_settings
        
        await db.commit()
        
        return OrganizationSettings(**updated_settings)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update organization settings"
        )


# Admin endpoints
@router.get("/admin/search", response_model=OrganizationSearchResponse)
async def search_organizations(
    search_params: OrganizationSearchParams = Depends(),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Search organizations (Admin only).
    
    Search and filter organizations with pagination.
    """
    try:
        user_service = UserService(db)
        result = await user_service.search_organizations(search_params)
        
        return OrganizationSearchResponse(
            organizations=result["organizations"],
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"],
            has_next=result["has_next"],
            has_prev=result["has_prev"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search organizations"
        )


@router.post("/admin/bulk-action", response_model=MessageResponse)
async def bulk_organization_action(
    action_data: BulkOrganizationAction,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Perform bulk action on organizations (Admin only).
    
    Performs bulk operations on multiple organizations.
    """
    try:
        user_service = UserService(db)
        
        # Get organizations
        organizations = []
        for org_id in action_data.organization_ids:
            organization = await user_service.get_organization(org_id)
            if organization:
                organizations.append(organization)
        
        if not organizations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No valid organizations found"
            )
        
        # Perform action
        success_count = 0
        for organization in organizations:
            if action_data.action == "activate":
                organization.is_active = True
                success_count += 1
            elif action_data.action == "deactivate":
                organization.is_active = False
                success_count += 1
            elif action_data.action == "delete":
                organization.is_active = False
                success_count += 1
        
        await db.commit()
        
        return MessageResponse(
            message=f"Bulk action '{action_data.action}' completed on {success_count} organizations"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk action"
        )
