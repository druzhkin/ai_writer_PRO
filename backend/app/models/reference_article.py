"""
ReferenceArticle model for storing reference articles used in style analysis.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, JSON, ForeignKey,
    Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ReferenceArticle(Base):
    """
    ReferenceArticle model for storing reference articles used in style analysis.
    """
    __tablename__ = "reference_articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=False)
    source_url = Column(Text, nullable=True)
    
    # File information
    original_filename = Column(String(255), nullable=True)
    file_size = Column(String(50), nullable=True)  # Store as string for flexibility
    mime_type = Column(String(100), nullable=True)
    s3_key = Column(String(500), nullable=True)  # S3 object key for file storage
    
    # Style profile relationship
    style_profile_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("style_profiles.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    
    # Uploader relationship
    uploaded_by_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="SET NULL"), 
        nullable=True, 
        index=True
    )
    
    # Organization relationship (for easier querying)
    organization_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("organizations.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    
    # Processing status
    processing_status = Column(String(50), default="pending", nullable=False)  # pending, processing, completed, failed
    processing_error = Column(Text, nullable=True)
    
    # Extracted metadata
    metadata = Column(JSON, default=dict, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    style_profile = relationship("StyleProfile", back_populates="reference_articles")
    uploaded_by = relationship("User", back_populates="uploaded_reference_articles")
    organization = relationship("Organization", back_populates="reference_articles")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_reference_article_style_profile", "style_profile_id"),
        Index("idx_reference_article_uploaded_by", "uploaded_by_id"),
        Index("idx_reference_article_organization", "organization_id"),
        Index("idx_reference_article_created_at", "created_at"),
        Index("idx_reference_article_processing_status", "processing_status"),
        Index("idx_reference_article_processed_at", "processed_at"),
    )

    def __repr__(self):
        return f"<ReferenceArticle(id={self.id}, title={self.title}, style_profile_id={self.style_profile_id})>"

    @property
    def is_processed(self) -> bool:
        """Check if the article has been processed successfully."""
        return self.processing_status == "completed"

    @property
    def is_processing(self) -> bool:
        """Check if the article is currently being processed."""
        return self.processing_status == "processing"

    @property
    def has_failed(self) -> bool:
        """Check if the article processing has failed."""
        return self.processing_status == "failed"

    @property
    def content_length(self) -> int:
        """Get the length of the content."""
        return len(self.content) if self.content else 0

    @property
    def word_count(self) -> int:
        """Get the approximate word count of the content."""
        if not self.content:
            return 0
        return len(self.content.split())

    def get_metadata_summary(self) -> Dict[str, Any]:
        """Get a summary of the metadata."""
        if not self.metadata:
            return {}
        
        return {
            "has_metadata": bool(self.metadata),
            "metadata_keys": list(self.metadata.keys()) if isinstance(self.metadata, dict) else [],
            "content_length": self.content_length,
            "word_count": self.word_count,
            "processing_status": self.processing_status,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None
        }

    def mark_processing(self) -> None:
        """Mark the article as being processed."""
        self.processing_status = "processing"
        self.processing_error = None

    def mark_completed(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Mark the article as completed processing."""
        self.processing_status = "completed"
        self.processing_error = None
        self.processed_at = datetime.utcnow()
        if metadata:
            self.metadata = metadata

    def mark_failed(self, error_message: str) -> None:
        """Mark the article as failed processing."""
        self.processing_status = "failed"
        self.processing_error = error_message
        self.processed_at = datetime.utcnow()
