"""
Tests for usage tracking and analytics functionality.
"""

import pytest
import uuid
from datetime import datetime, date, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_usage import APIUsage
from app.models.organization import Organization
from app.models.user import User
from app.services.usage_service import UsageService
from app.utils.usage_utils import (
    calculate_token_cost, estimate_tokens_from_text, get_usage_limits_for_plan,
    calculate_usage_percentage, get_usage_warnings, format_usage_cost,
    format_token_count, calculate_usage_efficiency, generate_usage_report,
    validate_usage_data, calculate_usage_trends, estimate_monthly_cost,
    ServiceType, OperationType, TokenUsage, UsageLimits
)


class TestUsageService:
    """Test cases for UsageService."""
    
    @pytest.fixture
    async def usage_service(self):
        """Create UsageService instance."""
        return UsageService()
    
    @pytest.fixture
    async def sample_organization(self, db_session: AsyncSession):
        """Create sample organization."""
        org = Organization(
            name="Test Organization",
            slug="test-org",
            owner_id=uuid.uuid4(),
            subscription_plan="pro"
        )
        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)
        return org
    
    @pytest.fixture
    async def sample_user(self, db_session: AsyncSession):
        """Create sample user."""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            is_active=True,
            is_verified=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user
    
    @pytest.fixture
    async def sample_usage_records(self, db_session: AsyncSession, sample_organization: Organization, sample_user: User):
        """Create sample usage records."""
        usage_records = []
        
        # Create usage records for the last 7 days
        for i in range(7):
            usage_date = date.today() - timedelta(days=i)
            
            usage = APIUsage(
                organization_id=sample_organization.id,
                user_id=sample_user.id,
                service_type="content_generation",
                operation_type="generate",
                input_tokens=1000,
                output_tokens=500,
                total_tokens=1500,
                input_cost=0.01,
                output_cost=0.015,
                total_cost=0.025,
                model_used="gpt-4-turbo-preview",
                input_cost_per_1k=0.01,
                output_cost_per_1k=0.03,
                success="true",
                usage_date=usage_date,
                usage_hour=10
            )
            db_session.add(usage)
            usage_records.append(usage)
        
        await db_session.commit()
        return usage_records
    
    @pytest.mark.asyncio
    async def test_track_usage_success(
        self,
        usage_service: UsageService,
        db_session: AsyncSession,
        sample_organization: Organization,
        sample_user: User
    ):
        """Test successful usage tracking."""
        usage = await usage_service.track_usage(
            db=db_session,
            organization_id=sample_organization.id,
            user_id=sample_user.id,
            service_type="content_generation",
            operation_type="generate",
            model_used="gpt-4-turbo-preview",
            input_tokens=1000,
            output_tokens=500,
            total_tokens=1500,
            estimated_cost=0.025
        )
        
        assert usage is not None
        assert usage.organization_id == sample_organization.id
        assert usage.user_id == sample_user.id
        assert usage.service_type == "content_generation"
        assert usage.total_tokens == 1500
        assert usage.total_cost == 0.025
    
    @pytest.mark.asyncio
    async def test_get_usage_analytics(
        self,
        usage_service: UsageService,
        db_session: AsyncSession,
        sample_organization: Organization,
        sample_usage_records: list
    ):
        """Test usage analytics retrieval."""
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        analytics = await usage_service.get_usage_analytics(
            db=db_session,
            organization_id=sample_organization.id,
            start_date=start_date,
            end_date=end_date
        )
        
        assert analytics is not None
        assert "total_usage" in analytics
        assert "usage_by_service" in analytics
        assert "usage_by_model" in analytics
        assert "daily_usage" in analytics
        
        total_usage = analytics["total_usage"]
        assert total_usage["requests"] >= 7
        assert total_usage["total_tokens"] >= 10500  # 7 * 1500
        assert total_usage["total_cost"] >= 0.175  # 7 * 0.025
    
    @pytest.mark.asyncio
    async def test_get_usage_limits(
        self,
        usage_service: UsageService,
        db_session: AsyncSession,
        sample_organization: Organization,
        sample_usage_records: list
    ):
        """Test usage limits retrieval."""
        limits = await usage_service.get_usage_limits(
            db=db_session,
            organization_id=sample_organization.id
        )
        
        assert limits is not None
        assert "subscription_plan" in limits
        assert "daily_limits" in limits
        assert "current_usage" in limits
        assert "status" in limits
        
        assert limits["subscription_plan"] == "pro"
        assert limits["daily_limits"]["tokens"] > 0
        assert limits["current_usage"]["daily"]["tokens"] >= 1500
    
    @pytest.mark.asyncio
    async def test_get_cost_breakdown(
        self,
        usage_service: UsageService,
        db_session: AsyncSession,
        sample_organization: Organization,
        sample_usage_records: list
    ):
        """Test cost breakdown retrieval."""
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        breakdown = await usage_service.get_cost_breakdown(
            db=db_session,
            organization_id=sample_organization.id,
            start_date=start_date,
            end_date=end_date
        )
        
        assert breakdown is not None
        assert "period" in breakdown
        assert "total_costs" in breakdown
        assert "cost_by_model" in breakdown
        
        total_costs = breakdown["total_costs"]
        assert total_costs["total_cost"] >= 0.175
        assert total_costs["total_requests"] >= 7


