"""
User model for authentication and user management.
"""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, 
    Index, UniqueConstraint, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """
    User model with authentication and profile information.
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth users
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # OAuth fields
    oauth_provider = Column(String(50), nullable=True)  # 'google', 'github', etc.
    oauth_id = Column(String(255), nullable=True)
    avatar_url = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Email verification
    email_verification_token = Column(String(255), nullable=True)
    email_verification_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Password reset
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    owned_organizations = relationship("Organization", back_populates="owner", cascade="all, delete-orphan")
    organization_memberships = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")
    created_style_profiles = relationship("StyleProfile", back_populates="created_by", cascade="all, delete-orphan")
    uploaded_reference_articles = relationship("ReferenceArticle", back_populates="uploaded_by", cascade="all, delete-orphan")
    generated_content = relationship("GeneratedContent", back_populates="created_by", cascade="all, delete-orphan")
    content_iterations = relationship("ContentIteration", back_populates="edited_by", cascade="all, delete-orphan")
    api_usage = relationship("APIUsage", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_username", "username"),
        Index("idx_user_oauth", "oauth_provider", "oauth_id"),
        Index("idx_user_created_at", "created_at"),
        UniqueConstraint("email", name="uq_user_email"),
        UniqueConstraint("username", name="uq_user_username"),
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username

    @property
    def is_oauth_user(self) -> bool:
        """Check if user is OAuth-only (no password)."""
        return self.oauth_provider is not None and self.password_hash is None

    def get_organizations(self) -> List["Organization"]:
        """Get all organizations the user belongs to."""
        return [membership.organization for membership in self.organization_memberships]

    def get_organization_role(self, organization_id: uuid.UUID) -> Optional[str]:
        """Get user's role in a specific organization."""
        for membership in self.organization_memberships:
            if membership.organization_id == organization_id:
                return membership.role
        return None
