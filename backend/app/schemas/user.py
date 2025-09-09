"""
User management schemas for profile and organization management.
"""

import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from enum import Enum

from .auth import UserRole, UserResponse, OrganizationResponse


class UserProfileResponse(UserResponse):
    """Extended user profile response with organization information."""
    organizations: List[OrganizationResponse] = []
    
    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    """User statistics response."""
    total_organizations: int
    owned_organizations: int
    member_organizations: int
    total_articles: int = 0  # Placeholder for future implementation
    total_styles: int = 0    # Placeholder for future implementation


class UserPreferences(BaseModel):
    """User preferences schema."""
    theme: str = "light"  # light, dark, auto
    language: str = "en"
    timezone: str = "UTC"
    email_notifications: bool = True
    marketing_emails: bool = False
    two_factor_enabled: bool = False


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences."""
    theme: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    email_notifications: Optional[bool] = None
    marketing_emails: Optional[bool] = None
    two_factor_enabled: Optional[bool] = None


class UserActivityLog(BaseModel):
    """User activity log entry."""
    id: uuid.UUID
    user_id: uuid.UUID
    action: str
    resource_type: str
    resource_id: Optional[uuid.UUID]
    details: Optional[dict]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserSession(BaseModel):
    """User session information."""
    id: uuid.UUID
    user_id: uuid.UUID
    device_info: Optional[str]
    ip_address: Optional[str]
    is_active: bool
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    
    class Config:
        from_attributes = True


class UserSessionResponse(BaseModel):
    """User session response with current session highlighted."""
    sessions: List[UserSession]
    current_session_id: Optional[uuid.UUID]


class OrganizationStatsResponse(BaseModel):
    """Organization statistics response."""
    total_members: int
    total_articles: int = 0  # Placeholder for future implementation
    total_styles: int = 0    # Placeholder for future implementation
    storage_used: int = 0    # Placeholder for future implementation
    api_calls_this_month: int = 0  # Placeholder for future implementation


class OrganizationSettings(BaseModel):
    """Organization settings schema."""
    allow_member_invites: bool = True
    require_email_verification: bool = True
    default_member_role: UserRole = UserRole.VIEWER
    max_members: int = 10
    branding: dict = {}
    integrations: dict = {}


class OrganizationSettingsUpdate(BaseModel):
    """Schema for updating organization settings."""
    allow_member_invites: Optional[bool] = None
    require_email_verification: Optional[bool] = None
    default_member_role: Optional[UserRole] = None
    max_members: Optional[int] = None
    branding: Optional[dict] = None
    integrations: Optional[dict] = None


class OrganizationBilling(BaseModel):
    """Organization billing information."""
    subscription_plan: str
    subscription_status: str
    subscription_expires_at: Optional[datetime]
    billing_email: Optional[EmailStr]
    payment_method: Optional[str]
    next_billing_date: Optional[datetime]
    usage_this_month: dict = {}


class OrganizationBillingUpdate(BaseModel):
    """Schema for updating organization billing."""
    billing_email: Optional[EmailStr] = None
    payment_method: Optional[str] = None


class UserSearchResponse(BaseModel):
    """User search response."""
    users: List[UserResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class UserSearchParams(BaseModel):
    """User search parameters."""
    query: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    organization_id: Optional[uuid.UUID] = None
    page: int = Field(1, ge=1)
    per_page: int = Field(10, ge=1, le=100)


class OrganizationSearchResponse(BaseModel):
    """Organization search response."""
    organizations: List[OrganizationResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class OrganizationSearchParams(BaseModel):
    """Organization search parameters."""
    query: Optional[str] = None
    subscription_plan: Optional[str] = None
    is_active: Optional[bool] = None
    owner_id: Optional[uuid.UUID] = None
    page: int = Field(1, ge=1)
    per_page: int = Field(10, ge=1, le=100)


class BulkUserAction(BaseModel):
    """Schema for bulk user actions."""
    user_ids: List[uuid.UUID] = Field(..., min_items=1)
    action: str  # activate, deactivate, delete, etc.
    reason: Optional[str] = None


class BulkOrganizationAction(BaseModel):
    """Schema for bulk organization actions."""
    organization_ids: List[uuid.UUID] = Field(..., min_items=1)
    action: str  # activate, deactivate, delete, etc.
    reason: Optional[str] = None


class UserExportResponse(BaseModel):
    """User data export response."""
    export_id: uuid.UUID
    status: str  # pending, processing, completed, failed
    download_url: Optional[str] = None
    expires_at: datetime
    created_at: datetime


class DataExportRequest(BaseModel):
    """Data export request schema."""
    include_organizations: bool = True
    include_activity_logs: bool = False
    include_preferences: bool = True
    format: str = "json"  # json, csv


class DataImportRequest(BaseModel):
    """Data import request schema."""
    file_url: str
    format: str = "json"  # json, csv
    overwrite_existing: bool = False


class DataImportResponse(BaseModel):
    """Data import response schema."""
    import_id: uuid.UUID
    status: str  # pending, processing, completed, failed
    imported_count: int = 0
    failed_count: int = 0
    errors: List[str] = []
    created_at: datetime
