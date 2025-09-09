"""
APIUsage model for tracking token usage and costs across all AI operations.
"""

import uuid
from datetime import datetime, date
from typing import Optional
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Date, 
    Index, ForeignKey, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class APIUsage(Base):
    """
    Model for tracking API usage, token consumption, and costs for billing and analytics.
    """
    __tablename__ = "api_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)  # Nullable for system operations
    
    # Usage metadata
    service_type = Column(String(50), nullable=False)  # content_generation, content_editing, style_analysis, etc.
    operation_type = Column(String(50), nullable=False)  # generate, edit, analyze, etc.
    
    # Token usage
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    
    # Cost calculation
    input_cost = Column(Float, nullable=False, default=0.0)
    output_cost = Column(Float, nullable=False, default=0.0)
    total_cost = Column(Float, nullable=False, default=0.0)
    
    # Model and pricing information
    model_used = Column(String(100), nullable=False)
    input_cost_per_1k = Column(Float, nullable=False, default=0.0)
    output_cost_per_1k = Column(Float, nullable=False, default=0.0)
    
    # Request metadata
    request_id = Column(String(255), nullable=True)  # For tracking specific requests
    response_time_ms = Column(Integer, nullable=True)  # Response time in milliseconds
    success = Column(String(10), nullable=False, default="true")  # true, false, partial
    
    # Date tracking for analytics
    usage_date = Column(Date, nullable=False, default=func.current_date())
    usage_hour = Column(Integer, nullable=True)  # Hour of day (0-23) for hourly analytics
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="api_usage")
    user = relationship("User", back_populates="api_usage")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_api_usage_org", "organization_id"),
        Index("idx_api_usage_user", "user_id"),
        Index("idx_api_usage_date", "usage_date"),
        Index("idx_api_usage_service", "service_type"),
        Index("idx_api_usage_operation", "operation_type"),
        Index("idx_api_usage_model", "model_used"),
        Index("idx_api_usage_created_at", "created_at"),
        Index("idx_api_usage_hour", "usage_hour"),
        Index("idx_api_usage_success", "success"),
        CheckConstraint("input_tokens >= 0", name="ck_api_usage_input_tokens_positive"),
        CheckConstraint("output_tokens >= 0", name="ck_api_usage_output_tokens_positive"),
        CheckConstraint("total_tokens >= 0", name="ck_api_usage_total_tokens_positive"),
        CheckConstraint("input_cost >= 0", name="ck_api_usage_input_cost_positive"),
        CheckConstraint("output_cost >= 0", name="ck_api_usage_output_cost_positive"),
        CheckConstraint("total_cost >= 0", name="ck_api_usage_total_cost_positive"),
        CheckConstraint("input_cost_per_1k >= 0", name="ck_api_usage_input_cost_per_1k_positive"),
        CheckConstraint("output_cost_per_1k >= 0", name="ck_api_usage_output_cost_per_1k_positive"),
        CheckConstraint("usage_hour >= 0 AND usage_hour <= 23", name="ck_api_usage_hour_valid"),
        CheckConstraint("response_time_ms >= 0", name="ck_api_usage_response_time_positive"),
    )

    def __repr__(self):
        return f"<APIUsage(id={self.id}, org={self.organization_id}, service={self.service_type}, tokens={self.total_tokens})>"

    @property
    def cost_per_token(self) -> float:
        """Calculate cost per token."""
        if self.total_tokens == 0:
            return 0.0
        return self.total_cost / self.total_tokens

    @property
    def tokens_per_dollar(self) -> float:
        """Calculate tokens per dollar spent."""
        if self.total_cost == 0:
            return float('inf')
        return self.total_tokens / self.total_cost

    @property
    def is_successful(self) -> bool:
        """Check if the operation was successful."""
        return self.success == "true"

    @property
    def is_partial_success(self) -> bool:
        """Check if the operation was partially successful."""
        return self.success == "partial"

    @property
    def is_failed(self) -> bool:
        """Check if the operation failed."""
        return self.success == "false"

    @classmethod
    def get_daily_usage_summary(cls, organization_id: uuid.UUID, usage_date: date) -> dict:
        """Get daily usage summary for an organization."""
        # This would be implemented as a class method or service method
        # Returns aggregated usage data for the day
        pass

    @classmethod
    def get_monthly_usage_summary(cls, organization_id: uuid.UUID, year: int, month: int) -> dict:
        """Get monthly usage summary for an organization."""
        # This would be implemented as a class method or service method
        # Returns aggregated usage data for the month
        pass
