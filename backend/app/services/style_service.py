"""
Style service for managing style profiles and reference articles.
"""

import uuid
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.style_profile import StyleProfile
from app.models.reference_article import ReferenceArticle
from app.models.organization import Organization
from app.models.user import User
from app.schemas.style import (
    StyleProfileCreate, StyleProfileUpdate, StyleSearchParams,
    ReferenceArticleCreate, ReferenceArticleUpdate, ReferenceArticleSearchParams
)
from app.services.openai_service import OpenAIService
from app.services.text_extraction_service import TextExtractionService
from app.core.config import settings


class StyleService:
    """Service for style profile and reference article management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.openai_service = OpenAIService()
        self.text_extraction_service = TextExtractionService()
    
    # Style Profile CRUD Operations
    
    async def create_style_profile(
        self, 
        style_data: StyleProfileCreate, 
        organization_id: uuid.UUID,
        created_by_id: uuid.UUID
    ) -> StyleProfile:
        """Create a new style profile."""
        try:
            # Check if style profile with same name exists in organization
            existing = await self.get_style_profile_by_name(organization_id, style_data.name)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Style profile with this name already exists in the organization"
                )
            
            # Create style profile
            style_profile = StyleProfile(
                name=style_data.name,
                description=style_data.description,
                organization_id=organization_id,
                created_by_id=created_by_id,
                tags=style_data.tags or [],
                is_public=style_data.is_public,
                analysis={}
            )
            
            self.db.add(style_profile)
            await self.db.commit()
            await self.db.refresh(style_profile)
            
            return style_profile
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create style profile: {str(e)}"
            )
    
    async def get_style_profile(
        self, 
        style_profile_id: uuid.UUID, 
        organization_id: uuid.UUID
    ) -> Optional[StyleProfile]:
        """Get a style profile by ID."""
        try:
            query = select(StyleProfile).where(
                and_(
                    StyleProfile.id == style_profile_id,
                    StyleProfile.organization_id == organization_id
                )
            ).options(selectinload(StyleProfile.reference_articles))
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get style profile: {str(e)}"
            )
    
    async def get_style_profile_by_name(
        self, 
        organization_id: uuid.UUID, 
        name: str
    ) -> Optional[StyleProfile]:
        """Get a style profile by name within an organization."""
        try:
            query = select(StyleProfile).where(
                and_(
                    StyleProfile.organization_id == organization_id,
                    StyleProfile.name == name
                )
            )
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get style profile by name: {str(e)}"
            )
    
    async def update_style_profile(
        self, 
        style_profile_id: uuid.UUID, 
        organization_id: uuid.UUID,
        update_data: StyleProfileUpdate
    ) -> Optional[StyleProfile]:
        """Update a style profile."""
        try:
            style_profile = await self.get_style_profile(style_profile_id, organization_id)
            if not style_profile:
                return None
            
            # Check name uniqueness if name is being updated
            if update_data.name and update_data.name != style_profile.name:
                existing = await self.get_style_profile_by_name(organization_id, update_data.name)
                if existing and existing.id != style_profile_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Style profile with this name already exists in the organization"
                    )
            
            # Update fields
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(style_profile, field, value)
            
            await self.db.commit()
            await self.db.refresh(style_profile)
            
            return style_profile
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update style profile: {str(e)}"
            )
    
    async def delete_style_profile(
        self, 
        style_profile_id: uuid.UUID, 
        organization_id: uuid.UUID
    ) -> bool:
        """Delete a style profile."""
        try:
            style_profile = await self.get_style_profile(style_profile_id, organization_id)
            if not style_profile:
                return False
            
            await self.db.delete(style_profile)
            await self.db.commit()
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete style profile: {str(e)}"
            )
    
    async def search_style_profiles(
        self, 
        organization_id: uuid.UUID,
        search_params: StyleSearchParams
    ) -> Dict[str, Any]:
        """Search style profiles with filters and pagination."""
        try:
            # Build query
            query = select(StyleProfile).where(
                StyleProfile.organization_id == organization_id
            )
            
            # Apply filters
            if search_params.query:
                query = query.where(
                    or_(
                        StyleProfile.name.ilike(f"%{search_params.query}%"),
                        StyleProfile.description.ilike(f"%{search_params.query}%")
                    )
                )
            
            if search_params.tags:
                for tag in search_params.tags:
                    query = query.where(StyleProfile.tags.contains([tag]))
            
            if search_params.is_public is not None:
                query = query.where(StyleProfile.is_public == search_params.is_public)
            
            if search_params.is_analyzed is not None:
                if search_params.is_analyzed:
                    query = query.where(StyleProfile.last_analyzed_at.isnot(None))
                else:
                    query = query.where(StyleProfile.last_analyzed_at.is_(None))
            
            # Apply sorting
            sort_column = getattr(StyleProfile, search_params.sort_by)
            if search_params.sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar()
            
            # Apply pagination
            offset = (search_params.page - 1) * search_params.per_page
            query = query.offset(offset).limit(search_params.per_page)
            
            # Execute query
            result = await self.db.execute(query)
            style_profiles = result.scalars().all()
            
            # Calculate pagination info
            has_next = offset + search_params.per_page < total
            has_prev = search_params.page > 1
            
            return {
                "style_profiles": style_profiles,
                "total": total,
                "page": search_params.page,
                "per_page": search_params.per_page,
                "has_next": has_next,
                "has_prev": has_prev
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to search style profiles: {str(e)}"
            )
    
    # Reference Article CRUD Operations
    
    async def create_reference_article(
        self, 
        article_data: ReferenceArticleCreate, 
        style_profile_id: uuid.UUID,
        organization_id: uuid.UUID,
        uploaded_by_id: uuid.UUID,
        content: str,
        s3_key: Optional[str] = None
    ) -> ReferenceArticle:
        """Create a new reference article."""
        try:
            # Check if style profile exists
            style_profile = await self.get_style_profile(style_profile_id, organization_id)
            if not style_profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Style profile not found"
                )
            
            # Check reference article limit
            current_count = await self.count_reference_articles(style_profile_id)
            if current_count >= settings.MAX_REFERENCE_ARTICLES_PER_STYLE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Maximum {settings.MAX_REFERENCE_ARTICLES_PER_STYLE} reference articles allowed per style profile"
                )
            
            # Create reference article
            reference_article = ReferenceArticle(
                title=article_data.title,
                content=content,
                source_url=article_data.source_url,
                original_filename=article_data.original_filename,
                file_size=article_data.file_size,
                mime_type=article_data.mime_type,
                s3_key=s3_key,
                style_profile_id=style_profile_id,
                uploaded_by_id=uploaded_by_id,
                organization_id=organization_id,
                processing_status="completed" if content else "pending",
                metadata={}
            )
            
            self.db.add(reference_article)
            await self.db.commit()
            await self.db.refresh(reference_article)
            
            return reference_article
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create reference article: {str(e)}"
            )
    
    async def get_reference_article(
        self, 
        article_id: uuid.UUID, 
        organization_id: uuid.UUID
    ) -> Optional[ReferenceArticle]:
        """Get a reference article by ID."""
        try:
            query = select(ReferenceArticle).where(
                and_(
                    ReferenceArticle.id == article_id,
                    ReferenceArticle.organization_id == organization_id
                )
            )
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get reference article: {str(e)}"
            )
    
    async def update_reference_article(
        self, 
        article_id: uuid.UUID, 
        organization_id: uuid.UUID,
        update_data: ReferenceArticleUpdate
    ) -> Optional[ReferenceArticle]:
        """Update a reference article."""
        try:
            reference_article = await self.get_reference_article(article_id, organization_id)
            if not reference_article:
                return None
            
            # Update fields
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(reference_article, field, value)
            
            await self.db.commit()
            await self.db.refresh(reference_article)
            
            return reference_article
            
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update reference article: {str(e)}"
            )
    
    async def delete_reference_article(
        self, 
        article_id: uuid.UUID, 
        organization_id: uuid.UUID
    ) -> bool:
        """Delete a reference article."""
        try:
            reference_article = await self.get_reference_article(article_id, organization_id)
            if not reference_article:
                return False
            
            await self.db.delete(reference_article)
            await self.db.commit()
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete reference article: {str(e)}"
            )
    
    async def search_reference_articles(
        self, 
        organization_id: uuid.UUID,
        search_params: ReferenceArticleSearchParams
    ) -> Dict[str, Any]:
        """Search reference articles with filters and pagination."""
        try:
            # Build query
            query = select(ReferenceArticle).where(
                ReferenceArticle.organization_id == organization_id
            )
            
            # Apply filters
            if search_params.style_profile_id:
                query = query.where(ReferenceArticle.style_profile_id == search_params.style_profile_id)
            
            if search_params.query:
                query = query.where(
                    or_(
                        ReferenceArticle.title.ilike(f"%{search_params.query}%"),
                        ReferenceArticle.content.ilike(f"%{search_params.query}%")
                    )
                )
            
            if search_params.processing_status:
                query = query.where(ReferenceArticle.processing_status == search_params.processing_status)
            
            if search_params.mime_type:
                query = query.where(ReferenceArticle.mime_type == search_params.mime_type)
            
            # Apply sorting
            sort_column = getattr(ReferenceArticle, search_params.sort_by)
            if search_params.sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar()
            
            # Apply pagination
            offset = (search_params.page - 1) * search_params.per_page
            query = query.offset(offset).limit(search_params.per_page)
            
            # Execute query
            result = await self.db.execute(query)
            reference_articles = result.scalars().all()
            
            # Calculate pagination info
            has_next = offset + search_params.per_page < total
            has_prev = search_params.page > 1
            
            return {
                "reference_articles": reference_articles,
                "total": total,
                "page": search_params.page,
                "per_page": search_params.per_page,
                "has_next": has_next,
                "has_prev": has_prev
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to search reference articles: {str(e)}"
            )
    
    # Analysis Operations
    
    async def analyze_style_profile(
        self, 
        style_profile_id: uuid.UUID, 
        organization_id: uuid.UUID,
        force_reanalysis: bool = False
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Analyze a style profile using reference articles."""
        try:
            # Get style profile with reference articles
            style_profile = await self.get_style_profile(style_profile_id, organization_id)
            if not style_profile:
                return False, "Style profile not found", None
            
            # Check if already analyzed and not forcing reanalysis
            if style_profile.is_analyzed and not force_reanalysis:
                return True, "Style profile already analyzed", style_profile.analysis
            
            # Get processed reference articles
            processed_articles = [
                article for article in style_profile.reference_articles 
                if article.is_processed and article.content
            ]
            
            if not processed_articles:
                return False, "No processed reference articles found for analysis", None
            
            # Extract texts for analysis
            texts = [article.content for article in processed_articles]
            
            # Perform analysis
            success, message, analysis_result = await self.openai_service.analyze_writing_style(
                texts, 
                style_profile.name,
                style_profile.description
            )
            
            if not success:
                return False, f"Analysis failed: {message}", None
            
            # Update style profile with analysis
            style_profile.update_analysis(analysis_result)
            await self.db.commit()
            
            return True, "Style analysis completed successfully", analysis_result
            
        except Exception as e:
            await self.db.rollback()
            return False, f"Style analysis failed: {str(e)}", None
    
    async def count_reference_articles(self, style_profile_id: uuid.UUID) -> int:
        """Count reference articles for a style profile."""
        try:
            query = select(func.count(ReferenceArticle.id)).where(
                ReferenceArticle.style_profile_id == style_profile_id
            )
            
            result = await self.db.execute(query)
            return result.scalar() or 0
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to count reference articles: {str(e)}"
            )
    
    async def get_style_profile_stats(self, organization_id: uuid.UUID) -> Dict[str, Any]:
        """Get statistics for style profiles in an organization."""
        try:
            # Get basic counts
            style_count_query = select(func.count(StyleProfile.id)).where(
                StyleProfile.organization_id == organization_id
            )
            style_count_result = await self.db.execute(style_count_query)
            total_style_profiles = style_count_result.scalar() or 0
            
            active_style_count_query = select(func.count(StyleProfile.id)).where(
                and_(
                    StyleProfile.organization_id == organization_id,
                    StyleProfile.is_active == True
                )
            )
            active_style_count_result = await self.db.execute(active_style_count_query)
            active_style_profiles = active_style_count_result.scalar() or 0
            
            analyzed_style_count_query = select(func.count(StyleProfile.id)).where(
                and_(
                    StyleProfile.organization_id == organization_id,
                    StyleProfile.last_analyzed_at.isnot(None)
                )
            )
            analyzed_style_count_result = await self.db.execute(analyzed_style_count_query)
            analyzed_style_profiles = analyzed_style_count_result.scalar() or 0
            
            # Get reference article counts
            article_count_query = select(func.count(ReferenceArticle.id)).where(
                ReferenceArticle.organization_id == organization_id
            )
            article_count_result = await self.db.execute(article_count_query)
            total_reference_articles = article_count_result.scalar() or 0
            
            processed_article_count_query = select(func.count(ReferenceArticle.id)).where(
                and_(
                    ReferenceArticle.organization_id == organization_id,
                    ReferenceArticle.processing_status == "completed"
                )
            )
            processed_article_count_result = await self.db.execute(processed_article_count_query)
            processed_reference_articles = processed_article_count_result.scalar() or 0
            
            return {
                "total_style_profiles": total_style_profiles,
                "active_style_profiles": active_style_profiles,
                "analyzed_style_profiles": analyzed_style_profiles,
                "total_reference_articles": total_reference_articles,
                "processed_reference_articles": processed_reference_articles
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get style profile stats: {str(e)}"
            )
