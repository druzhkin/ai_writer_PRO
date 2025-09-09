"""
Content generation service for managing AI-generated content.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.generated_content import GeneratedContent
from app.models.content_iteration import ContentIteration
from app.models.style_profile import StyleProfile
from app.models.user import User
from app.models.organization import Organization
from app.schemas.content import (
    ContentGenerationRequest, ContentGenerationResponse, ContentUpdateRequest,
    ContentEditRequest, ContentEditResponse, ContentSearchParams, ContentSearchResponse,
    ContentDetailResponse, ContentListResponse, ContentStatsResponse, ContentType, ContentStatus
)
from app.services.openai_service import OpenAIService
from app.services.usage_service import UsageService


class ContentService:
    """Service for managing AI-generated content."""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.usage_service = UsageService()
    
    async def generate_content(
        self,
        db: AsyncSession,
        request: ContentGenerationRequest,
        organization_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Tuple[bool, str, Optional[ContentGenerationResponse]]:
        """
        Generate new content using AI.
        
        Args:
            db: Database session
            request: Content generation request
            organization_id: Organization ID
            user_id: User ID
            
        Returns:
            Tuple of (success, error_message, content_response)
        """
        try:
            # Check usage limits before generation
            limits = await self.usage_service.get_usage_limits(db, organization_id)
            if limits["status"]["daily_limit_exceeded"]:
                return False, "Daily usage limit exceeded. Please upgrade your plan or try again tomorrow.", None
            
            # Validate content length constraints (word-based)
            if request.target_length:
                if request.target_length < settings.MIN_TARGET_WORDS:
                    return False, f"Target length must be at least {settings.MIN_TARGET_WORDS} words", None
                if request.target_length > settings.MAX_TARGET_WORDS:
                    return False, f"Target length cannot exceed {settings.MAX_TARGET_WORDS} words", None
            
            # Get style profile if specified
            style_analysis = None
            if request.style_profile_id:
                style_profile = await self._get_style_profile(db, request.style_profile_id, organization_id)
                if not style_profile:
                    return False, "Style profile not found or access denied", None
                style_analysis = style_profile.analysis
            
            # Generate content using OpenAI
            success, error_msg, generation_result = await self.openai_service.generate_content(
                title=request.title,
                brief=request.brief,
                content_type=request.content_type.value,
                style_analysis=style_analysis,
                target_length=request.target_length,
                additional_instructions=request.additional_instructions,
                model=request.model
            )
            
            if not success:
                return False, error_msg, None
            
            # Create content record
            content = GeneratedContent(
                organization_id=organization_id,
                created_by_id=user_id,
                style_profile_id=request.style_profile_id,
                title=request.title,
                brief=request.brief,
                content_type=request.content_type.value,
                generated_text=generation_result["generated_text"],
                word_count=generation_result["word_count"],
                character_count=generation_result["character_count"],
                input_tokens=generation_result["input_tokens"],
                output_tokens=generation_result["output_tokens"],
                total_tokens=generation_result["total_tokens"],
                estimated_cost=generation_result["estimated_cost"],
                model_used=generation_result["model_used"],
                generation_prompt=generation_result["generation_prompt"],
                status=ContentStatus.COMPLETED.value
            )
            
            db.add(content)
            await db.commit()
            await db.refresh(content)
            
            # Track usage
            await self.usage_service.track_usage(
                db=db,
                organization_id=organization_id,
                user_id=user_id,
                service_type="content_generation",
                operation_type="generate",
                model_used=generation_result["model_used"],
                input_tokens=generation_result["input_tokens"],
                output_tokens=generation_result["output_tokens"],
                total_tokens=generation_result["total_tokens"],
                estimated_cost=generation_result["estimated_cost"]
            )
            
            # Convert to response
            response = await self._content_to_response(db, content)
            return True, "Content generated successfully", response
            
        except Exception as e:
            await db.rollback()
            return False, f"Content generation failed: {str(e)}", None
    
    async def edit_content(
        self,
        db: AsyncSession,
        content_id: uuid.UUID,
        request: ContentEditRequest,
        organization_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Tuple[bool, str, Optional[ContentEditResponse]]:
        """
        Edit existing content using AI.
        
        Args:
            db: Database session
            content_id: Content ID to edit
            request: Content edit request
            organization_id: Organization ID
            user_id: User ID
            
        Returns:
            Tuple of (success, error_message, edit_response)
        """
        try:
            # Check usage limits before editing
            limits = await self.usage_service.get_usage_limits(db, organization_id)
            if limits["status"]["daily_limit_exceeded"]:
                return False, "Daily usage limit exceeded. Please upgrade your plan or try again tomorrow.", None
            
            # Get content
            content = await self._get_content(db, content_id, organization_id)
            if not content:
                return False, "Content not found or access denied", None
            
            # Check if content has too many iterations
            if len(content.iterations) >= settings.MAX_CONTENT_ITERATIONS:
                return False, f"Maximum iterations limit ({settings.MAX_CONTENT_ITERATIONS}) reached", None
            
            # Edit content using OpenAI
            success, error_msg, edit_result = await self.openai_service.edit_content(
                current_text=content.generated_text,
                edit_prompt=request.edit_prompt,
                edit_type=request.edit_type.value,
                model=request.model
            )
            
            if not success:
                return False, error_msg, None
            
            # Create iteration record
            iteration = ContentIteration(
                generated_content_id=content_id,
                edited_by_id=user_id,
                iteration_number=len(content.iterations) + 1,
                edit_prompt=request.edit_prompt,
                edit_type=request.edit_type.value,
                previous_text=edit_result["previous_text"],
                new_text=edit_result["new_text"],
                diff_summary=edit_result["diff_summary"],
                diff_lines=edit_result.get("diff_lines"),  # Store detailed diff lines
                previous_word_count=edit_result["previous_word_count"],
                new_word_count=edit_result["new_word_count"],
                word_count_change=edit_result["word_count_change"],
                previous_character_count=edit_result["previous_character_count"],
                new_character_count=edit_result["new_character_count"],
                character_count_change=edit_result["character_count_change"],
                input_tokens=edit_result["input_tokens"],
                output_tokens=edit_result["output_tokens"],
                total_tokens=edit_result["total_tokens"],
                estimated_cost=edit_result["estimated_cost"],
                model_used=edit_result["model_used"],
                generation_prompt=edit_result["generation_prompt"],
                status=ContentStatus.COMPLETED.value
            )
            
            # Create new version of content (versioning model)
            new_content = GeneratedContent(
                organization_id=content.organization_id,
                created_by_id=content.created_by_id,
                style_profile_id=content.style_profile_id,
                title=content.title,
                brief=content.brief,
                content_type=content.content_type,
                generated_text=edit_result["new_text"],
                word_count=edit_result["new_word_count"],
                character_count=edit_result["new_character_count"],
                version=content.version + 1,
                is_current=True,
                input_tokens=content.input_tokens,
                output_tokens=content.output_tokens,
                total_tokens=content.total_tokens,
                estimated_cost=content.estimated_cost,
                model_used=content.model_used,
                generation_time_seconds=content.generation_time_seconds,
                generation_prompt=content.generation_prompt,
                status=content.status,
                is_archived=content.is_archived
            )
            
            # Set previous version as not current
            content.is_current = False
            
            db.add(new_content)
            db.add(iteration)
            await db.commit()
            await db.refresh(new_content)
            await db.refresh(iteration)
            
            # Track usage
            await self.usage_service.track_usage(
                db=db,
                organization_id=organization_id,
                user_id=user_id,
                service_type="content_editing",
                operation_type="edit",
                model_used=edit_result["model_used"],
                input_tokens=edit_result["input_tokens"],
                output_tokens=edit_result["output_tokens"],
                total_tokens=edit_result["total_tokens"],
                estimated_cost=edit_result["estimated_cost"]
            )
            
            # Convert to response using new content
            response = await self._iteration_to_response(db, iteration)
            return True, "Content edited successfully", response
            
        except Exception as e:
            await db.rollback()
            return False, f"Content editing failed: {str(e)}", None
    
    async def get_content(
        self,
        db: AsyncSession,
        content_id: uuid.UUID,
        organization_id: uuid.UUID
    ) -> Optional[ContentDetailResponse]:
        """Get content by ID with full details."""
        content = await self._get_content_with_relations(db, content_id, organization_id)
        if not content:
            return None
        
        return await self._content_to_detail_response(db, content)
    
    async def list_content(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        search_params: ContentSearchParams
    ) -> ContentSearchResponse:
        """List content with filtering and pagination."""
        # Build filters helper
        filters = self._build_filters(search_params, organization_id)
        
        # Build main query
        query = select(GeneratedContent).where(and_(*filters))
        
        # Apply sorting
        if search_params.sort_by == "created_at":
            sort_column = GeneratedContent.created_at
        elif search_params.sort_by == "updated_at":
            sort_column = GeneratedContent.updated_at
        elif search_params.sort_by == "title":
            sort_column = GeneratedContent.title
        elif search_params.sort_by == "word_count":
            sort_column = GeneratedContent.word_count
        elif search_params.sort_by == "estimated_cost":
            sort_column = GeneratedContent.estimated_cost
        else:
            sort_column = GeneratedContent.created_at
        
        if search_params.sort_order == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))
        
        # Get total count with same filters
        count_query = select(func.count(GeneratedContent.id)).where(and_(*filters))
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (search_params.page - 1) * search_params.per_page
        query = query.offset(offset).limit(search_params.per_page)
        
        # Execute query
        result = await db.execute(query)
        content_list = result.scalars().all()
        
        # Convert to response
        content_responses = []
        for content in content_list:
            response = await self._content_to_list_response(db, content)
            content_responses.append(response)
        
        # Calculate pagination info
        has_next = (search_params.page * search_params.per_page) < total
        has_prev = search_params.page > 1
        
        return ContentSearchResponse(
            content=content_responses,
            total=total,
            page=search_params.page,
            per_page=search_params.per_page,
            has_next=has_next,
            has_prev=has_prev
        )
    
    def _build_filters(self, search_params: ContentSearchParams, organization_id: uuid.UUID) -> List:
        """Build list of SQLAlchemy filter expressions."""
        filters = [
            GeneratedContent.organization_id == organization_id,
            GeneratedContent.is_current == True
        ]
        
        if search_params.query:
            filters.append(
                or_(
                    GeneratedContent.title.ilike(f"%{search_params.query}%"),
                    GeneratedContent.generated_text.ilike(f"%{search_params.query}%")
                )
            )
        
        if search_params.content_type:
            filters.append(GeneratedContent.content_type == search_params.content_type.value)
        
        if search_params.status:
            filters.append(GeneratedContent.status == search_params.status.value)
        
        if search_params.style_profile_id:
            filters.append(GeneratedContent.style_profile_id == search_params.style_profile_id)
        
        if search_params.created_by_id:
            filters.append(GeneratedContent.created_by_id == search_params.created_by_id)
        
        if search_params.is_archived is not None:
            filters.append(GeneratedContent.is_archived == search_params.is_archived)
        
        if search_params.date_from:
            filters.append(GeneratedContent.created_at >= search_params.date_from)
        
        if search_params.date_to:
            filters.append(GeneratedContent.created_at <= search_params.date_to)
        
        if search_params.min_word_count:
            filters.append(GeneratedContent.word_count >= search_params.min_word_count)
        
        if search_params.max_word_count:
            filters.append(GeneratedContent.word_count <= search_params.max_word_count)
        
        return filters
    
    async def update_content(
        self,
        db: AsyncSession,
        content_id: uuid.UUID,
        request: ContentUpdateRequest,
        organization_id: uuid.UUID
    ) -> Tuple[bool, str, Optional[ContentGenerationResponse]]:
        """Update content metadata."""
        content = await self._get_content(db, content_id, organization_id)
        if not content:
            return False, "Content not found or access denied", None
        
        try:
            # Update fields
            if request.title is not None:
                content.title = request.title
            if request.brief is not None:
                content.brief = request.brief
            if request.is_archived is not None:
                content.is_archived = request.is_archived
            
            content.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(content)
            
            response = await self._content_to_response(db, content)
            return True, "Content updated successfully", response
            
        except Exception as e:
            await db.rollback()
            return False, f"Content update failed: {str(e)}", None
    
    async def delete_content(
        self,
        db: AsyncSession,
        content_id: uuid.UUID,
        organization_id: uuid.UUID
    ) -> Tuple[bool, str]:
        """Delete content."""
        content = await self._get_content(db, content_id, organization_id)
        if not content:
            return False, "Content not found or access denied"
        
        try:
            await db.delete(content)
            await db.commit()
            return True, "Content deleted successfully"
            
        except Exception as e:
            await db.rollback()
            return False, f"Content deletion failed: {str(e)}"
    
    async def get_content_iterations(
        self,
        db: AsyncSession,
        content_id: uuid.UUID,
        organization_id: uuid.UUID
    ) -> List[ContentEditResponse]:
        """Get all iterations for a content piece."""
        content = await self._get_content(db, content_id, organization_id)
        if not content:
            return []
        
        iterations = await db.execute(
            select(ContentIteration)
            .where(ContentIteration.generated_content_id == content_id)
            .order_by(ContentIteration.iteration_number)
        )
        
        iteration_list = iterations.scalars().all()
        responses = []
        
        for iteration in iteration_list:
            response = await self._iteration_to_response(db, iteration)
            responses.append(response)
        
        return responses
    
    async def get_content_stats(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID
    ) -> ContentStatsResponse:
        """Get content statistics for organization."""
        # Get basic stats (only current versions)
        stats_query = select(
            func.count(GeneratedContent.id).label('total_content'),
            func.sum(GeneratedContent.word_count).label('total_words'),
            func.sum(GeneratedContent.total_tokens).label('total_tokens'),
            func.sum(GeneratedContent.estimated_cost).label('total_cost'),
            func.avg(GeneratedContent.word_count).label('avg_word_count'),
            func.avg(GeneratedContent.estimated_cost).label('avg_cost')
        ).where(
            and_(
                GeneratedContent.organization_id == organization_id,
                GeneratedContent.is_current == True
            )
        )
        
        stats_result = await db.execute(stats_query)
        stats = stats_result.first()
        
        # Get iteration stats
        iteration_stats_query = select(
            func.sum(ContentIteration.total_tokens).label('iteration_tokens'),
            func.sum(ContentIteration.estimated_cost).label('iteration_cost')
        ).join(GeneratedContent).where(
            and_(
                GeneratedContent.organization_id == organization_id,
                GeneratedContent.is_current == True
            )
        )
        
        iteration_result = await db.execute(iteration_stats_query)
        iteration_stats = iteration_result.first()
        
        # Combine base and iteration stats
        total_tokens = (stats.total_tokens or 0) + (iteration_stats.iteration_tokens or 0)
        total_cost = (stats.total_cost or 0) + (iteration_stats.iteration_cost or 0)
        
        # Get content by type (only current versions)
        type_query = select(
            GeneratedContent.content_type,
            func.count(GeneratedContent.id).label('count')
        ).where(
            and_(
                GeneratedContent.organization_id == organization_id,
                GeneratedContent.is_current == True
            )
        ).group_by(GeneratedContent.content_type)
        
        type_result = await db.execute(type_query)
        content_by_type = {row.content_type: row.count for row in type_result}
        
        # Get content by status (only current versions)
        status_query = select(
            GeneratedContent.status,
            func.count(GeneratedContent.id).label('count')
        ).where(
            and_(
                GeneratedContent.organization_id == organization_id,
                GeneratedContent.is_current == True
            )
        ).group_by(GeneratedContent.status)
        
        status_result = await db.execute(status_query)
        content_by_status = {row.status: row.count for row in status_result}
        
        # Get most used style profiles (only current versions)
        style_query = select(
            StyleProfile.name,
            func.count(GeneratedContent.id).label('count')
        ).join(GeneratedContent).where(
            and_(
                GeneratedContent.organization_id == organization_id,
                GeneratedContent.is_current == True
            )
        ).group_by(StyleProfile.name).order_by(desc('count')).limit(5)
        
        style_result = await db.execute(style_query)
        most_used_styles = [
            {"name": row.name, "count": row.count} 
            for row in style_result
        ]
        
        # Get recent activity (last 10 content pieces, only current versions)
        recent_query = select(GeneratedContent).where(
            and_(
                GeneratedContent.organization_id == organization_id,
                GeneratedContent.is_current == True
            )
        ).order_by(desc(GeneratedContent.created_at)).limit(10)
        
        recent_result = await db.execute(recent_query)
        recent_content = recent_result.scalars().all()
        
        recent_activity = [
            {
                "id": str(content.id),
                "title": content.title,
                "content_type": content.content_type,
                "created_at": content.created_at.isoformat(),
                "word_count": content.word_count
            }
            for content in recent_content
        ]
        
        return ContentStatsResponse(
            total_content=stats.total_content or 0,
            total_words=stats.total_words or 0,
            total_tokens=total_tokens,
            total_cost=float(total_cost),
            content_by_type=content_by_type,
            content_by_status=content_by_status,
            average_word_count=float(stats.avg_word_count or 0),
            average_cost_per_content=float(stats.avg_cost or 0),
            most_used_style_profiles=most_used_styles,
            recent_activity=recent_activity
        )
    
    # Helper methods
    async def _get_content(
        self,
        db: AsyncSession,
        content_id: uuid.UUID,
        organization_id: uuid.UUID
    ) -> Optional[GeneratedContent]:
        """Get current version of content by ID with organization check."""
        result = await db.execute(
            select(GeneratedContent).where(
                and_(
                    GeneratedContent.id == content_id,
                    GeneratedContent.organization_id == organization_id,
                    GeneratedContent.is_current == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def _get_content_with_relations(
        self,
        db: AsyncSession,
        content_id: uuid.UUID,
        organization_id: uuid.UUID
    ) -> Optional[GeneratedContent]:
        """Get current version of content with all relations loaded."""
        result = await db.execute(
            select(GeneratedContent)
            .options(
                selectinload(GeneratedContent.iterations),
                selectinload(GeneratedContent.style_profile),
                selectinload(GeneratedContent.created_by)
            )
            .where(
                and_(
                    GeneratedContent.id == content_id,
                    GeneratedContent.organization_id == organization_id,
                    GeneratedContent.is_current == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def _get_style_profile(
        self,
        db: AsyncSession,
        style_profile_id: uuid.UUID,
        organization_id: uuid.UUID
    ) -> Optional[StyleProfile]:
        """Get style profile with organization check."""
        result = await db.execute(
            select(StyleProfile).where(
                and_(
                    StyleProfile.id == style_profile_id,
                    StyleProfile.organization_id == organization_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def _content_to_response(
        self,
        db: AsyncSession,
        content: GeneratedContent
    ) -> ContentGenerationResponse:
        """Convert content model to response."""
        return ContentGenerationResponse(
            id=content.id,
            title=content.title,
            brief=content.brief,
            content_type=ContentType(content.content_type),
            generated_text=content.generated_text,
            word_count=content.word_count,
            character_count=content.character_count,
            version=content.version,
            status=ContentStatus(content.status),
            input_tokens=content.input_tokens,
            output_tokens=content.output_tokens,
            total_tokens=content.total_tokens,
            estimated_cost=content.estimated_cost,
            model_used=content.model_used,
            generation_time_seconds=content.generation_time_seconds,
            organization_id=content.organization_id,
            created_by_id=content.created_by_id,
            style_profile_id=content.style_profile_id,
            created_at=content.created_at,
            updated_at=content.updated_at
        )
    
    async def _content_to_list_response(
        self,
        db: AsyncSession,
        content: GeneratedContent
    ) -> ContentListResponse:
        """Convert content model to list response."""
        return ContentListResponse(
            id=content.id,
            title=content.title,
            content_type=ContentType(content.content_type),
            word_count=content.word_count,
            version=content.version,
            status=ContentStatus(content.status),
            is_archived=content.is_archived,
            total_tokens=content.total_tokens,
            estimated_cost=content.estimated_cost,
            organization_id=content.organization_id,
            created_by_id=content.created_by_id,
            style_profile_id=content.style_profile_id,
            created_at=content.created_at,
            updated_at=content.updated_at
        )
    
    async def _content_to_detail_response(
        self,
        db: AsyncSession,
        content: GeneratedContent
    ) -> ContentDetailResponse:
        """Convert content model to detail response."""
        # Get style profile name
        style_profile_name = None
        if content.style_profile:
            style_profile_name = content.style_profile.name
        
        # Get creator name
        creator_name = content.created_by.full_name if content.created_by else "Unknown"
        
        # Calculate totals
        total_cost = content.get_total_cost()
        total_tokens = content.get_total_tokens()
        iteration_count = content.get_iteration_count()
        reading_time = content.reading_time_minutes
        
        base_response = await self._content_to_response(db, content)
        
        return ContentDetailResponse(
            **base_response.dict(),
            is_archived=content.is_archived,
            iteration_count=iteration_count,
            total_cost=total_cost,
            total_tokens_all_versions=total_tokens,
            reading_time_minutes=reading_time,
            style_profile_name=style_profile_name,
            created_by_name=creator_name
        )
    
    async def _iteration_to_response(
        self,
        db: AsyncSession,
        iteration: ContentIteration
    ) -> ContentEditResponse:
        """Convert iteration model to response."""
        return ContentEditResponse(
            id=iteration.id,
            generated_content_id=iteration.generated_content_id,
            iteration_number=iteration.iteration_number,
            edit_prompt=iteration.edit_prompt,
            edit_type=iteration.edit_type,
            previous_text=iteration.previous_text,
            new_text=iteration.new_text,
            diff_summary=iteration.diff_summary,
            previous_word_count=iteration.previous_word_count,
            new_word_count=iteration.new_word_count,
            word_count_change=iteration.word_count_change,
            previous_character_count=iteration.previous_character_count,
            new_character_count=iteration.new_character_count,
            character_count_change=iteration.character_count_change,
            input_tokens=iteration.input_tokens,
            output_tokens=iteration.output_tokens,
            total_tokens=iteration.total_tokens,
            estimated_cost=iteration.estimated_cost,
            model_used=iteration.model_used,
            generation_time_seconds=iteration.generation_time_seconds,
            status=ContentStatus(iteration.status),
            edited_by_id=iteration.edited_by_id,
            created_at=iteration.created_at,
            updated_at=iteration.updated_at
        )
