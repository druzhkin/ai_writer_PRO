"""
User management service for CRUD operations and organization management.
"""

import uuid
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload
import structlog

from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.schemas.auth import UserUpdate, OrganizationCreate, OrganizationUpdate, UserRole
from app.schemas.user import UserSearchParams, OrganizationSearchParams

logger = structlog.get_logger()


class UserService:
    """User management service for CRUD operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_profile(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user profile with organization memberships."""
        try:
            result = await self.db.execute(
                select(User)
                .options(selectinload(User.organization_memberships).selectinload(OrganizationMember.organization))
                .where(User.id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Error getting user profile", error=str(e), user_id=str(user_id))
            return None
    
    async def update_user_profile(self, user: User, update_data: UserUpdate) -> User:
        """Update user profile."""
        try:
            # Check if username is taken by another user
            if update_data.username and update_data.username != user.username:
                result = await self.db.execute(
                    select(User).where(
                        and_(User.username == update_data.username, User.id != user.id)
                    )
                )
                if result.scalar_one_or_none():
                    raise ValueError("Username already taken")
            
            # Update fields
            for field, value in update_data.dict(exclude_unset=True).items():
                setattr(user, field, value)
            
            user.updated_at = datetime.utcnow()
            await self.db.commit()
            
            logger.info("User profile updated", user_id=str(user.id))
            return user
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Error updating user profile", error=str(e), user_id=str(user.id))
            raise
    
    async def deactivate_user(self, user: User) -> bool:
        """Deactivate a user account."""
        try:
            user.is_active = False
            user.updated_at = datetime.utcnow()
            await self.db.commit()
            
            logger.info("User deactivated", user_id=str(user.id))
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Error deactivating user", error=str(e), user_id=str(user.id))
            return False
    
    async def delete_user(self, user: User) -> bool:
        """Delete a user account (soft delete by deactivating)."""
        return await self.deactivate_user(user)
    
    async def search_users(self, search_params: UserSearchParams) -> Dict[str, Any]:
        """Search users with pagination and filters."""
        try:
            query = select(User)
            
            # Apply filters
            if search_params.query:
                search_term = f"%{search_params.query}%"
                query = query.where(
                    or_(
                        User.email.ilike(search_term),
                        User.username.ilike(search_term),
                        User.first_name.ilike(search_term),
                        User.last_name.ilike(search_term)
                    )
                )
            
            if search_params.is_active is not None:
                query = query.where(User.is_active == search_params.is_active)
            
            if search_params.is_verified is not None:
                query = query.where(User.is_verified == search_params.is_verified)
            
            if search_params.organization_id:
                query = query.join(OrganizationMember).where(
                    OrganizationMember.organization_id == search_params.organization_id
                )
            
            if search_params.role:
                query = query.join(OrganizationMember).where(
                    OrganizationMember.role == search_params.role
                )
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar()
            
            # Apply pagination
            offset = (search_params.page - 1) * search_params.per_page
            query = query.offset(offset).limit(search_params.per_page)
            query = query.order_by(desc(User.created_at))
            
            result = await self.db.execute(query)
            users = result.scalars().all()
            
            return {
                "users": users,
                "total": total,
                "page": search_params.page,
                "per_page": search_params.per_page,
                "has_next": offset + search_params.per_page < total,
                "has_prev": search_params.page > 1
            }
            
        except Exception as e:
            logger.error("Error searching users", error=str(e))
            return {
                "users": [],
                "total": 0,
                "page": search_params.page,
                "per_page": search_params.per_page,
                "has_next": False,
                "has_prev": False
            }
    
    async def create_organization(self, owner: User, org_data: OrganizationCreate) -> Organization:
        """Create a new organization."""
        try:
            # Generate unique slug
            slug = self._generate_org_slug(org_data.name)
            
            organization = Organization(
                name=org_data.name,
                slug=slug,
                description=org_data.description,
                owner_id=owner.id,
                subscription_plan="free",
                subscription_status="active"
            )
            
            self.db.add(organization)
            await self.db.flush()  # Get the organization ID
            
            # Add owner as member
            membership = OrganizationMember(
                user_id=owner.id,
                organization_id=organization.id,
                role=UserRole.OWNER.value,
                is_active="active"
            )
            
            self.db.add(membership)
            await self.db.commit()
            
            logger.info("Organization created", org_id=str(organization.id), owner_id=str(owner.id))
            return organization
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Error creating organization", error=str(e))
            raise
    
    async def update_organization(self, organization: Organization, update_data: OrganizationUpdate) -> Organization:
        """Update organization."""
        try:
            # Check if name is taken by another organization
            if update_data.name and update_data.name != organization.name:
                result = await self.db.execute(
                    select(Organization).where(
                        and_(Organization.name == update_data.name, Organization.id != organization.id)
                    )
                )
                if result.scalar_one_or_none():
                    raise ValueError("Organization name already taken")
            
            # Update fields
            for field, value in update_data.dict(exclude_unset=True).items():
                setattr(organization, field, value)
            
            organization.updated_at = datetime.utcnow()
            await self.db.commit()
            
            logger.info("Organization updated", org_id=str(organization.id))
            return organization
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Error updating organization", error=str(e), org_id=str(organization.id))
            raise
    
    async def get_organization(self, org_id: uuid.UUID) -> Optional[Organization]:
        """Get organization by ID."""
        try:
            result = await self.db.execute(
                select(Organization)
                .options(selectinload(Organization.members).selectinload(OrganizationMember.user))
                .where(Organization.id == org_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Error getting organization", error=str(e), org_id=str(org_id))
            return None
    
    async def get_user_organizations(self, user: User) -> List[Organization]:
        """Get all organizations a user belongs to."""
        try:
            result = await self.db.execute(
                select(Organization)
                .join(OrganizationMember)
                .where(OrganizationMember.user_id == user.id)
                .order_by(desc(Organization.created_at))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error("Error getting user organizations", error=str(e), user_id=str(user.id))
            return []
    
    async def search_organizations(self, search_params: OrganizationSearchParams) -> Dict[str, Any]:
        """Search organizations with pagination and filters."""
        try:
            query = select(Organization)
            
            # Apply filters
            if search_params.query:
                search_term = f"%{search_params.query}%"
                query = query.where(
                    or_(
                        Organization.name.ilike(search_term),
                        Organization.description.ilike(search_term)
                    )
                )
            
            if search_params.subscription_plan:
                query = query.where(Organization.subscription_plan == search_params.subscription_plan)
            
            if search_params.is_active is not None:
                query = query.where(Organization.is_active == search_params.is_active)
            
            if search_params.owner_id:
                query = query.where(Organization.owner_id == search_params.owner_id)
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar()
            
            # Apply pagination
            offset = (search_params.page - 1) * search_params.per_page
            query = query.offset(offset).limit(search_params.per_page)
            query = query.order_by(desc(Organization.created_at))
            
            result = await self.db.execute(query)
            organizations = result.scalars().all()
            
            return {
                "organizations": organizations,
                "total": total,
                "page": search_params.page,
                "per_page": search_params.per_page,
                "has_next": offset + search_params.per_page < total,
                "has_prev": search_params.page > 1
            }
            
        except Exception as e:
            logger.error("Error searching organizations", error=str(e))
            return {
                "organizations": [],
                "total": 0,
                "page": search_params.page,
                "per_page": search_params.per_page,
                "has_next": False,
                "has_prev": False
            }
    
    async def invite_user_to_organization(
        self, 
        organization: Organization, 
        inviter: User, 
        email: str, 
        role: UserRole = UserRole.VIEWER,
        message: Optional[str] = None
    ) -> OrganizationMember:
        """Invite a user to an organization."""
        try:
            # Check if user already exists
            user = await self.db.execute(select(User).where(User.email == email))
            user = user.scalar_one_or_none()
            
            if not user:
                # Create pending user
                username = email.split('@')[0]
                user = User(
                    email=email,
                    username=username,
                    is_active=True,
                    is_verified=False
                )
                self.db.add(user)
                await self.db.flush()
            
            # Check if user is already a member
            existing_membership = await self.db.execute(
                select(OrganizationMember).where(
                    and_(
                        OrganizationMember.user_id == user.id,
                        OrganizationMember.organization_id == organization.id
                    )
                )
            )
            if existing_membership.scalar_one_or_none():
                raise ValueError("User is already a member of this organization")
            
            # Create invitation
            invitation_token = secrets.token_urlsafe(32)
            membership = OrganizationMember(
                user_id=user.id,
                organization_id=organization.id,
                role=role.value,
                invited_by_id=inviter.id,
                invitation_token=invitation_token,
                invitation_expires_at=datetime.utcnow() + timedelta(days=7),
                is_active="pending"
            )
            
            self.db.add(membership)
            await self.db.commit()
            
            logger.info("User invited to organization", 
                       user_id=str(user.id), org_id=str(organization.id), role=role)
            
            return membership
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Error inviting user to organization", error=str(e))
            raise
    
    async def accept_organization_invitation(self, token: str, password: Optional[str] = None) -> Optional[OrganizationMember]:
        """Accept organization invitation."""
        try:
            result = await self.db.execute(
                select(OrganizationMember).where(
                    and_(
                        OrganizationMember.invitation_token == token,
                        OrganizationMember.invitation_expires_at > datetime.utcnow(),
                        OrganizationMember.is_active == "pending"
                    )
                )
            )
            membership = result.scalar_one_or_none()
            
            if not membership:
                return None
            
            # Update user if password provided
            if password:
                from app.services.auth_service import AuthService
                auth_service = AuthService(self.db)
                membership.user.password_hash = auth_service.get_password_hash(password)
                membership.user.is_verified = True
            
            # Accept invitation
            membership.is_active = "active"
            membership.invitation_accepted_at = datetime.utcnow()
            membership.invitation_token = None
            membership.invitation_expires_at = None
            
            await self.db.commit()
            
            logger.info("Organization invitation accepted", 
                       user_id=str(membership.user_id), org_id=str(membership.organization_id))
            
            return membership
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Error accepting organization invitation", error=str(e))
            return None
    
    async def update_member_role(self, membership: OrganizationMember, new_role: UserRole) -> OrganizationMember:
        """Update member role in organization."""
        try:
            membership.role = new_role.value
            membership.updated_at = datetime.utcnow()
            await self.db.commit()
            
            logger.info("Member role updated", 
                       user_id=str(membership.user_id), org_id=str(membership.organization_id), role=new_role)
            
            return membership
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Error updating member role", error=str(e))
            raise
    
    async def remove_member_from_organization(self, membership: OrganizationMember) -> bool:
        """Remove member from organization."""
        try:
            await self.db.delete(membership)
            await self.db.commit()
            
            logger.info("Member removed from organization", 
                       user_id=str(membership.user_id), org_id=str(membership.organization_id))
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Error removing member from organization", error=str(e))
            return False
    
    def _generate_org_slug(self, name: str) -> str:
        """Generate a unique organization slug."""
        import re
        slug = re.sub(r'[^a-zA-Z0-9-]', '-', name.lower())
        slug = re.sub(r'-+', '-', slug).strip('-')
        return f"{slug}-{secrets.token_hex(4)}"
