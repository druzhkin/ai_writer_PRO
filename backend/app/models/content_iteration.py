"""
ContentIteration model for tracking content editing and version control.
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Text, Integer, Float, DateTime, 
    Index, ForeignKey, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ContentIteration(Base):
    """
    Model for tracking content iterations and edits with diff tracking.
    """
    __tablename__ = "content_iterations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    generated_content_id = Column(UUID(as_uuid=True), ForeignKey("generated_content.id", ondelete="CASCADE"), nullable=False)
    edited_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Iteration metadata
    iteration_number = Column(Integer, nullable=False)
    edit_prompt = Column(Text, nullable=False)  # The user's instruction for the edit
    edit_type = Column(String(50), nullable=False, default="general")  # general, style, tone, length, structure, etc.
    
    # Content changes
    previous_text = Column(Text, nullable=False)  # Text before the edit
    new_text = Column(Text, nullable=False)       # Text after the edit
    diff_summary = Column(Text, nullable=True)    # Human-readable summary of changes
    diff_lines = Column(Text, nullable=True)      # Detailed diff lines (JSON/Text)
    
    # Text metrics
    previous_word_count = Column(Integer, nullable=False, default=0)
    new_word_count = Column(Integer, nullable=False, default=0)
    word_count_change = Column(Integer, nullable=False, default=0)
    
    previous_character_count = Column(Integer, nullable=False, default=0)
    new_character_count = Column(Integer, nullable=False, default=0)
    character_count_change = Column(Integer, nullable=False, default=0)
    
    # Token usage for this iteration
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    estimated_cost = Column(Float, nullable=False, default=0.0)
    
    # Generation metadata
    model_used = Column(String(100), nullable=False, default="gpt-4-turbo-preview")
    generation_time_seconds = Column(Float, nullable=True)
    generation_prompt = Column(Text, nullable=True)
    
    # Status
    status = Column(String(50), nullable=False, default="completed")  # pending, completed, failed, cancelled
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    generated_content = relationship("GeneratedContent", back_populates="iterations")
    edited_by = relationship("User", back_populates="content_iterations")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_content_iteration_content", "generated_content_id"),
        Index("idx_content_iteration_editor", "edited_by_id"),
        Index("idx_content_iteration_number", "iteration_number"),
        Index("idx_content_iteration_created_at", "created_at"),
        Index("idx_content_iteration_type", "edit_type"),
        Index("idx_content_iteration_status", "status"),
        CheckConstraint("iteration_number > 0", name="ck_content_iteration_number_positive"),
        CheckConstraint("previous_word_count >= 0", name="ck_content_iteration_prev_word_count_positive"),
        CheckConstraint("new_word_count >= 0", name="ck_content_iteration_new_word_count_positive"),
        CheckConstraint("previous_character_count >= 0", name="ck_content_iteration_prev_char_count_positive"),
        CheckConstraint("new_character_count >= 0", name="ck_content_iteration_new_char_count_positive"),
        CheckConstraint("input_tokens >= 0", name="ck_content_iteration_input_tokens_positive"),
        CheckConstraint("output_tokens >= 0", name="ck_content_iteration_output_tokens_positive"),
        CheckConstraint("total_tokens >= 0", name="ck_content_iteration_total_tokens_positive"),
        CheckConstraint("estimated_cost >= 0", name="ck_content_iteration_cost_positive"),
    )

    def __repr__(self):
        return f"<ContentIteration(id={self.id}, content_id={self.generated_content_id}, iteration={self.iteration_number})>"

    @property
    def word_count_change_percentage(self) -> float:
        """Calculate percentage change in word count."""
        if self.previous_word_count == 0:
            return 100.0 if self.new_word_count > 0 else 0.0
        return ((self.new_word_count - self.previous_word_count) / self.previous_word_count) * 100

    @property
    def character_count_change_percentage(self) -> float:
        """Calculate percentage change in character count."""
        if self.previous_character_count == 0:
            return 100.0 if self.new_character_count > 0 else 0.0
        return ((self.new_character_count - self.previous_character_count) / self.previous_character_count) * 100

    @property
    def is_expansion(self) -> bool:
        """Check if this iteration expanded the content."""
        return self.word_count_change > 0

    @property
    def is_contraction(self) -> bool:
        """Check if this iteration contracted the content."""
        return self.word_count_change < 0

    @property
    def is_rewrite(self) -> bool:
        """Check if this iteration was a significant rewrite (large change)."""
        return abs(self.word_count_change_percentage) > 50

    def get_change_summary(self) -> str:
        """Get a human-readable summary of the changes."""
        if self.diff_summary:
            return self.diff_summary
        
        change_type = "expanded" if self.is_expansion else "contracted" if self.is_contraction else "modified"
        return f"Content {change_type} by {abs(self.word_count_change)} words ({abs(self.word_count_change_percentage):.1f}%)"
