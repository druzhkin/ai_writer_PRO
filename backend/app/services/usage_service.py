"""
Usage tracking service for monitoring API usage and costs.
"""

import uuid
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, asc
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.api_usage import APIUsage
from app.models.organization import Organization
from app.models.user import User


class UsageService:
    """Service for tracking and managing API usage."""
    
    async def track_usage(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        user_id: Optional[uuid.UUID],
        service_type: str,
        operation_type: str,
        model_used: str,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
        estimated_cost: float,
        request_id: Optional[str] = None,
        response_time_ms: Optional[int] = None,
        success: str = "true"
    ) -> APIUsage:
        """
        Track API usage for billing and analytics.
        
        Args:
            db: Database session
            organization_id: Organization ID
            user_id: User ID (optional for system operations)
            service_type: Type of service (content_generation, content_editing, style_analysis)
            operation_type: Type of operation (generate, edit, analyze)
            model_used: OpenAI model used
            input_tokens: Input tokens consumed
            output_tokens: Output tokens generated
            total_tokens: Total tokens used
            estimated_cost: Estimated cost in USD
            request_id: Optional request ID for tracking
            response_time_ms: Response time in milliseconds
            success: Success status (true, false, partial)
            
        Returns:
            APIUsage record
        """
        # Calculate pricing information
        input_cost_per_1k, output_cost_per_1k = self._get_model_pricing(model_used)
        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k
        
        # Create usage record
        usage = APIUsage(
            organization_id=organization_id,
            user_id=user_id,
            service_type=service_type,
            operation_type=operation_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=estimated_cost,
            model_used=model_used,
            input_cost_per_1k=input_cost_per_1k,
            output_cost_per_1k=output_cost_per_1k,
            request_id=request_id,
            response_time_ms=response_time_ms,
            success=success,
            usage_date=date.today(),
            usage_hour=datetime.now().hour
        )
        
        db.add(usage)
        await db.commit()
        await db.refresh(usage)
        
        return usage
    
    async def get_usage_analytics(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        user_id: Optional[uuid.UUID] = None,
        service_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get usage analytics for an organization.
        
        Args:
            db: Database session
            organization_id: Organization ID
            start_date: Start date for analytics (default: 30 days ago)
            end_date: End date for analytics (default: today)
            user_id: Optional user ID to filter by
            service_type: Optional service type to filter by
            
        Returns:
            Dictionary with usage analytics
        """
        # Set default date range
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Base query
        query = select(APIUsage).where(
            and_(
                APIUsage.organization_id == organization_id,
                APIUsage.usage_date >= start_date,
                APIUsage.usage_date <= end_date
            )
        )
        
        # Apply filters
        if user_id:
            query = query.where(APIUsage.user_id == user_id)
        if service_type:
            query = query.where(APIUsage.service_type == service_type)
        
        # Get total usage
        total_query = select(
            func.count(APIUsage.id).label('total_requests'),
            func.sum(APIUsage.input_tokens).label('total_input_tokens'),
            func.sum(APIUsage.output_tokens).label('total_output_tokens'),
            func.sum(APIUsage.total_tokens).label('total_tokens'),
            func.sum(APIUsage.total_cost).label('total_cost'),
            func.avg(APIUsage.response_time_ms).label('avg_response_time')
        ).where(query.whereclause)
        
        total_result = await db.execute(total_query)
        total_stats = total_result.first()
        
        # Get usage by service type
        service_query = select(
            APIUsage.service_type,
            func.count(APIUsage.id).label('requests'),
            func.sum(APIUsage.total_tokens).label('tokens'),
            func.sum(APIUsage.total_cost).label('cost')
        ).where(query.whereclause).group_by(APIUsage.service_type)
        
        service_result = await db.execute(service_query)
        usage_by_service = {
            row.service_type: {
                "requests": row.requests,
                "tokens": row.tokens or 0,
                "cost": float(row.cost or 0)
            }
            for row in service_result
        }
        
        # Get usage by model
        model_query = select(
            APIUsage.model_used,
            func.count(APIUsage.id).label('requests'),
            func.sum(APIUsage.total_tokens).label('tokens'),
            func.sum(APIUsage.total_cost).label('cost')
        ).where(query.whereclause).group_by(APIUsage.model_used)
        
        model_result = await db.execute(model_query)
        usage_by_model = {
            row.model_used: {
                "requests": row.requests,
                "tokens": row.tokens or 0,
                "cost": float(row.cost or 0)
            }
            for row in model_result
        }
        
        # Get daily usage
        daily_query = select(
            APIUsage.usage_date,
            func.count(APIUsage.id).label('requests'),
            func.sum(APIUsage.total_tokens).label('tokens'),
            func.sum(APIUsage.total_cost).label('cost')
        ).where(query.whereclause).group_by(APIUsage.usage_date).order_by(APIUsage.usage_date)
        
        daily_result = await db.execute(daily_query)
        daily_usage = [
            {
                "date": row.usage_date.isoformat(),
                "requests": row.requests,
                "tokens": row.tokens or 0,
                "cost": float(row.cost or 0)
            }
            for row in daily_result
        ]
        
        # Get hourly usage (last 24 hours)
        hourly_query = select(
            APIUsage.usage_hour,
            func.count(APIUsage.id).label('requests'),
            func.sum(APIUsage.total_tokens).label('tokens'),
            func.sum(APIUsage.total_cost).label('cost')
        ).where(
            and_(
                APIUsage.organization_id == organization_id,
                APIUsage.usage_date >= date.today() - timedelta(days=1)
            )
        ).group_by(APIUsage.usage_hour).order_by(APIUsage.usage_hour)
        
        hourly_result = await db.execute(hourly_query)
        hourly_usage = [
            {
                "hour": row.usage_hour,
                "requests": row.requests,
                "tokens": row.tokens or 0,
                "cost": float(row.cost or 0)
            }
            for row in hourly_result
        ]
        
        # Get top users
        user_query = select(
            User.username,
            User.email,
            func.count(APIUsage.id).label('requests'),
            func.sum(APIUsage.total_tokens).label('tokens'),
            func.sum(APIUsage.total_cost).label('cost')
        ).join(APIUsage).where(query.whereclause).group_by(
            User.id, User.username, User.email
        ).order_by(desc('tokens')).limit(10)
        
        user_result = await db.execute(user_query)
        top_users = [
            {
                "username": row.username,
                "email": row.email,
                "requests": row.requests,
                "tokens": row.tokens or 0,
                "cost": float(row.cost or 0)
            }
            for row in user_result
        ]
        
        # Get success rate
        success_query = select(
            APIUsage.success,
            func.count(APIUsage.id).label('count')
        ).where(query.whereclause).group_by(APIUsage.success)
        
        success_result = await db.execute(success_query)
        success_stats = {row.success: row.count for row in success_result}
        
        total_requests = sum(success_stats.values())
        success_rate = (success_stats.get("true", 0) / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days + 1
            },
            "total_usage": {
                "requests": total_stats.total_requests or 0,
                "input_tokens": total_stats.total_input_tokens or 0,
                "output_tokens": total_stats.total_output_tokens or 0,
                "total_tokens": total_stats.total_tokens or 0,
                "total_cost": float(total_stats.total_cost or 0),
                "avg_response_time_ms": float(total_stats.avg_response_time or 0),
                "success_rate": round(success_rate, 2)
            },
            "usage_by_service": usage_by_service,
            "usage_by_model": usage_by_model,
            "daily_usage": daily_usage,
            "hourly_usage": hourly_usage,
            "top_users": top_users,
            "success_breakdown": success_stats
        }
    
    async def get_usage_limits(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Get usage limits and current usage for an organization.
        
        Args:
            db: Database session
            organization_id: Organization ID
            
        Returns:
            Dictionary with usage limits and current usage
        """
        # Get organization subscription plan
        org_query = select(Organization.subscription_plan).where(
            Organization.id == organization_id
        )
        org_result = await db.execute(org_query)
        subscription_plan = org_result.scalar()
        
        # Get daily limits based on plan
        daily_limits = self._get_daily_limits(subscription_plan)
        
        # Get current daily usage
        today = date.today()
        usage_query = select(
            func.sum(APIUsage.total_tokens).label('tokens'),
            func.sum(APIUsage.total_cost).label('cost')
        ).where(
            and_(
                APIUsage.organization_id == organization_id,
                APIUsage.usage_date == today
            )
        )
        
        usage_result = await db.execute(usage_query)
        current_usage = usage_result.first()
        
        # Get monthly usage
        month_start = today.replace(day=1)
        monthly_query = select(
            func.sum(APIUsage.total_tokens).label('tokens'),
            func.sum(APIUsage.total_cost).label('cost')
        ).where(
            and_(
                APIUsage.organization_id == organization_id,
                APIUsage.usage_date >= month_start,
                APIUsage.usage_date <= today
            )
        )
        
        monthly_result = await db.execute(monthly_query)
        monthly_usage = monthly_result.first()
        
        # Calculate usage percentages
        daily_token_usage = current_usage.tokens or 0
        daily_cost_usage = float(current_usage.cost or 0)
        monthly_token_usage = monthly_usage.tokens or 0
        monthly_cost_usage = float(monthly_usage.cost or 0)
        
        daily_token_percentage = (daily_token_usage / daily_limits["tokens"] * 100) if daily_limits["tokens"] > 0 else 0
        monthly_token_percentage = (monthly_token_usage / daily_limits["tokens"] * 100) if daily_limits["tokens"] > 0 else 0
        
        return {
            "subscription_plan": subscription_plan,
            "daily_limits": daily_limits,
            "current_usage": {
                "daily": {
                    "tokens": daily_token_usage,
                    "cost": daily_cost_usage,
                    "token_percentage": round(daily_token_percentage, 2)
                },
                "monthly": {
                    "tokens": monthly_token_usage,
                    "cost": monthly_cost_usage,
                    "token_percentage": round(monthly_token_percentage, 2)
                }
            },
            "status": {
                "daily_limit_exceeded": daily_token_usage >= daily_limits["tokens"],
                "monthly_limit_exceeded": monthly_token_usage >= daily_limits["tokens"],
                "warnings": self._get_usage_warnings(daily_token_percentage, monthly_token_percentage)
            }
        }
    
    async def get_cost_breakdown(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get detailed cost breakdown for an organization.
        
        Args:
            db: Database session
            organization_id: Organization ID
            start_date: Start date for breakdown
            end_date: End date for breakdown
            
        Returns:
            Dictionary with cost breakdown
        """
        # Set default date range
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Get cost breakdown by model
        model_query = select(
            APIUsage.model_used,
            func.count(APIUsage.id).label('requests'),
            func.sum(APIUsage.input_tokens).label('input_tokens'),
            func.sum(APIUsage.output_tokens).label('output_tokens'),
            func.sum(APIUsage.input_cost).label('input_cost'),
            func.sum(APIUsage.output_cost).label('output_cost'),
            func.sum(APIUsage.total_cost).label('total_cost'),
            func.avg(APIUsage.input_cost_per_1k).label('avg_input_cost_per_1k'),
            func.avg(APIUsage.output_cost_per_1k).label('avg_output_cost_per_1k')
        ).where(
            and_(
                APIUsage.organization_id == organization_id,
                APIUsage.usage_date >= start_date,
                APIUsage.usage_date <= end_date
            )
        ).group_by(APIUsage.model_used)
        
        model_result = await db.execute(model_query)
        cost_by_model = [
            {
                "model": row.model_used,
                "requests": row.requests,
                "input_tokens": row.input_tokens or 0,
                "output_tokens": row.output_tokens or 0,
                "input_cost": float(row.input_cost or 0),
                "output_cost": float(row.output_cost or 0),
                "total_cost": float(row.total_cost or 0),
                "avg_input_cost_per_1k": float(row.avg_input_cost_per_1k or 0),
                "avg_output_cost_per_1k": float(row.avg_output_cost_per_1k or 0),
                "cost_per_request": float(row.total_cost or 0) / row.requests if row.requests > 0 else 0
            }
            for row in model_result
        ]
        
        # Get total costs
        total_query = select(
            func.sum(APIUsage.input_cost).label('total_input_cost'),
            func.sum(APIUsage.output_cost).label('total_output_cost'),
            func.sum(APIUsage.total_cost).label('total_cost'),
            func.count(APIUsage.id).label('total_requests')
        ).where(
            and_(
                APIUsage.organization_id == organization_id,
                APIUsage.usage_date >= start_date,
                APIUsage.usage_date <= end_date
            )
        )
        
        total_result = await db.execute(total_query)
        total_costs = total_result.first()
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days + 1
            },
            "total_costs": {
                "input_cost": float(total_costs.total_input_cost or 0),
                "output_cost": float(total_costs.total_output_cost or 0),
                "total_cost": float(total_costs.total_cost or 0),
                "total_requests": total_costs.total_requests or 0,
                "avg_cost_per_request": float(total_costs.total_cost or 0) / (total_costs.total_requests or 1)
            },
            "cost_by_model": cost_by_model
        }
    
    def _get_model_pricing(self, model: str) -> Tuple[float, float]:
        """Get pricing for a specific model."""
        if "gpt-4" in model.lower():
            if "turbo" in model.lower():
                return (
                    settings.OPENAI_GPT4_TURBO_INPUT_COST_PER_1K,
                    settings.OPENAI_GPT4_TURBO_OUTPUT_COST_PER_1K
                )
            else:
                return (
                    settings.OPENAI_GPT4_INPUT_COST_PER_1K,
                    settings.OPENAI_GPT4_OUTPUT_COST_PER_1K
                )
        else:
            # Default to GPT-4 pricing for unknown models
            return (
                settings.OPENAI_GPT4_INPUT_COST_PER_1K,
                settings.OPENAI_GPT4_OUTPUT_COST_PER_1K
            )
    
    def _get_daily_limits(self, subscription_plan: str) -> Dict[str, int]:
        """Get daily limits based on subscription plan."""
        limits = {
            "free": settings.FREE_PLAN_DAILY_TOKENS,
            "basic": settings.BASIC_PLAN_DAILY_TOKENS,
            "pro": settings.PRO_PLAN_DAILY_TOKENS,
            "enterprise": settings.ENTERPRISE_PLAN_DAILY_TOKENS
        }
        
        daily_tokens = limits.get(subscription_plan, limits["free"])
        
        return {
            "tokens": daily_tokens,
            "requests": daily_tokens // 1000,  # Rough estimate
            "cost": daily_tokens * 0.03 / 1000  # Rough estimate
        }
    
    def _get_usage_warnings(self, daily_percentage: float, monthly_percentage: float) -> List[str]:
        """Get usage warnings based on percentages."""
        warnings = []
        
        if daily_percentage >= 90:
            warnings.append("Daily token limit nearly exceeded")
        elif daily_percentage >= 75:
            warnings.append("Daily token usage is high")
        
        if monthly_percentage >= 90:
            warnings.append("Monthly token limit nearly exceeded")
        elif monthly_percentage >= 75:
            warnings.append("Monthly token usage is high")
        
        return warnings