class TestUsageUtils:
    """Test cases for usage utility functions."""
    
    def test_calculate_token_cost(self):
        """Test token cost calculation."""
        input_cost, output_cost, total_cost = calculate_token_cost(
            "gpt-4-turbo-preview", 1000, 500
        )
        
        assert input_cost > 0
        assert output_cost > 0
        assert total_cost == input_cost + output_cost
    
    def test_estimate_tokens_from_text(self):
        """Test token estimation from text."""
        text = "This is a test text for token estimation."
        tokens = estimate_tokens_from_text(text)
        
        assert tokens > 0
        assert tokens <= len(text)  # Should be less than character count
    
    def test_get_usage_limits_for_plan(self):
        """Test usage limits for different plans."""
        # Test free plan
        free_limits = get_usage_limits_for_plan("free")
        assert free_limits.daily_tokens > 0
        assert free_limits.daily_requests > 0
        
        # Test pro plan
        pro_limits = get_usage_limits_for_plan("pro")
        assert pro_limits.daily_tokens > free_limits.daily_tokens
        assert pro_limits.daily_requests > free_limits.daily_requests
        
        # Test unknown plan (should default to free)
        unknown_limits = get_usage_limits_for_plan("unknown")
        assert unknown_limits.daily_tokens == free_limits.daily_tokens
    
    def test_calculate_usage_percentage(self):
        """Test usage percentage calculation."""
        # Normal usage
        percentage = calculate_usage_percentage(500, 1000)
        assert percentage == 50.0
        
        # Over limit
        percentage = calculate_usage_percentage(1200, 1000)
        assert percentage == 100.0
        
        # Zero limit
        percentage = calculate_usage_percentage(100, 0)
        assert percentage == 0.0
    
    def test_get_usage_warnings(self):
        """Test usage warnings generation."""
        # No warnings
        warnings = get_usage_warnings(30.0)
        assert len(warnings) == 0
        
        # Moderate usage
        warnings = get_usage_warnings(60.0)
        assert len(warnings) == 1
        assert "50%" in warnings[0]
        
        # High usage
        warnings = get_usage_warnings(80.0)
        assert len(warnings) == 1
        assert "75%" in warnings[0]
        
        # Critical usage
        warnings = get_usage_warnings(95.0)
        assert len(warnings) == 1
        assert "90%" in warnings[0]
        
        # Over limit
        warnings = get_usage_warnings(105.0)
        assert len(warnings) == 1
        assert "exceeded" in warnings[0]
    
    def test_format_usage_cost(self):
        """Test usage cost formatting."""
        # Small cost
        formatted = format_usage_cost(0.001)
        assert "$0.001000" in formatted
        
        # Medium cost
        formatted = format_usage_cost(0.5)
        assert "$0.5000" in formatted
        
        # Large cost
        formatted = format_usage_cost(10.50)
        assert "$10.50" in formatted
    
    def test_format_token_count(self):
        """Test token count formatting."""
        # Small count
        formatted = format_token_count(500)
        assert "500" in formatted
        
        # Medium count
        formatted = format_token_count(1500)
        assert "1.5K" in formatted
        
        # Large count
        formatted = format_token_count(1500000)
        assert "1.5M" in formatted
    
    def test_calculate_usage_efficiency(self):
        """Test usage efficiency calculation."""
        efficiency = calculate_usage_efficiency(1000, 500, True)
        
        assert efficiency["total_tokens"] == 1500
        assert efficiency["input_ratio"] == 1000/1500
        assert efficiency["output_ratio"] == 500/1500
        assert efficiency["success"] is True
        assert efficiency["efficiency_score"] == 1.0
        
        # Failed operation
        efficiency = calculate_usage_efficiency(1000, 500, False)
        assert efficiency["efficiency_score"] == 0.0
    
    def test_generate_usage_report(self):
        """Test usage report generation."""
        usage_data = [
            {
                "input_tokens": 1000,
                "output_tokens": 500,
                "total_tokens": 1500,
                "total_cost": 0.025,
                "service_type": "content_generation",
                "model_used": "gpt-4-turbo-preview",
                "success": "true"
            },
            {
                "input_tokens": 800,
                "output_tokens": 400,
                "total_tokens": 1200,
                "total_cost": 0.020,
                "service_type": "content_editing",
                "model_used": "gpt-4-turbo-preview",
                "success": "true"
            }
        ]
        
        start_date = date.today() - timedelta(days=1)
        end_date = date.today()
        
        report = generate_usage_report(usage_data, start_date, end_date)
        
        assert report["total_usage"]["requests"] == 2
        assert report["total_usage"]["total_tokens"] == 2700
        assert report["total_usage"]["total_cost"] == 0.045
        assert report["total_usage"]["success_rate"] == 100.0
        assert "content_generation" in report["usage_by_service"]
        assert "content_editing" in report["usage_by_service"]
    
    def test_validate_usage_data(self):
        """Test usage data validation."""
        # Valid data
        valid_data = {
            "organization_id": str(uuid.uuid4()),
            "service_type": "content_generation",
            "operation_type": "generate",
            "input_tokens": 1000,
            "output_tokens": 500,
            "total_tokens": 1500,
            "model_used": "gpt-4-turbo-preview"
        }
        
        is_valid, error = validate_usage_data(valid_data)
        assert is_valid is True
        assert error is None
        
        # Missing required field
        invalid_data = valid_data.copy()
        del invalid_data["service_type"]
        
        is_valid, error = validate_usage_data(invalid_data)
        assert is_valid is False
        assert "service_type" in error
        
        # Invalid token counts
        invalid_data = valid_data.copy()
        invalid_data["input_tokens"] = -100
        
        is_valid, error = validate_usage_data(invalid_data)
        assert is_valid is False
        assert "negative" in error
        
        # Mismatched total tokens
        invalid_data = valid_data.copy()
        invalid_data["total_tokens"] = 1000  # Should be 1500
        
        is_valid, error = validate_usage_data(invalid_data)
        assert is_valid is False
        assert "must equal" in error
    
    def test_calculate_usage_trends(self):
        """Test usage trend calculation."""
        # Increasing trend
        daily_usage = [
            {"date": "2024-01-01", "tokens": 1000},
            {"date": "2024-01-02", "tokens": 1200},
            {"date": "2024-01-03", "tokens": 1400},
            {"date": "2024-01-04", "tokens": 1600}
        ]
        
        trends = calculate_usage_trends(daily_usage)
        assert trends["trend"] == "increasing"
        assert trends["change_percentage"] > 0
        
        # Decreasing trend
        daily_usage = [
            {"date": "2024-01-01", "tokens": 1600},
            {"date": "2024-01-02", "tokens": 1400},
            {"date": "2024-01-03", "tokens": 1200},
            {"date": "2024-01-04", "tokens": 1000}
        ]
        
        trends = calculate_usage_trends(daily_usage)
        assert trends["trend"] == "decreasing"
        assert trends["change_percentage"] < 0
        
        # Stable trend
        daily_usage = [
            {"date": "2024-01-01", "tokens": 1000},
            {"date": "2024-01-02", "tokens": 1050},
            {"date": "2024-01-03", "tokens": 950},
            {"date": "2024-01-04", "tokens": 1000}
        ]
        
        trends = calculate_usage_trends(daily_usage)
        assert trends["trend"] == "stable"
        assert abs(trends["change_percentage"]) < 10
    
    def test_estimate_monthly_cost(self):
        """Test monthly cost estimation."""
        daily_usage = [
            {"cost": 0.025, "tokens": 1500},
            {"cost": 0.030, "tokens": 1800},
            {"cost": 0.020, "tokens": 1200},
            {"cost": 0.035, "tokens": 2100},
            {"cost": 0.028, "tokens": 1680}
        ]
        
        estimate = estimate_monthly_cost(daily_usage, days_in_month=30)
        
        assert estimate["estimated_monthly_cost"] > 0
        assert estimate["estimated_monthly_tokens"] > 0
        assert estimate["confidence"] in ["low", "medium", "high"]
        assert "summary" in estimate
        
        # No data
        estimate = estimate_monthly_cost([])
        assert estimate["estimated_monthly_cost"] == 0.0
        assert estimate["confidence"] == "low"


