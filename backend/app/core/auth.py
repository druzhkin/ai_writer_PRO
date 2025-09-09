"""
Authentication dependencies for JWT token validation and role-based access control.
"""

import uuid
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.services.auth_service import AuthService
from app.schemas.auth import UserRole

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        auth_service = AuthService(db)
        payload = auth_service.verify_token(credentials.credentials, "access")
        
        if payload is None:
            raise credentials_exception
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        user = await auth_service.get_user_by_id(uuid.UUID(user_id))
        if user is None or not user.is_active:
            raise credentials_exception
        
        return user
        
    except Exception:
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current verified user."""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


async def get_organization(
    organization_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Organization:
    """Get organization by ID."""
    result = await db.execute(
        select(Organization).where(Organization.id == organization_id)
    )
    organization = result.scalar_one_or_none()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return organization


async def get_organization_member(
    organization_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> OrganizationMember:
    """Get user's membership in organization."""
    result = await db.execute(
        select(OrganizationMember).where(
            and_(
                OrganizationMember.user_id == current_user.id,
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.is_active == "active"
            )
        )
    )
    membership = result.scalar_one_or_none()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )
    
    return membership


async def get_organization_owner(
    organization: Organization = Depends(get_organization),
    current_user: User = Depends(get_current_active_user)
) -> Organization:
    """Check if user is owner of organization."""
    if organization.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not the owner of this organization"
        )
    return organization


async def get_organization_admin_or_owner(
    organization: Organization = Depends(get_organization),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Organization:
    """Check if user is admin or owner of organization."""
    # Check if user is owner
    if organization.owner_id == current_user.id:
        return organization
    
    # Check if user is admin
    result = await db.execute(
        select(OrganizationMember).where(
            and_(
                OrganizationMember.user_id == current_user.id,
                OrganizationMember.organization_id == organization.id,
                OrganizationMember.role.in_([UserRole.OWNER.value, UserRole.ADMIN.value]),
                OrganizationMember.is_active == "active"
            )
        )
    )
    membership = result.scalar_one_or_none()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not an admin or owner of this organization"
        )
    
    return organization


async def get_organization_editor_or_higher(
    organization: Organization = Depends(get_organization),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Organization:
    """Check if user can edit content in organization."""
    # Check if user is owner
    if organization.owner_id == current_user.id:
        return organization
    
    # Check if user has editor role or higher
    result = await db.execute(
        select(OrganizationMember).where(
            and_(
                OrganizationMember.user_id == current_user.id,
                OrganizationMember.organization_id == organization.id,
                OrganizationMember.role.in_([UserRole.OWNER.value, UserRole.ADMIN.value, UserRole.EDITOR.value]),
                OrganizationMember.is_active == "active"
            )
        )
    )
    membership = result.scalar_one_or_none()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit content in this organization"
        )
    
    return organization


async def get_organization_member_or_higher(
    organization: Organization = Depends(get_organization),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Organization:
    """Check if user is a member of organization."""
    # Check if user is owner
    if organization.owner_id == current_user.id:
        return organization
    
    # Check if user is a member
    result = await db.execute(
        select(OrganizationMember).where(
            and_(
                OrganizationMember.user_id == current_user.id,
                OrganizationMember.organization_id == organization.id,
                OrganizationMember.is_active == "active"
            )
        )
    )
    membership = result.scalar_one_or_none()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )
    
    return organization


def require_role(required_roles: List[UserRole]):
    """Decorator to require specific roles."""
    async def role_checker(
        organization: Organization = Depends(get_organization),
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
    ) -> Organization:
        # Check if user is owner
        if organization.owner_id == current_user.id:
            return organization
        
        # Check if user has required role
        result = await db.execute(
            select(OrganizationMember).where(
                and_(
                    OrganizationMember.user_id == current_user.id,
                    OrganizationMember.organization_id == organization.id,
                    OrganizationMember.role.in_([r.value for r in required_roles]),
                    OrganizationMember.is_active == "active"
                )
            )
        )
        membership = result.scalar_one_or_none()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of the following roles: {', '.join([r.value for r in required_roles])}"
            )
        
        return organization
    
    return role_checker


# Common role requirements
require_owner = require_role([UserRole.OWNER])
require_admin_or_owner = require_role([UserRole.OWNER, UserRole.ADMIN])
require_editor_or_higher = require_role([UserRole.OWNER, UserRole.ADMIN, UserRole.EDITOR])
require_member = require_role([UserRole.OWNER, UserRole.ADMIN, UserRole.EDITOR, UserRole.VIEWER])


class PermissionChecker:
    """Permission checker for fine-grained access control."""
    
    def __init__(self, user: User, organization: Organization, membership: Optional[OrganizationMember] = None):
        self.user = user
        self.organization = organization
        self.membership = membership
        self.is_owner = organization.owner_id == user.id
    
    def can_manage_organization(self) -> bool:
        """Check if user can manage organization settings."""
        return self.is_owner or (self.membership and self.membership.role in [UserRole.OWNER.value, UserRole.ADMIN.value])
    
    def can_manage_members(self) -> bool:
        """Check if user can manage organization members."""
        return self.is_owner or (self.membership and self.membership.role in [UserRole.OWNER.value, UserRole.ADMIN.value])
    
    def can_edit_content(self) -> bool:
        """Check if user can edit content."""
        return self.is_owner or (self.membership and self.membership.role in [UserRole.OWNER.value, UserRole.ADMIN.value, UserRole.EDITOR.value])
    
    def can_view_content(self) -> bool:
        """Check if user can view content."""
        return self.is_owner or (self.membership and self.membership.role in [UserRole.OWNER.value, UserRole.ADMIN.value, UserRole.EDITOR.value, UserRole.VIEWER.value])
    
    def can_invite_members(self) -> bool:
        """Check if user can invite new members."""
        return self.is_owner or (self.membership and self.membership.role in [UserRole.OWNER.value, UserRole.ADMIN.value])
    
    def can_remove_members(self, target_membership: OrganizationMember) -> bool:
        """Check if user can remove a specific member."""
        if self.is_owner:
            return True
        
        if not self.membership:
            return False
        
        # Admins can remove editors and viewers, but not other admins or owners
        if self.membership.role == UserRole.ADMIN.value:
            return target_membership.role in [UserRole.EDITOR.value, UserRole.VIEWER.value]
        
        return False
    
    def can_change_role(self, target_membership: OrganizationMember, new_role: UserRole) -> bool:
        """Check if user can change another member's role."""
        if self.is_owner:
            return True
        
        if not self.membership:
            return False
        
        # Admins can change roles of editors and viewers
        if self.membership.role == UserRole.ADMIN.value:
            return target_membership.role in [UserRole.EDITOR.value, UserRole.VIEWER.value] and new_role in [UserRole.EDITOR, UserRole.VIEWER]
        
        return False


async def get_permission_checker(
    organization: Organization = Depends(get_organization),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> PermissionChecker:
    """Get permission checker for current user and organization."""
    membership = None
    
    if organization.owner_id != current_user.id:
        result = await db.execute(
            select(OrganizationMember).where(
                and_(
                    OrganizationMember.user_id == current_user.id,
                    OrganizationMember.organization_id == organization.id,
                    OrganizationMember.is_active == "active"
                )
            )
        )
        membership = result.scalar_one_or_none()
    
    return PermissionChecker(current_user, organization, membership)
