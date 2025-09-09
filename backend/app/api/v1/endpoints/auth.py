"""
Authentication endpoints for registration, login, password reset, and email verification.
"""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_active_user, get_current_verified_user
from app.core.config import settings
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.schemas.auth import (
    UserCreate, UserLogin, UserResponse, TokenResponse, TokenRefresh,
    PasswordReset, PasswordResetConfirm, EmailVerification, PasswordChange,
    MessageResponse, ErrorResponse
)
from app.models.user import User

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Register a new user account.
    
    Creates a new user account and their default organization.
    Sends an email verification link.
    """
    try:
        auth_service = AuthService(db)
        email_service = EmailService()
        
        # Create user and organization
        user, organization = await auth_service.create_user(user_data)
        
        # Generate email verification token
        verification_token = await auth_service.generate_email_verification_token(user)
        
        # Send verification email
        verification_url = f"{request.base_url}api/v1/auth/verify-email?token={verification_token}"
        email_service.send_verification_email(user.email, user.username, verification_url)
        
        return UserResponse.model_validate(user, from_attributes=True)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Authenticate user and return JWT tokens.
    
    Returns access token and refresh token for authenticated user.
    """
    try:
        auth_service = AuthService(db)
        
        # Authenticate user
        user = await auth_service.authenticate_user(
            user_credentials.email, 
            user_credentials.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create tokens
        tokens = await auth_service.create_tokens(user)
        
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Refresh access token using refresh token.
    
    Returns new access token and refresh token.
    """
    try:
        auth_service = AuthService(db)
        
        tokens = await auth_service.refresh_tokens(token_data.refresh_token)
        
        if not tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Logout current user.
    
    In a stateless JWT system, logout is handled client-side by removing tokens.
    This endpoint exists for consistency and future session management.
    """
    return MessageResponse(message="Successfully logged out")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    verification_data: EmailVerification,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Verify user email address using verification token.
    
    Marks user email as verified and activates the account.
    """
    try:
        auth_service = AuthService(db)
        email_service = EmailService()
        
        user = await auth_service.verify_email_token(verification_data.token)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        # Send welcome email
        email_service.send_welcome_email(user.email, user.username)
        
        return MessageResponse(message="Email verified successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification_email(
    current_user: User = Depends(get_current_active_user),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Resend email verification link.
    
    Generates a new verification token and sends verification email.
    """
    try:
        if current_user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already verified"
            )
        
        auth_service = AuthService(db)
        email_service = EmailService()
        
        # Generate new verification token
        verification_token = await auth_service.generate_email_verification_token(current_user)
        
        # Send verification email
        verification_url = f"{request.base_url}api/v1/auth/verify-email?token={verification_token}"
        email_service.send_verification_email(current_user.email, current_user.username, verification_url)
        
        return MessageResponse(message="Verification email sent")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend verification email"
        )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    password_reset_data: PasswordReset,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Request password reset.
    
    Sends password reset email to user if account exists.
    """
    try:
        auth_service = AuthService(db)
        email_service = EmailService()
        
        user = await auth_service.get_user_by_email(password_reset_data.email)
        
        if user and user.is_active:
            # Generate password reset token
            reset_token = await auth_service.generate_password_reset_token(user)
            
            # Send password reset email
            reset_url = f"{request.base_url}api/v1/auth/reset-password?token={reset_token}"
            email_service.send_password_reset_email(user.email, user.username, reset_url)
        
        # Always return success to prevent email enumeration
        return MessageResponse(message="If the email exists, a password reset link has been sent")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed"
        )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Reset password using reset token.
    
    Sets new password for user using valid reset token.
    """
    try:
        auth_service = AuthService(db)
        
        user = await auth_service.reset_password(reset_data.token, reset_data.new_password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        return MessageResponse(message="Password reset successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Change user password.
    
    Changes password for authenticated user after verifying current password.
    """
    try:
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
            detail="Password change failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get current user information.
    
    Returns profile information for authenticated user.
    """
    return UserResponse.model_validate(current_user, from_attributes=True)


@router.get("/verify-email")
async def verify_email_get(
    token: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Verify email address via GET request (for email links).
    
    Redirects to frontend with success/error status.
    """
    try:
        auth_service = AuthService(db)
        
        user = await auth_service.verify_email_token(token)
        
        if not user:
            # Redirect to frontend with error
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/auth/verify-email?status=error", status_code=302)
        
        # Redirect to frontend with success
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/auth/verify-email?status=success", status_code=302)
        
    except Exception as e:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/auth/verify-email?status=error", status_code=302)


@router.get("/reset-password")
async def reset_password_get(
    token: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Reset password page via GET request (for email links).
    
    Redirects to frontend password reset page with token.
    """
    try:
        auth_service = AuthService(db)
        
        # Verify token is valid (not expired)
        from sqlalchemy import select, and_
        from app.models.user import User
        from datetime import datetime
        
        result = await db.execute(
            select(User).where(
                and_(
                    User.password_reset_token == token,
                    User.password_reset_expires > datetime.utcnow()
                )
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Redirect to frontend with error
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/auth/reset-password?status=invalid", status_code=302)
        
        # Redirect to frontend with valid token
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/auth/reset-password?token={token}", status_code=302)
        
    except Exception as e:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/auth/reset-password?status=error", status_code=302)
