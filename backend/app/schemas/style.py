"""
Pydantic schemas for style management and analysis.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator


class StyleProfileBase(BaseModel):
    """Base schema for style profile."""
    name: str = Field(..., min_length=1, max_length=255, description="Style profile name")
    description: Optional[str] = Field(None, max_length=1000, description="Style profile description")
    tags: List[str] = Field(default_factory=list, description="Style tags")
    is_public: bool = Field(False, description="Whether the style profile is public")


class StyleProfileCreate(StyleProfileBase):
    """Schema for creating a style profile."""
    pass


class StyleProfileUpdate(BaseModel):
    """Schema for updating a style profile."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None

    @validator('tags')
    def validate_tags(cls, v):
        if v is not None and len(v) > 20:
            raise ValueError('Maximum 20 tags allowed')
        return v


class StyleProfileResponse(StyleProfileBase):
    """Schema for style profile response."""
    id: uuid.UUID
    organization_id: uuid.UUID
    created_by_id: Optional[uuid.UUID]
    analysis: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_analyzed_at: Optional[datetime]
    reference_count: int = Field(0, description="Number of reference articles")

    class Config:
        from_attributes = True


class StyleProfileListResponse(BaseModel):
    """Schema for style profile list response."""
    style_profiles: List[StyleProfileResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class ReferenceArticleBase(BaseModel):
    """Base schema for reference article."""
    title: str = Field(..., min_length=1, max_length=500, description="Article title")
    source_url: Optional[str] = Field(None, max_length=1000, description="Source URL")
    original_filename: Optional[str] = Field(None, max_length=255, description="Original filename")


class ReferenceArticleCreate(ReferenceArticleBase):
    """Schema for creating a reference article."""
    content: Optional[str] = Field(None, description="Article content (if not from file)")
    file_size: Optional[str] = Field(None, description="File size")
    mime_type: Optional[str] = Field(None, description="MIME type")


class ReferenceArticleUpdate(BaseModel):
    """Schema for updating a reference article."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    source_url: Optional[str] = Field(None, max_length=1000)
    content: Optional[str] = None


class ReferenceArticleResponse(ReferenceArticleBase):
    """Schema for reference article response."""
    id: uuid.UUID
    style_profile_id: uuid.UUID
    uploaded_by_id: Optional[uuid.UUID]
    organization_id: uuid.UUID
    content: str
    file_size: Optional[str]
    mime_type: Optional[str]
    s3_key: Optional[str]
    processing_status: str
    processing_error: Optional[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime]
    content_length: int = Field(0, description="Content length in characters")
    word_count: int = Field(0, description="Approximate word count")

    class Config:
        from_attributes = True


class ReferenceArticleListResponse(BaseModel):
    """Schema for reference article list response."""
    reference_articles: List[ReferenceArticleResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class AnalysisResult(BaseModel):
    """Schema for style analysis result."""
    style_profile_id: uuid.UUID
    analysis_data: Dict[str, Any] = Field(..., description="Analysis results")
    reference_articles_used: List[uuid.UUID] = Field(..., description="IDs of articles used in analysis")
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_time_seconds: Optional[float] = Field(None, description="Time taken for analysis")
    model_used: Optional[str] = Field(None, description="AI model used for analysis")
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="Analysis confidence score")


class AnalysisRequest(BaseModel):
    """Schema for requesting style analysis."""
    style_profile_id: uuid.UUID
    force_reanalysis: bool = Field(False, description="Force reanalysis even if already analyzed")
    include_metadata: bool = Field(True, description="Include metadata in analysis")


class AnalysisResponse(BaseModel):
    """Schema for analysis response."""
    success: bool
    analysis_result: Optional[AnalysisResult] = None
    message: str
    processing_time_seconds: Optional[float] = None


class StyleSearchParams(BaseModel):
    """Schema for style profile search parameters."""
    query: Optional[str] = Field(None, max_length=255, description="Search query")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    is_public: Optional[bool] = Field(None, description="Filter by public status")
    is_analyzed: Optional[bool] = Field(None, description="Filter by analysis status")
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")

    @validator('sort_by')
    def validate_sort_by(cls, v):
        allowed_fields = ['created_at', 'updated_at', 'name', 'last_analyzed_at', 'reference_count']
        if v not in allowed_fields:
            raise ValueError(f'sort_by must be one of {allowed_fields}')
        return v

    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('sort_order must be "asc" or "desc"')
        return v


class ReferenceArticleSearchParams(BaseModel):
    """Schema for reference article search parameters."""
    style_profile_id: Optional[uuid.UUID] = Field(None, description="Filter by style profile")
    query: Optional[str] = Field(None, max_length=255, description="Search query")
    processing_status: Optional[str] = Field(None, description="Filter by processing status")
    mime_type: Optional[str] = Field(None, description="Filter by MIME type")
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")

    @validator('sort_by')
    def validate_sort_by(cls, v):
        allowed_fields = ['created_at', 'updated_at', 'title', 'processed_at', 'word_count']
        if v not in allowed_fields:
            raise ValueError(f'sort_by must be one of {allowed_fields}')
        return v

    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('sort_order must be "asc" or "desc"')
        return v


class FileUploadResponse(BaseModel):
    """Schema for file upload response."""
    success: bool
    file_id: Optional[uuid.UUID] = None
    filename: str
    file_size: int
    mime_type: str
    s3_key: Optional[str] = None
    message: str


class BulkStyleAction(BaseModel):
    """Schema for bulk style profile actions."""
    style_profile_ids: List[uuid.UUID] = Field(..., min_items=1, max_items=100)
    action: str = Field(..., description="Action to perform")

    @validator('action')
    def validate_action(cls, v):
        allowed_actions = ['activate', 'deactivate', 'delete', 'analyze']
        if v not in allowed_actions:
            raise ValueError(f'action must be one of {allowed_actions}')
        return v


class StyleStatsResponse(BaseModel):
    """Schema for style statistics response."""
    total_style_profiles: int
    active_style_profiles: int
    analyzed_style_profiles: int
    total_reference_articles: int
    processed_reference_articles: int
    total_tags: int
    most_used_tags: List[Dict[str, Union[str, int]]]
    recent_activity: List[Dict[str, Any]]
