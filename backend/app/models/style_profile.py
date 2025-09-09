"""
StyleProfile model for managing writing styles and analysis.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, JSON, ForeignKey,
    Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class StyleProfile(Base):
    """
    StyleProfile model for managing writing styles and their analysis.
    """
    __tablename__ = "style_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Organization relationship
    organization_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("organizations.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    
    # Creator relationship
    created_by_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="SET NULL"), 
        nullable=True, 
        index=True
    )
    
    # Style analysis data
    analysis = Column(JSON, default=dict, nullable=False)
    tags = Column(JSON, default=list, nullable=False)
    
    # Status and settings
    is_active = Column(Boolean, default=True, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_analyzed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="style_profiles")
    created_by = relationship("User", back_populates="created_style_profiles")
    reference_articles = relationship("ReferenceArticle", back_populates="style_profile", cascade="all, delete-orphan")
    generated_content = relationship("GeneratedContent", back_populates="style_profile", cascade="all, delete-orphan")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_style_profile_org", "organization_id"),
        Index("idx_style_profile_created_by", "created_by_id"),
        Index("idx_style_profile_created_at", "created_at"),
        Index("idx_style_profile_last_analyzed", "last_analyzed_at"),
        UniqueConstraint("organization_id", "name", name="uq_style_profile_org_name"),
    )

    def __repr__(self):
        return f"<StyleProfile(id={self.id}, name={self.name}, organization_id={self.organization_id})>"

    @property
    def reference_count(self) -> int:
        """Get the number of reference articles."""
        return len(self.reference_articles)

    @property
    def is_analyzed(self) -> bool:
        """Check if the style profile has been analyzed."""
        return self.last_analyzed_at is not None and bool(self.analysis)

    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get a summary of the analysis data."""
        if not self.analysis:
            return {}
        
        return {
            "has_analysis": bool(self.analysis),
            "last_analyzed": self.last_analyzed_at.isoformat() if self.last_analyzed_at else None,
            "reference_count": self.reference_count,
            "tags": self.tags or [],
            "analysis_keys": list(self.analysis.keys()) if isinstance(self.analysis, dict) else []
        }

    def add_tag(self, tag: str) -> None:
        """Add a tag to the style profile."""
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the style profile."""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)

    def update_analysis(self, analysis_data: Dict[str, Any]) -> None:
        """Update the analysis data and timestamp."""
        self.analysis = analysis_data
        self.last_analyzed_at = datetime.utcnow()
