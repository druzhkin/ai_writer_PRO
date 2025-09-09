"""
Authentication schemas for request/response validation.
"""

import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum


class UserRole(str, Enum):
    """User roles in organization."""
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class OAuthProvider(str, Enum):
    """OAuth providers."""
    GOOGLE = "google"
    GITHUB = "github"


# Base schemas
class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, regex="^[a-zA-Z0-9_-]+$")
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8, max_length=128)
    organization_name: Optional[str] = Field(None, max_length=255)
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user response."""
    id: uuid.UUID
    is_active: bool
    is_verified: bool
    is_superuser: bool
    oauth_provider: Optional[OAuthProvider]
    avatar_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for user profile updates."""
    username: Optional[str] = Field(None, min_length=3, max_length=50, regex="^[a-zA-Z0-9_-]+$")
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None


class PasswordChange(BaseModel):
    """Schema for password change."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class PasswordReset(BaseModel):
    """Schema for password reset request."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class EmailVerification(BaseModel):
    """Schema for email verification."""
    token: str


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    """Schema for token refresh."""
    refresh_token: str


class OAuthLogin(BaseModel):
    """Schema for OAuth login."""
    provider: OAuthProvider
    redirect_uri: Optional[str] = None


class OAuthCallback(BaseModel):
    """Schema for OAuth callback."""
    code: str
    state: str
    provider: OAuthProvider


class OrganizationBase(BaseModel):
    """Base organization schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    """Schema for organization creation."""
    pass


class OrganizationResponse(OrganizationBase):
    """Schema for organization response."""
    id: uuid.UUID
    slug: str
    owner_id: uuid.UUID
    subscription_plan: str
    subscription_status: str
    subscription_expires_at: Optional[datetime]
    settings: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime
    member_count: int
    
    class Config:
        from_attributes = True


class OrganizationUpdate(BaseModel):
    """Schema for organization updates."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    settings: Optional[dict] = None


class OrganizationMemberBase(BaseModel):
    """Base organization member schema."""
    role: UserRole = UserRole.VIEWER


class OrganizationMemberCreate(OrganizationMemberBase):
    """Schema for organization member creation."""
    user_id: uuid.UUID


class OrganizationMemberResponse(OrganizationMemberBase):
    """Schema for organization member response."""
    id: uuid.UUID
    user_id: uuid.UUID
    organization_id: uuid.UUID
    invited_by_id: Optional[uuid.UUID]
    is_active: str
    created_at: datetime
    updated_at: datetime
    invitation_accepted_at: Optional[datetime]
    user: UserResponse
    
    class Config:
        from_attributes = True


class OrganizationMemberUpdate(BaseModel):
    """Schema for organization member updates."""
    role: Optional[UserRole] = None
    is_active: Optional[str] = None


class OrganizationInvite(BaseModel):
    """Schema for organization invitation."""
    email: EmailStr
    role: UserRole = UserRole.VIEWER
    message: Optional[str] = Field(None, max_length=500)


class OrganizationInviteResponse(BaseModel):
    """Schema for organization invitation response."""
    id: uuid.UUID
    email: str
    role: UserRole
    organization_id: uuid.UUID
    invited_by_id: uuid.UUID
    invitation_token: str
    invitation_expires_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class OrganizationInviteAccept(BaseModel):
    """Schema for accepting organization invitation."""
    token: str
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password if provided."""
        if v is not None:
            if len(v) < 8:
                raise ValueError('Password must be at least 8 characters long')
            if not any(c.isupper() for c in v):
                raise ValueError('Password must contain at least one uppercase letter')
            if not any(c.islower() for c in v):
                raise ValueError('Password must contain at least one lowercase letter')
            if not any(c.isdigit() for c in v):
                raise ValueError('Password must contain at least one digit')
        return v


class MessageResponse(BaseModel):
    """Generic message response schema."""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: Optional[str] = None
    success: bool = False
