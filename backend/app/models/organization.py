"""
Organization model for multi-tenant support.
"""

import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Organization(Base):
    """
    Organization model for multi-tenant support.
    """
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Owner relationship
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Subscription and billing
    subscription_plan = Column(String(50), default="free", nullable=False)
    subscription_status = Column(String(50), default="active", nullable=False)
    subscription_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Organization settings
    settings = Column(JSON, default=dict, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="owned_organizations", foreign_keys=[owner_id])
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    style_profiles = relationship("StyleProfile", back_populates="organization", cascade="all, delete-orphan")
    reference_articles = relationship("ReferenceArticle", back_populates="organization", cascade="all, delete-orphan")
    generated_content = relationship("GeneratedContent", back_populates="organization", cascade="all, delete-orphan")
    api_usage = relationship("APIUsage", back_populates="organization", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name={self.name}, slug={self.slug})>"

    @property
    def member_count(self) -> int:
        """Get the number of members in the organization."""
        return len(self.members)

    def get_members_by_role(self, role: str) -> List["OrganizationMember"]:
        """Get all members with a specific role."""
        return [member for member in self.members if member.role == role]

    def get_owners(self) -> List["OrganizationMember"]:
        """Get all owners of the organization."""
        return self.get_members_by_role("owner")

    def get_admins(self) -> List["OrganizationMember"]:
        """Get all admins of the organization."""
        return self.get_members_by_role("admin")

    def get_editors(self) -> List["OrganizationMember"]:
        """Get all editors of the organization."""
        return self.get_members_by_role("editor")

    def get_viewers(self) -> List["OrganizationMember"]:
        """Get all viewers of the organization."""
        return self.get_members_by_role("viewer")

    def is_owner(self, user_id: uuid.UUID) -> bool:
        """Check if a user is an owner of the organization."""
        return any(member.user_id == user_id and member.role == "owner" for member in self.members)

    def is_admin_or_owner(self, user_id: uuid.UUID) -> bool:
        """Check if a user is an admin or owner of the organization."""
        return any(
            member.user_id == user_id and member.role in ["owner", "admin"] 
            for member in self.members
        )

    def can_edit(self, user_id: uuid.UUID) -> bool:
        """Check if a user can edit content in the organization."""
        return any(
            member.user_id == user_id and member.role in ["owner", "admin", "editor"] 
            for member in self.members
        )

    def can_view(self, user_id: uuid.UUID) -> bool:
        """Check if a user can view content in the organization."""
        return any(member.user_id == user_id for member in self.members)
