"""
Analytics service for tracking user interactions, content generation metrics, and usage analytics.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.organization import Organization
from app.models.generated_content import GeneratedContent
from app.models.api_usage import APIUsage
from app.models.style_profile import StyleProfile
from app.core.logging import get_logger

logger = get_logger(__name__)


class AnalyticsService:
    """
    Service for collecting and analyzing application usage data.
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def track_user_action(
        self,
        user_id: str,
        action: str,
        metadata: Optional[Dict[str, Any]] = None,
        organization_id: Optional[str] = None
    ) -> None:
        """Track a user action for analytics."""
        try:
            # This would typically be stored in a separate analytics table
            # For now, we'll log the action
            logger.info(
                "User action tracked",
                user_id=user_id,
                action=action,
                organization_id=organization_id,
                metadata=metadata
            )
            
            # In a real implementation, you might:
            # 1. Store in a dedicated analytics table
            # 2. Send to an external analytics service
            # 3. Update user activity metrics
            
        except Exception as e:
            logger.error("Failed to track user action", error=str(e))
    
    async def track_content_generation(
        self,
        user_id: str,
        content_id: str,
        style_profile_id: str,
        target_words: int,
        tokens_used: int,
        cost: float,
        generation_time: float,
        organization_id: Optional[str] = None
    ) -> None:
        """Track content generation metrics."""
        try:
            await self.track_user_action(
                user_id=user_id,
                action="content_generated",
                metadata={
                    "content_id": content_id,
                    "style_profile_id": style_profile_id,
                    "target_words": target_words,
                    "tokens_used": tokens_used,
                    "cost": cost,
                    "generation_time": generation_time
                },
                organization_id=organization_id
            )
            
            logger.info(
                "Content generation tracked",
                user_id=user_id,
                content_id=content_id,
                tokens_used=tokens_used,
                cost=cost,
                generation_time=generation_time
            )
            
        except Exception as e:
            logger.error("Failed to track content generation", error=str(e))
    
    async def track_style_analysis(
        self,
        user_id: str,
        style_profile_id: str,
        article_count: int,
        analysis_time: float,
        organization_id: Optional[str] = None
    ) -> None:
        """Track style analysis metrics."""
        try:
            await self.track_user_action(
                user_id=user_id,
                action="style_analyzed",
                metadata={
                    "style_profile_id": style_profile_id,
                    "article_count": article_count,
                    "analysis_time": analysis_time
                },
                organization_id=organization_id
            )
            
            logger.info(
                "Style analysis tracked",
                user_id=user_id,
                style_profile_id=style_profile_id,
                article_count=article_count,
                analysis_time=analysis_time
            )
            
        except Exception as e:
            logger.error("Failed to track style analysis", error=str(e))
    
    async def track_file_upload(
        self,
        user_id: str,
        filename: str,
        file_size: int,
        file_type: str,
        organization_id: Optional[str] = None
    ) -> None:
        """Track file upload metrics."""
        try:
            await self.track_user_action(
                user_id=user_id,
                action="file_uploaded",
                metadata={
                    "filename": filename,
                    "file_size": file_size,
                    "file_type": file_type
                },
                organization_id=organization_id
            )
            
            logger.info(
                "File upload tracked",
                user_id=user_id,
                filename=filename,
                file_size=file_size,
                file_type=file_type
            )
            
        except Exception as e:
            logger.error("Failed to track file upload", error=str(e))
    
    async def get_usage_statistics(
        self,
        organization_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get usage statistics for an organization or globally."""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Base query for API usage
            query = select(APIUsage).where(
                and_(
                    APIUsage.created_at >= start_date,
                    APIUsage.created_at <= end_date
                )
            )
            
            if organization_id:
                query = query.where(APIUsage.organization_id == organization_id)
            
            # Get total usage
            result = await self.db_session.execute(query)
            usage_records = result.scalars().all()
            
            # Calculate statistics
            total_requests = len(usage_records)
            total_tokens = sum(record.tokens_used for record in usage_records)
            total_cost = sum(record.cost for record in usage_records)
            avg_response_time = sum(record.response_time for record in usage_records) / total_requests if total_requests > 0 else 0
            
            # Usage by endpoint
            endpoint_usage = {}
            for record in usage_records:
                endpoint = record.endpoint
                if endpoint not in endpoint_usage:
                    endpoint_usage[endpoint] = {
                        "requests": 0,
                        "tokens": 0,
                        "cost": 0
                    }
                endpoint_usage[endpoint]["requests"] += 1
                endpoint_usage[endpoint]["tokens"] += record.tokens_used
                endpoint_usage[endpoint]["cost"] += record.cost
            
            # Usage by date
            daily_usage = {}
            for record in usage_records:
                date = record.created_at.date().isoformat()
                if date not in daily_usage:
                    daily_usage[date] = {
                        "requests": 0,
                        "tokens": 0,
                        "cost": 0
                    }
                daily_usage[date]["requests"] += 1
                daily_usage[date]["tokens"] += record.tokens_used
                daily_usage[date]["cost"] += record.cost
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "total_requests": total_requests,
                "total_tokens": total_tokens,
                "total_cost": round(total_cost, 4),
                "average_response_time": round(avg_response_time, 2),
                "usage_by_endpoint": endpoint_usage,
                "usage_by_date": daily_usage,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to get usage statistics", error=str(e))
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }
    
    async def get_content_generation_metrics(
        self,
        organization_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get content generation metrics."""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Base query for generated content
            query = select(GeneratedContent).where(
                and_(
                    GeneratedContent.created_at >= start_date,
                    GeneratedContent.created_at <= end_date
                )
            )
            
            if organization_id:
                query = query.where(GeneratedContent.organization_id == organization_id)
            
            result = await self.db_session.execute(query)
            content_records = result.scalars().all()
            
            # Calculate metrics
            total_content = len(content_records)
            completed_content = len([c for c in content_records if c.status == "completed"])
            pending_content = len([c for c in content_records if c.status == "pending"])
            failed_content = len([c for c in content_records if c.status == "failed"])
            
            total_words = sum(c.target_words for c in content_records)
            avg_words = total_words / total_content if total_content > 0 else 0
            
            # Content by style profile
            style_usage = {}
            for content in content_records:
                if content.style_profile_id:
                    if content.style_profile_id not in style_usage:
                        style_usage[content.style_profile_id] = 0
                    style_usage[content.style_profile_id] += 1
            
            # Content by date
            daily_content = {}
            for content in content_records:
                date = content.created_at.date().isoformat()
                if date not in daily_content:
                    daily_content[date] = 0
                daily_content[date] += 1
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "total_content": total_content,
                "completed_content": completed_content,
                "pending_content": pending_content,
                "failed_content": failed_content,
                "completion_rate": round(completed_content / total_content * 100, 2) if total_content > 0 else 0,
                "total_words": total_words,
                "average_words": round(avg_words, 0),
                "content_by_style": style_usage,
                "content_by_date": daily_content,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to get content generation metrics", error=str(e))
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }
    
    async def get_user_activity_metrics(
        self,
        organization_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get user activity metrics."""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Get active users
            query = select(User).where(
                and_(
                    User.updated_at >= start_date,
                    User.is_active == True
                )
            )
            
            if organization_id:
                query = query.join(Organization).where(Organization.id == organization_id)
            
            result = await self.db_session.execute(query)
            active_users = result.scalars().all()
            
            # Get new users
            new_users_query = select(User).where(
                and_(
                    User.created_at >= start_date,
                    User.created_at <= end_date
                )
            )
            
            if organization_id:
                new_users_query = new_users_query.join(Organization).where(Organization.id == organization_id)
            
            result = await self.db_session.execute(new_users_query)
            new_users = result.scalars().all()
            
            # Get user engagement (users who generated content)
            engagement_query = select(User).join(GeneratedContent).where(
                and_(
                    GeneratedContent.created_at >= start_date,
                    GeneratedContent.created_at <= end_date
                )
            ).distinct()
            
            if organization_id:
                engagement_query = engagement_query.join(Organization).where(Organization.id == organization_id)
            
            result = await self.db_session.execute(engagement_query)
            engaged_users = result.scalars().all()
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "active_users": len(active_users),
                "new_users": len(new_users),
                "engaged_users": len(engaged_users),
                "engagement_rate": round(len(engaged_users) / len(active_users) * 100, 2) if active_users else 0,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to get user activity metrics", error=str(e))
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }
    
    async def get_organization_metrics(
        self,
        organization_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get comprehensive metrics for an organization."""
        try:
            # Get organization info
            result = await self.db_session.execute(
                select(Organization).where(Organization.id == organization_id)
            )
            organization = result.scalar_one_or_none()
            
            if not organization:
                return {"error": "Organization not found"}
            
            # Get all metrics
            usage_stats = await self.get_usage_statistics(organization_id, start_date, end_date)
            content_metrics = await self.get_content_generation_metrics(organization_id, start_date, end_date)
            user_metrics = await self.get_user_activity_metrics(organization_id, start_date, end_date)
            
            return {
                "organization": {
                    "id": organization.id,
                    "name": organization.name,
                    "plan": organization.subscription_plan,
                    "status": organization.subscription_status
                },
                "usage_statistics": usage_stats,
                "content_metrics": content_metrics,
                "user_metrics": user_metrics,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to get organization metrics", error=str(e))
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }
    
    async def get_global_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get global application metrics."""
        try:
            # Get all metrics globally
            usage_stats = await self.get_usage_statistics(None, start_date, end_date)
            content_metrics = await self.get_content_generation_metrics(None, start_date, end_date)
            user_metrics = await self.get_user_activity_metrics(None, start_date, end_date)
            
            # Get organization count
            result = await self.db_session.execute(select(func.count(Organization.id)))
            total_organizations = result.scalar()
            
            # Get style profile count
            result = await self.db_session.execute(select(func.count(StyleProfile.id)))
            total_style_profiles = result.scalar()
            
            return {
                "usage_statistics": usage_stats,
                "content_metrics": content_metrics,
                "user_metrics": user_metrics,
                "total_organizations": total_organizations,
                "total_style_profiles": total_style_profiles,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to get global metrics", error=str(e))
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }
