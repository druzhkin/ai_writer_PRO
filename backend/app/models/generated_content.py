"""
GeneratedContent model for AI-generated content management.
"""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, 
    Index, ForeignKey, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class GeneratedContent(Base):
    """
    Model for storing AI-generated content with version control and metadata.
    """
    __tablename__ = "generated_content"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Organization and user relationships
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    style_profile_id = Column(UUID(as_uuid=True), ForeignKey("style_profiles.id", ondelete="SET NULL"), nullable=True)
    
    # Content metadata
    title = Column(String(500), nullable=False)
    brief = Column(Text, nullable=True)
    content_type = Column(String(50), nullable=False, default="article")  # article, blog_post, marketing_copy, etc.
    
    # Generated content
    generated_text = Column(Text, nullable=False)
    word_count = Column(Integer, nullable=False, default=0)
    character_count = Column(Integer, nullable=False, default=0)
    
    # Version control
    version = Column(Integer, nullable=False, default=1)
    is_current = Column(Boolean, nullable=False, default=True)
    
    # Token usage tracking
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    estimated_cost = Column(Float, nullable=False, default=0.0)
    
    # Generation metadata
    model_used = Column(String(100), nullable=False, default="gpt-4-turbo-preview")
    generation_time_seconds = Column(Float, nullable=True)
    generation_prompt = Column(Text, nullable=True)
    
    # Status and flags
    status = Column(String(50), nullable=False, default="completed")  # pending, completed, failed, cancelled
    is_archived = Column(Boolean, nullable=False, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="generated_content")
    created_by = relationship("User", back_populates="generated_content")
    style_profile = relationship("StyleProfile", back_populates="generated_content")
    iterations = relationship("ContentIteration", back_populates="generated_content", cascade="all, delete-orphan")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_generated_content_org", "organization_id"),
        Index("idx_generated_content_creator", "created_by_id"),
        Index("idx_generated_content_style", "style_profile_id"),
        Index("idx_generated_content_created_at", "created_at"),
        Index("idx_generated_content_status", "status"),
        Index("idx_generated_content_type", "content_type"),
        Index("idx_generated_content_current", "is_current"),
        CheckConstraint("word_count >= 0", name="ck_generated_content_word_count_positive"),
        CheckConstraint("character_count >= 0", name="ck_generated_content_char_count_positive"),
        CheckConstraint("input_tokens >= 0", name="ck_generated_content_input_tokens_positive"),
        CheckConstraint("output_tokens >= 0", name="ck_generated_content_output_tokens_positive"),
        CheckConstraint("total_tokens >= 0", name="ck_generated_content_total_tokens_positive"),
        CheckConstraint("estimated_cost >= 0", name="ck_generated_content_cost_positive"),
        CheckConstraint("version > 0", name="ck_generated_content_version_positive"),
    )

    def __repr__(self):
        return f"<GeneratedContent(id={self.id}, title='{self.title}', version={self.version})>"

    @property
    def is_latest_version(self) -> bool:
        """Check if this is the latest version of the content."""
        return self.is_current

    @property
    def reading_time_minutes(self) -> int:
        """Estimate reading time in minutes (assuming 200 words per minute)."""
        return max(1, self.word_count // 200)

    def get_iteration_count(self) -> int:
        """Get the number of iterations for this content."""
        return len(self.iterations)

    def get_total_cost(self) -> float:
        """Get total cost including all iterations."""
        total_cost = self.estimated_cost
        for iteration in self.iterations:
            total_cost += iteration.estimated_cost
        return total_cost

    def get_total_tokens(self) -> int:
        """Get total tokens including all iterations."""
        total_tokens = self.total_tokens
        for iteration in self.iterations:
            total_tokens += iteration.total_tokens
        return total_tokens
