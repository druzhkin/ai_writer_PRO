"""
Usage tracking utilities for token calculation, cost estimation, and analytics.
"""

import uuid
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from app.core.config import settings


class ServiceType(str, Enum):
    """Service type enumeration."""
    CONTENT_GENERATION = "content_generation"
    CONTENT_EDITING = "content_editing"
    STYLE_ANALYSIS = "style_analysis"
    FILE_PROCESSING = "file_processing"


class OperationType(str, Enum):
    """Operation type enumeration."""
    GENERATE = "generate"
    EDIT = "edit"
    ANALYZE = "analyze"
    PROCESS = "process"
    UPLOAD = "upload"


@dataclass
class TokenUsage:
    """Token usage data class."""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    model_used: str
    estimated_cost: float


@dataclass
class UsageLimits:
    """Usage limits data class."""
    daily_tokens: int
    daily_requests: int
    daily_cost: float
    monthly_tokens: int
    monthly_requests: int
    monthly_cost: float


def calculate_token_cost(
    model: str,
    input_tokens: int,
    output_tokens: int
) -> Tuple[float, float, float]:
    """
    Calculate cost for token usage based on model.
    
    Args:
        model: OpenAI model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        
    Returns:
        Tuple of (input_cost, output_cost, total_cost)
    """
    # Get pricing based on model
    if "gpt-4" in model.lower():
        if "turbo" in model.lower():
            input_cost_per_1k = settings.OPENAI_GPT4_TURBO_INPUT_COST_PER_1K
            output_cost_per_1k = settings.OPENAI_GPT4_TURBO_OUTPUT_COST_PER_1K
        else:
            input_cost_per_1k = settings.OPENAI_GPT4_INPUT_COST_PER_1K
            output_cost_per_1k = settings.OPENAI_GPT4_OUTPUT_COST_PER_1K
    else:
        # Default to GPT-4 pricing for unknown models
        input_cost_per_1k = settings.OPENAI_GPT4_INPUT_COST_PER_1K
        output_cost_per_1k = settings.OPENAI_GPT4_OUTPUT_COST_PER_1K
    
    input_cost = (input_tokens / 1000) * input_cost_per_1k
    output_cost = (output_tokens / 1000) * output_cost_per_1k
    total_cost = input_cost + output_cost
    
    return round(input_cost, 6), round(output_cost, 6), round(total_cost, 6)


