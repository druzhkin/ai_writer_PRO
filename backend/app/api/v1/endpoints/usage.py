"""
Usage analytics endpoints for monitoring API usage and costs.
"""

import uuid
from datetime import date, timedelta
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_active_user, get_current_verified_user
from app.services.usage_service import UsageService
from app.models.user import User

router = APIRouter()


@router.get("/analytics")
async def get_usage_analytics(
    organization_id: uuid.UUID,
    start_date: Optional[date] = Query(None, description="Start date for analytics (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for analytics (YYYY-MM-DD)"),
    user_id: Optional[uuid.UUID] = Query(None, description="Filter by specific user"),
    service_type: Optional[str] = Query(None, description="Filter by service type"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get usage analytics for an organization.
    
    Returns comprehensive usage analytics including token consumption,
    costs, success rates, and usage patterns.
    """
    try:
        usage_service = UsageService()
        
        analytics = await usage_service.get_usage_analytics(
            db=db,
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            service_type=service_type
        )
        
        return analytics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get usage analytics: {str(e)}"
        )


@router.get("/limits")
async def get_usage_limits(
    organization_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get usage limits and current usage for an organization.
    
    Returns subscription plan limits, current usage, and warnings
    about approaching limits.
    """
    try:
        usage_service = UsageService()
        
        limits = await usage_service.get_usage_limits(
            db=db,
            organization_id=organization_id
        )
        
        return limits
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get usage limits: {str(e)}"
        )


@router.get("/cost-breakdown")
async def get_cost_breakdown(
    organization_id: uuid.UUID,
    start_date: Optional[date] = Query(None, description="Start date for breakdown (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for breakdown (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get detailed cost breakdown for an organization.
    
    Returns cost analysis by model, service type, and time period
    with detailed pricing information.
    """
    try:
        usage_service = UsageService()
        
        breakdown = await usage_service.get_cost_breakdown(
            db=db,
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return breakdown
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cost breakdown: {str(e)}"
        )


@router.get("/daily-usage")
async def get_daily_usage(
    organization_id: uuid.UUID,
    days: int = Query(30, ge=1, le=365, description="Number of days to retrieve"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get daily usage summary for the specified number of days.
    
    Returns daily token usage, costs, and request counts for trend analysis.
    """
    try:
        usage_service = UsageService()
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        analytics = await usage_service.get_usage_analytics(
            db=db,
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "period": analytics["period"],
            "daily_usage": analytics["daily_usage"],
            "total_usage": analytics["total_usage"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get daily usage: {str(e)}"
        )


@router.get("/hourly-usage")
async def get_hourly_usage(
    organization_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get hourly usage for the last 24 hours.
    
    Returns hourly breakdown of usage for the current day.
    """
    try:
        usage_service = UsageService()
        
        end_date = date.today()
        start_date = end_date - timedelta(days=1)
        
        analytics = await usage_service.get_usage_analytics(
            db=db,
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "period": analytics["period"],
            "hourly_usage": analytics["hourly_usage"],
            "total_usage": analytics["total_usage"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get hourly usage: {str(e)}"
        )


@router.get("/top-users")
async def get_top_users(
    organization_id: uuid.UUID,
    limit: int = Query(10, ge=1, le=50, description="Number of top users to return"),
    start_date: Optional[date] = Query(None, description="Start date for analysis (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for analysis (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get top users by usage within the organization.
    
    Returns users ranked by token usage, costs, or request count.
    Requires verified user access.
    """
    try:
        usage_service = UsageService()
        
        analytics = await usage_service.get_usage_analytics(
            db=db,
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Limit the top users list
        top_users = analytics["top_users"][:limit]
        
        return {
            "period": analytics["period"],
            "top_users": top_users,
            "total_users": len(analytics["top_users"])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get top users: {str(e)}"
        )


@router.get("/model-usage")
async def get_model_usage(
    organization_id: uuid.UUID,
    start_date: Optional[date] = Query(None, description="Start date for analysis (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for analysis (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get usage breakdown by AI model.
    
    Returns usage statistics and costs for each AI model used.
    """
    try:
        usage_service = UsageService()
        
        analytics = await usage_service.get_usage_analytics(
            db=db,
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "period": analytics["period"],
            "usage_by_model": analytics["usage_by_model"],
            "total_usage": analytics["total_usage"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model usage: {str(e)}"
        )


@router.get("/service-usage")
async def get_service_usage(
    organization_id: uuid.UUID,
    start_date: Optional[date] = Query(None, description="Start date for analysis (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for analysis (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get usage breakdown by service type.
    
    Returns usage statistics for different services (content generation, editing, analysis).
    """
    try:
        usage_service = UsageService()
        
        analytics = await usage_service.get_usage_analytics(
            db=db,
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "period": analytics["period"],
            "usage_by_service": analytics["usage_by_service"],
            "total_usage": analytics["total_usage"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service usage: {str(e)}"
        )


@router.get("/success-rates")
async def get_success_rates(
    organization_id: uuid.UUID,
    start_date: Optional[date] = Query(None, description="Start date for analysis (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for analysis (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get API success rates and error analysis.
    
    Returns success rates, error breakdown, and performance metrics.
    """
    try:
        usage_service = UsageService()
        
        analytics = await usage_service.get_usage_analytics(
            db=db,
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "period": analytics["period"],
            "success_rates": {
                "overall_success_rate": analytics["total_usage"]["success_rate"],
                "success_breakdown": analytics["success_breakdown"],
                "total_requests": analytics["total_usage"]["requests"]
            },
            "performance": {
                "avg_response_time_ms": analytics["total_usage"]["avg_response_time_ms"]
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get success rates: {str(e)}"
        )


@router.get("/export")
async def export_usage_data(
    organization_id: uuid.UUID,
    start_date: Optional[date] = Query(None, description="Start date for export (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for export (YYYY-MM-DD)"),
    format: str = Query("json", description="Export format (json, csv)"),
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Export usage data for external analysis.
    
    Returns usage data in JSON or CSV format for download.
    Requires verified user access.
    """
    try:
        usage_service = UsageService()
        
        # Set default date range if not provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        analytics = await usage_service.get_usage_analytics(
            db=db,
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Add export metadata
        export_data = {
            "export_info": {
                "organization_id": str(organization_id),
                "exported_by": current_user.username,
                "export_date": date.today().isoformat(),
                "format": format,
                "period": analytics["period"]
            },
            "data": analytics
        }
        
        if format.lower() == "csv":
            # This would convert to CSV format
            # For now, return JSON with CSV flag
            return {
                "message": "CSV export not yet implemented",
                "data": export_data,
                "format": "json"
            }
        
        return export_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export usage data: {str(e)}"
        )
