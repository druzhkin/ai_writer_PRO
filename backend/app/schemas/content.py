"""
Content generation schemas for AI-generated content management.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class ContentType(str, Enum):
    """Content type enumeration."""
    ARTICLE = "article"
    BLOG_POST = "blog_post"
    MARKETING_COPY = "marketing_copy"
    PRODUCT_DESCRIPTION = "product_description"
    EMAIL = "email"
    SOCIAL_MEDIA = "social_media"
    PRESS_RELEASE = "press_release"
    WHITE_PAPER = "white_paper"
    CASE_STUDY = "case_study"
    NEWS_LETTER = "news_letter"


class ContentStatus(str, Enum):
    """Content status enumeration."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EditType(str, Enum):
    """Edit type enumeration."""
    GENERAL = "general"
    STYLE = "style"
    TONE = "tone"
    LENGTH = "length"
    STRUCTURE = "structure"
    GRAMMAR = "grammar"
    CLARITY = "clarity"


class ContentGenerationRequest(BaseModel):
    """Request schema for content generation."""
    title: str = Field(..., min_length=1, max_length=500, description="Content title")
    brief: Optional[str] = Field(None, max_length=5000, description="Content brief or outline")
    content_type: ContentType = Field(ContentType.ARTICLE, description="Type of content to generate")
    style_profile_id: Optional[uuid.UUID] = Field(None, description="Style profile to apply")
    target_length: Optional[int] = Field(None, ge=100, le=5000, description="Target word count")
    additional_instructions: Optional[str] = Field(None, max_length=2000, description="Additional generation instructions")
    model: Optional[str] = Field("gpt-4-turbo-preview", description="OpenAI model to use")
    
    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()


class ContentGenerationResponse(BaseModel):
    """Response schema for content generation."""
    id: uuid.UUID
    title: str
    brief: Optional[str]
    content_type: ContentType
    generated_text: str
    word_count: int
    character_count: int
    version: int
    status: ContentStatus
    
    # Token usage
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: float
    
    # Generation metadata
    model_used: str
    generation_time_seconds: Optional[float]
    
    # Relationships
    organization_id: uuid.UUID
    created_by_id: uuid.UUID
    style_profile_id: Optional[uuid.UUID]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ContentUpdateRequest(BaseModel):
    """Request schema for updating content."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    brief: Optional[str] = Field(None, max_length=5000)
    is_archived: Optional[bool] = None
    
    @validator('title')
    def validate_title(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip() if v else v


class ContentEditRequest(BaseModel):
    """Request schema for editing content."""
    edit_prompt: str = Field(..., min_length=1, max_length=2000, description="Instructions for the edit")
    edit_type: EditType = Field(EditType.GENERAL, description="Type of edit being requested")
    model: Optional[str] = Field("gpt-4-turbo-preview", description="OpenAI model to use")
    
    @validator('edit_prompt')
    def validate_edit_prompt(cls, v):
        if not v.strip():
            raise ValueError('Edit prompt cannot be empty')
        return v.strip()


class ContentEditResponse(BaseModel):
    """Response schema for content editing."""
    id: uuid.UUID
    generated_content_id: uuid.UUID
    iteration_number: int
    edit_prompt: str
    edit_type: EditType
    previous_text: str
    new_text: str
    diff_summary: Optional[str]
    
    # Text metrics
    previous_word_count: int
    new_word_count: int
    word_count_change: int
    previous_character_count: int
    new_character_count: int
    character_count_change: int
    
    # Token usage
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: float
    
    # Generation metadata
    model_used: str
    generation_time_seconds: Optional[float]
    status: ContentStatus
    
    # Relationships
    edited_by_id: uuid.UUID
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ContentIterationCreate(BaseModel):
    """Schema for creating content iterations."""
    edit_prompt: str = Field(..., min_length=1, max_length=2000)
    edit_type: EditType = Field(EditType.GENERAL)
    model: Optional[str] = Field("gpt-4-turbo-preview")


class ContentIterationResponse(BaseModel):
    """Response schema for content iterations."""
    id: uuid.UUID
    iteration_number: int
    edit_prompt: str
    edit_type: EditType
    diff_summary: Optional[str]
    
    # Text metrics
    word_count_change: int
    character_count_change: int
    
    # Token usage
    total_tokens: int
    estimated_cost: float
    
    # Status
    status: ContentStatus
    
    # Relationships
    edited_by_id: uuid.UUID
    
    # Timestamps
    created_at: datetime
    
    class Config:
        from_attributes = True


class ContentListResponse(BaseModel):
    """Response schema for content listing."""
    id: uuid.UUID
    title: str
    content_type: ContentType
    word_count: int
    version: int
    status: ContentStatus
    is_archived: bool
    
    # Token usage
    total_tokens: int
    estimated_cost: float
    
    # Relationships
    organization_id: uuid.UUID
    created_by_id: uuid.UUID
    style_profile_id: Optional[uuid.UUID]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ContentDetailResponse(ContentGenerationResponse):
    """Extended response schema for content details."""
    is_archived: bool
    iteration_count: int
    total_cost: float
    total_tokens_all_versions: int
    reading_time_minutes: int
    
    # Style profile information
    style_profile_name: Optional[str] = None
    
    # Creator information
    created_by_name: str
    
    class Config:
        from_attributes = True


class ContentSearchParams(BaseModel):
    """Search parameters for content."""
    query: Optional[str] = Field(None, description="Search query for title and content")
    content_type: Optional[ContentType] = None
    status: Optional[ContentStatus] = None
    style_profile_id: Optional[uuid.UUID] = None
    created_by_id: Optional[uuid.UUID] = None
    is_archived: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_word_count: Optional[int] = Field(None, ge=0)
    max_word_count: Optional[int] = Field(None, ge=0)
    page: int = Field(1, ge=1)
    per_page: int = Field(10, ge=1, le=100)
    sort_by: str = Field("created_at", description="Field to sort by")
    sort_order: str = Field("desc", description="Sort order: asc or desc")


class ContentSearchResponse(BaseModel):
    """Response schema for content search."""
    content: List[ContentListResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class ContentStatsResponse(BaseModel):
    """Response schema for content statistics."""
    total_content: int
    total_words: int
    total_tokens: int
    total_cost: float
    content_by_type: Dict[str, int]
    content_by_status: Dict[str, int]
    average_word_count: float
    average_cost_per_content: float
    most_used_style_profiles: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]


class ContentBulkAction(BaseModel):
    """Schema for bulk content actions."""
    content_ids: List[uuid.UUID] = Field(..., min_items=1)
    action: str = Field(..., description="Action to perform: archive, unarchive, delete")
    reason: Optional[str] = Field(None, max_length=500)


class ContentExportRequest(BaseModel):
    """Schema for content export request."""
    content_ids: Optional[List[uuid.UUID]] = None  # If None, export all
    include_iterations: bool = True
    include_metadata: bool = True
    format: str = Field("json", description="Export format: json, markdown, html")
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class ContentExportResponse(BaseModel):
    """Response schema for content export."""
    export_id: uuid.UUID
    status: str  # pending, processing, completed, failed
    download_url: Optional[str] = None
    expires_at: datetime
    created_at: datetime
    content_count: int = 0