def estimate_tokens_from_text(text: str) -> int:
    """
    Estimate token count from text (rough approximation).
    
    Args:
        text: Text to estimate tokens for
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    
    # Rough approximation: 1 token ≈ 4 characters for English text
    # This is a simplified estimation and may not be accurate for all cases
    return max(1, len(text) // 4)


def get_usage_limits_for_plan(subscription_plan: str) -> UsageLimits:
    """
    Get usage limits based on subscription plan.
    
    Args:
        subscription_plan: Subscription plan name
        
    Returns:
        UsageLimits object
    """
    plan_limits = {
        "free": settings.FREE_PLAN_DAILY_TOKENS,
        "basic": settings.BASIC_PLAN_DAILY_TOKENS,
        "pro": settings.PRO_PLAN_DAILY_TOKENS,
        "enterprise": settings.ENTERPRISE_PLAN_DAILY_TOKENS
    }
    
    daily_tokens = plan_limits.get(subscription_plan, plan_limits["free"])
    
    # Estimate other limits based on token limit
    daily_requests = daily_tokens // 1000  # Rough estimate
    daily_cost = daily_tokens * 0.03 / 1000  # Rough estimate
    
    # Monthly limits (assuming 30 days)
    monthly_tokens = daily_tokens * 30
    monthly_requests = daily_requests * 30
    monthly_cost = daily_cost * 30
    
    return UsageLimits(
        daily_tokens=daily_tokens,
        daily_requests=daily_requests,
        daily_cost=daily_cost,
        monthly_tokens=monthly_tokens,
        monthly_requests=monthly_requests,
        monthly_cost=monthly_cost
    )


def calculate_usage_percentage(current_usage: int, limit: int) -> float:
    """
    Calculate usage percentage.
    
    Args:
        current_usage: Current usage amount
        limit: Usage limit
        
    Returns:
        Usage percentage (0-100)
    """
    if limit <= 0:
        return 0.0
    
    percentage = (current_usage / limit) * 100
    return min(100.0, max(0.0, percentage))


def get_usage_warnings(usage_percentage: float) -> List[str]:
    """
    Get usage warnings based on percentage.
    
    Args:
        usage_percentage: Current usage percentage
        
    Returns:
        List of warning messages
    """
    warnings = []
    
    if usage_percentage >= 100:
        warnings.append("Usage limit exceeded")
    elif usage_percentage >= 90:
        warnings.append("Usage limit nearly exceeded (90%+)")
    elif usage_percentage >= 75:
        warnings.append("High usage level (75%+)")
    elif usage_percentage >= 50:
        warnings.append("Moderate usage level (50%+)")
    
    return warnings


def format_usage_cost(cost: float) -> str:
    """
    Format usage cost for display.
    
    Args:
        cost: Cost amount in USD
        
    Returns:
        Formatted cost string
    """
    if cost < 0.01:
        return f"${cost:.6f}"
    elif cost < 1.0:
        return f"${cost:.4f}"
    else:
        return f"${cost:.2f}"


def format_token_count(tokens: int) -> str:
    """
    Format token count for display.
    
    Args:
        tokens: Token count
        
    Returns:
        Formatted token string
    """
    if tokens < 1000:
        return str(tokens)
    elif tokens < 1000000:
        return f"{tokens/1000:.1f}K"
    else:
        return f"{tokens/1000000:.1f}M"


def calculate_usage_efficiency(
    input_tokens: int,
    output_tokens: int,
    success: bool
) -> Dict[str, Any]:
    """
    Calculate usage efficiency metrics.
    
    Args:
        input_tokens: Input tokens used
        output_tokens: Output tokens generated
        success: Whether the operation was successful
        
    Returns:
        Dictionary with efficiency metrics
    """
    total_tokens = input_tokens + output_tokens
    
    # Calculate efficiency ratios
    input_ratio = input_tokens / total_tokens if total_tokens > 0 else 0
    output_ratio = output_tokens / total_tokens if total_tokens > 0 else 0
    
    # Calculate tokens per dollar (rough estimate)
    estimated_cost = calculate_token_cost("gpt-4-turbo-preview", input_tokens, output_tokens)[2]
    tokens_per_dollar = total_tokens / estimated_cost if estimated_cost > 0 else 0
    
    return {
        "total_tokens": total_tokens,
        "input_ratio": round(input_ratio, 3),
        "output_ratio": round(output_ratio, 3),
        "tokens_per_dollar": round(tokens_per_dollar, 2),
        "success": success,
        "efficiency_score": 1.0 if success else 0.0
    }


def generate_usage_report(
    usage_data: List[Dict[str, Any]],
    start_date: date,
    end_date: date
) -> Dict[str, Any]:
    """
    Generate comprehensive usage report.
    
    Args:
        usage_data: List of usage records
        start_date: Report start date
        end_date: Report end date
        
    Returns:
        Dictionary with usage report
    """
    if not usage_data:
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days + 1
            },
            "total_usage": {
                "requests": 0,
                "tokens": 0,
                "cost": 0.0
            },
            "summary": "No usage data available"
        }
    
    # Calculate totals
    total_requests = len(usage_data)
    total_input_tokens = sum(record.get("input_tokens", 0) for record in usage_data)
    total_output_tokens = sum(record.get("output_tokens", 0) for record in usage_data)
    total_tokens = total_input_tokens + total_output_tokens
    total_cost = sum(record.get("total_cost", 0) for record in usage_data)
    
    # Calculate averages
    avg_tokens_per_request = total_tokens / total_requests if total_requests > 0 else 0
    avg_cost_per_request = total_cost / total_requests if total_requests > 0 else 0
    
    # Calculate success rate
    successful_requests = sum(1 for record in usage_data if record.get("success") == "true")
    success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
    
    # Group by service type
    service_usage = {}
    for record in usage_data:
        service_type = record.get("service_type", "unknown")
        if service_type not in service_usage:
            service_usage[service_type] = {
                "requests": 0,
                "tokens": 0,
                "cost": 0.0
            }
        service_usage[service_type]["requests"] += 1
        service_usage[service_type]["tokens"] += record.get("total_tokens", 0)
        service_usage[service_type]["cost"] += record.get("total_cost", 0)
    
    # Group by model
    model_usage = {}
    for record in usage_data:
        model = record.get("model_used", "unknown")
        if model not in model_usage:
            model_usage[model] = {
                "requests": 0,
                "tokens": 0,
                "cost": 0.0
            }
        model_usage[model]["requests"] += 1
        model_usage[model]["tokens"] += record.get("total_tokens", 0)
        model_usage[model]["cost"] += record.get("total_cost", 0)
    
    return {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": (end_date - start_date).days + 1
        },
        "total_usage": {
            "requests": total_requests,
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 6),
            "avg_tokens_per_request": round(avg_tokens_per_request, 2),
            "avg_cost_per_request": round(avg_cost_per_request, 6),
            "success_rate": round(success_rate, 2)
        },
        "usage_by_service": service_usage,
        "usage_by_model": model_usage,
        "summary": f"Generated {total_requests} requests using {format_token_count(total_tokens)} tokens for {format_usage_cost(total_cost)}"
    }


def validate_usage_data(usage_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate usage data structure.
    
    Args:
        usage_data: Usage data to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = [
        "organization_id", "service_type", "operation_type",
        "input_tokens", "output_tokens", "total_tokens", "model_used"
    ]
    
    for field in required_fields:
        if field not in usage_data:
            return False, f"Missing required field: {field}"
    
    # Validate token counts
    if usage_data["input_tokens"] < 0:
        return False, "Input tokens cannot be negative"
    
    if usage_data["output_tokens"] < 0:
        return False, "Output tokens cannot be negative"
    
    if usage_data["total_tokens"] != usage_data["input_tokens"] + usage_data["output_tokens"]:
        return False, "Total tokens must equal input + output tokens"
    
    # Validate service type
    valid_service_types = [service.value for service in ServiceType]
    if usage_data["service_type"] not in valid_service_types:
        return False, f"Invalid service type: {usage_data['service_type']}"
    
    # Validate operation type
    valid_operation_types = [operation.value for operation in OperationType]
    if usage_data["operation_type"] not in valid_operation_types:
        return False, f"Invalid operation type: {usage_data['operation_type']}"
    
    return True, None


def calculate_usage_trends(
    daily_usage: List[Dict[str, Any]],
    days: int = 30
) -> Dict[str, Any]:
    """
    Calculate usage trends from daily usage data.
    
    Args:
        daily_usage: List of daily usage records
        days: Number of days to analyze
        
    Returns:
        Dictionary with trend analysis
    """
    if not daily_usage or len(daily_usage) < 2:
        return {
            "trend": "insufficient_data",
            "change_percentage": 0.0,
            "summary": "Insufficient data for trend analysis"
        }
    
    # Sort by date
    sorted_usage = sorted(daily_usage, key=lambda x: x.get("date", ""))
    
    # Calculate trend
    first_half = sorted_usage[:len(sorted_usage)//2]
    second_half = sorted_usage[len(sorted_usage)//2:]
    
    first_half_avg = sum(day.get("tokens", 0) for day in first_half) / len(first_half)
    second_half_avg = sum(day.get("tokens", 0) for day in second_half) / len(second_half)
    
    if first_half_avg == 0:
        change_percentage = 100.0 if second_half_avg > 0 else 0.0
    else:
        change_percentage = ((second_half_avg - first_half_avg) / first_half_avg) * 100
    
    # Determine trend direction
    if change_percentage > 10:
        trend = "increasing"
    elif change_percentage < -10:
        trend = "decreasing"
    else:
        trend = "stable"
    
    return {
        "trend": trend,
        "change_percentage": round(change_percentage, 2),
        "first_half_avg": round(first_half_avg, 2),
        "second_half_avg": round(second_half_avg, 2),
        "summary": f"Usage trend is {trend} with {abs(change_percentage):.1f}% change"
    }


def estimate_monthly_cost(
    daily_usage: List[Dict[str, Any]],
    days_in_month: int = 30
) -> Dict[str, Any]:
    """
    Estimate monthly cost based on daily usage patterns.
    
    Args:
        daily_usage: List of daily usage records
        days_in_month: Number of days in the month
        
    Returns:
        Dictionary with cost estimates
    """
    if not daily_usage:
        return {
            "estimated_monthly_cost": 0.0,
            "estimated_monthly_tokens": 0,
            "confidence": "low",
            "summary": "No usage data available for estimation"
        }
    
    # Calculate average daily usage
    total_daily_cost = sum(day.get("cost", 0) for day in daily_usage)
    total_daily_tokens = sum(day.get("tokens", 0) for day in daily_usage)
    
    avg_daily_cost = total_daily_cost / len(daily_usage)
    avg_daily_tokens = total_daily_tokens / len(daily_usage)
    
    # Estimate monthly usage
    estimated_monthly_cost = avg_daily_cost * days_in_month
    estimated_monthly_tokens = avg_daily_tokens * days_in_month
    
    # Calculate confidence based on data consistency
    cost_variance = sum((day.get("cost", 0) - avg_daily_cost) ** 2 for day in daily_usage) / len(daily_usage)
    cost_std_dev = cost_variance ** 0.5
    coefficient_of_variation = cost_std_dev / avg_daily_cost if avg_daily_cost > 0 else 0
    
    if coefficient_of_variation < 0.2:
        confidence = "high"
    elif coefficient_of_variation < 0.5:
        confidence = "medium"
    else:
        confidence = "low"
    
    return {
        "estimated_monthly_cost": round(estimated_monthly_cost, 2),
        "estimated_monthly_tokens": int(estimated_monthly_tokens),
        "confidence": confidence,
        "avg_daily_cost": round(avg_daily_cost, 4),
        "avg_daily_tokens": round(avg_daily_tokens, 2),
        "coefficient_of_variation": round(coefficient_of_variation, 3),
        "summary": f"Estimated monthly cost: {format_usage_cost(estimated_monthly_cost)} ({confidence} confidence)"
    }
