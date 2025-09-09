"""
OrganizationMember model for many-to-many relationship between users and organizations.
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class OrganizationMember(Base):
    """
    OrganizationMember model for role-based access control.
    """
    __tablename__ = "organization_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    # Role-based access control
    role = Column(String(20), nullable=False, default="viewer")  # owner, admin, editor, viewer
    
    # Invitation fields
    invited_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    invitation_token = Column(String(255), nullable=True)
    invitation_expires_at = Column(DateTime(timezone=True), nullable=True)
    invitation_accepted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active = Column(String(20), default="active", nullable=False)  # active, pending, suspended
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="organization_memberships", foreign_keys=[user_id])
    organization = relationship("Organization", back_populates="members")
    invited_by = relationship("User", foreign_keys=[invited_by_id])
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_org_member_user", "user_id"),
        Index("idx_org_member_org", "organization_id"),
        Index("idx_org_member_role", "role"),
        Index("idx_org_member_status", "is_active"),
        UniqueConstraint("user_id", "organization_id", name="uq_user_organization"),
    )

    def __repr__(self):
        return f"<OrganizationMember(user_id={self.user_id}, organization_id={self.organization_id}, role={self.role})>"

    @property
    def is_owner(self) -> bool:
        """Check if member is an owner."""
        return self.role == "owner"

    @property
    def is_admin(self) -> bool:
        """Check if member is an admin."""
        return self.role == "admin"

    @property
    def is_editor(self) -> bool:
        """Check if member is an editor."""
        return self.role == "editor"

    @property
    def is_viewer(self) -> bool:
        """Check if member is a viewer."""
        return self.role == "viewer"

    @property
    def is_pending(self) -> bool:
        """Check if invitation is pending."""
        return self.is_active == "pending"

    @property
    def is_suspended(self) -> bool:
        """Check if member is suspended."""
        return self.is_active == "suspended"

    def can_manage_organization(self) -> bool:
        """Check if member can manage organization settings."""
        return self.role in ["owner", "admin"]

    def can_manage_members(self) -> bool:
        """Check if member can manage other members."""
        return self.role in ["owner", "admin"]

    def can_edit_content(self) -> bool:
        """Check if member can edit content."""
        return self.role in ["owner", "admin", "editor"]

    def can_view_content(self) -> bool:
        """Check if member can view content."""
        return self.role in ["owner", "admin", "editor", "viewer"]

    def get_role_hierarchy_level(self) -> int:
        """Get role hierarchy level (higher number = more permissions)."""
        role_levels = {
            "viewer": 1,
            "editor": 2,
            "admin": 3,
            "owner": 4
        }
        return role_levels.get(self.role, 0)

    def can_manage_role(self, target_role: str) -> bool:
        """Check if this member can manage someone with the target role."""
        if self.role == "owner":
            return True  # Owners can manage everyone
        elif self.role == "admin":
            return target_role in ["editor", "viewer"]  # Admins can manage editors and viewers
        else:
            return False  # Editors and viewers cannot manage others