class TestUsageEnums:
    """Test cases for usage enums and data classes."""
    
    def test_service_type_enum(self):
        """Test ServiceType enum."""
        assert ServiceType.CONTENT_GENERATION == "content_generation"
        assert ServiceType.CONTENT_EDITING == "content_editing"
        assert ServiceType.STYLE_ANALYSIS == "style_analysis"
        assert ServiceType.FILE_PROCESSING == "file_processing"
    
    def test_operation_type_enum(self):
        """Test OperationType enum."""
        assert OperationType.GENERATE == "generate"
        assert OperationType.EDIT == "edit"
        assert OperationType.ANALYZE == "analyze"
        assert OperationType.PROCESS == "process"
        assert OperationType.UPLOAD == "upload"
    
    def test_token_usage_dataclass(self):
        """Test TokenUsage dataclass."""
        usage = TokenUsage(
            input_tokens=1000,
            output_tokens=500,
            total_tokens=1500,
            model_used="gpt-4-turbo-preview",
            estimated_cost=0.025
        )
        
        assert usage.input_tokens == 1000
        assert usage.output_tokens == 500
        assert usage.total_tokens == 1500
        assert usage.model_used == "gpt-4-turbo-preview"
        assert usage.estimated_cost == 0.025
    
    def test_usage_limits_dataclass(self):
        """Test UsageLimits dataclass."""
        limits = UsageLimits(
            daily_tokens=100000,
            daily_requests=100,
            daily_cost=3.0,
            monthly_tokens=3000000,
            monthly_requests=3000,
            monthly_cost=90.0
        )
        
        assert limits.daily_tokens == 100000
        assert limits.daily_requests == 100
        assert limits.daily_cost == 3.0
        assert limits.monthly_tokens == 3000000
        assert limits.monthly_requests == 3000
        assert limits.monthly_cost == 90.0
