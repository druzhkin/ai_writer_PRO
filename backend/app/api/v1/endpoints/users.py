"""
User management endpoints for profile management and user operations.
"""

import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_active_user, get_current_verified_user, get_current_superuser
from app.services.user_service import UserService
from app.schemas.auth import UserUpdate, PasswordChange
from app.schemas.user import (
    UserProfileResponse, UserStatsResponse, UserPreferences, UserPreferencesUpdate,
    UserSearchResponse, UserSearchParams, BulkUserAction, MessageResponse
)
from app.models.user import User

router = APIRouter()


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get current user's profile with organization information.
    
    Returns detailed profile information including organization memberships.
    """
    try:
        user_service = UserService(db)
        user_profile = await user_service.get_user_profile(current_user.id)
        
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        return UserProfileResponse.model_validate(user_profile, from_attributes=True)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )


@router.put("/me", response_model=UserProfileResponse)
async def update_my_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update current user's profile.
    
    Updates user profile information including username, name, and avatar.
    """
    try:
        user_service = UserService(db)
        updated_user = await user_service.update_user_profile(current_user, update_data)
        
        return UserProfileResponse.model_validate(updated_user, from_attributes=True)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )


@router.post("/me/change-password", response_model=MessageResponse)
async def change_my_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Change current user's password.
    
    Changes password after verifying current password.
    """
    try:
        from app.services.auth_service import AuthService
        auth_service = AuthService(db)
        
        success = await auth_service.change_password(
            current_user,
            password_data.current_password,
            password_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        return MessageResponse(message="Password changed successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.get("/me/stats", response_model=UserStatsResponse)
async def get_my_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get current user's statistics.
    
    Returns user statistics including organization counts and activity.
    """
    try:
        user_service = UserService(db)
        organizations = await user_service.get_user_organizations(current_user)
        
        owned_count = sum(1 for org in organizations if org.owner_id == current_user.id)
        
        return UserStatsResponse(
            total_organizations=len(organizations),
            owned_organizations=owned_count,
            member_organizations=len(organizations) - owned_count,
            total_articles=0,  # Placeholder for future implementation
            total_styles=0     # Placeholder for future implementation
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user statistics"
        )


@router.get("/me/preferences", response_model=UserPreferences)
async def get_my_preferences(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get current user's preferences.
    
    Returns user preferences and settings.
    """
    # For now, return default preferences
    # In the future, this would be stored in the database
    return UserPreferences()


@router.put("/me/preferences", response_model=UserPreferences)
async def update_my_preferences(
    preferences_data: UserPreferencesUpdate,
    current_user: User = Depends(get_current_verified_user)
) -> Any:
    """
    Update current user's preferences.
    
    Updates user preferences and settings.
    """
    # For now, return the updated preferences
    # In the future, this would be stored in the database
    current_prefs = UserPreferences()
    updated_prefs = current_prefs.copy(update=preferences_data.dict(exclude_unset=True))
    return updated_prefs


@router.delete("/me", response_model=MessageResponse)
async def delete_my_account(
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete current user's account.
    
    Deactivates the user account (soft delete).
    """
    try:
        user_service = UserService(db)
        success = await user_service.deactivate_user(current_user)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete account"
            )
        
        return MessageResponse(message="Account deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )


# Admin endpoints
@router.get("/", response_model=UserSearchResponse)
async def search_users(
    search_params: UserSearchParams = Depends(),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Search users (Admin only).
    
    Search and filter users with pagination.
    """
    try:
        user_service = UserService(db)
        result = await user_service.search_users(search_params)
        
        return UserSearchResponse(
            users=result["users"],
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"],
            has_next=result["has_next"],
            has_prev=result["has_prev"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search users"
        )


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_by_id(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get user by ID (Admin only).
    
    Returns detailed profile information for any user.
    """
    try:
        user_service = UserService(db)
        user_profile = await user_service.get_user_profile(user_id)
        
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserProfileResponse.model_validate(user_profile, from_attributes=True)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )


@router.put("/{user_id}", response_model=UserProfileResponse)
async def update_user_by_id(
    user_id: uuid.UUID,
    update_data: UserUpdate,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update user by ID (Admin only).
    
    Updates any user's profile information.
    """
    try:
        user_service = UserService(db)
        user = await user_service.get_user_profile(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        updated_user = await user_service.update_user_profile(user, update_data)
        
        return UserProfileResponse.model_validate(updated_user, from_attributes=True)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user_by_id(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete user by ID (Admin only).
    
    Deactivates any user account.
    """
    try:
        user_service = UserService(db)
        user = await user_service.get_user_profile(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        success = await user_service.deactivate_user(user)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user"
            )
        
        return MessageResponse(message="User deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )


@router.post("/bulk-action", response_model=MessageResponse)
async def bulk_user_action(
    action_data: BulkUserAction,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Perform bulk action on users (Admin only).
    
    Performs bulk operations on multiple users.
    """
    try:
        user_service = UserService(db)
        
        # Get users
        users = []
        for user_id in action_data.user_ids:
            user = await user_service.get_user_profile(user_id)
            if user:
                users.append(user)
        
        if not users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No valid users found"
            )
        
        # Perform action
        success_count = 0
        for user in users:
            if action_data.action == "activate":
                user.is_active = True
                success_count += 1
            elif action_data.action == "deactivate":
                user.is_active = False
                success_count += 1
            elif action_data.action == "delete":
                if await user_service.deactivate_user(user):
                    success_count += 1
        
        await db.commit()
        
        return MessageResponse(
            message=f"Bulk action '{action_data.action}' completed on {success_count} users"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk action"
        )
