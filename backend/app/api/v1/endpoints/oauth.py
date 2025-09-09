"""
OAuth endpoints for Google and GitHub authentication.
"""

import secrets
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.core.oauth import oauth_service
from app.core.config import settings
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.schemas.auth import OAuthLogin, OAuthCallback, TokenResponse, MessageResponse
from app.models.user import User

router = APIRouter()


@router.get("/{provider}/login")
async def oauth_login(
    provider: str,
    request: Request,
    redirect_uri: str = None
) -> Any:
    """
    Initiate OAuth login flow.
    
    Redirects user to OAuth provider for authentication.
    """
    try:
        if not oauth_service.is_provider_configured(provider):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth provider '{provider}' not configured"
            )
        
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Store state in session for verification
        request.session["oauth_state"] = state
        
        # Append provider to redirect_uri to preserve context
        redirect_uri = redirect_uri or settings.OAUTH_REDIRECT_URI
        if "?" in redirect_uri:
            redirect_uri += f"&provider={provider}"
        else:
            redirect_uri += f"?provider={provider}"
        
        # Get authorization URL
        auth_url = await oauth_service.get_authorization_url(provider, redirect_uri, state, request)
        
        # Redirect to OAuth provider
        return RedirectResponse(url=auth_url)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth login failed"
        )


@router.get("/callback")
async def oauth_callback(
    provider: str,
    code: str,
    state: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Handle OAuth callback.
    
    Processes OAuth callback and creates/authenticates user.
    """
    try:
        if not oauth_service.is_provider_configured(provider):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth provider '{provider}' not configured"
            )
        
        # Verify state parameter for CSRF protection
        stored_state = request.session.get("oauth_state")
        if not stored_state or stored_state != state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state parameter"
            )
        
        # Clear state from session
        request.session.pop("oauth_state", None)
        
        auth_service = AuthService(db)
        email_service = EmailService()
        
        # Get access token
        token = await oauth_service.get_access_token(provider, code, str(request.url), request)
        
        # Get user info
        user_info = await oauth_service.get_user_info(provider, token)
        
        if not user_info.get('email'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not provided by OAuth provider"
            )
        
        # Check if user exists
        user = await auth_service.get_user_by_email(user_info['email'])
        
        if user:
            # Update OAuth info if needed
            if not user.oauth_provider:
                user.oauth_provider = provider
                user.oauth_id = user_info['id']
                user.avatar_url = user_info.get('avatar_url')
                user.is_verified = user_info.get('verified_email', True)
                await db.commit()
        else:
            # Create new user
            username = user_info['email'].split('@')[0]
            # Ensure username is unique
            original_username = username
            counter = 1
            while True:
                from sqlalchemy import select
                result = await db.execute(select(User.id).where(User.username == username))
                if not result.scalar_one_or_none():
                    break
                username = f"{original_username}{counter}"
                counter += 1
            
            user = User(
                email=user_info['email'],
                username=username,
                first_name=user_info.get('first_name'),
                last_name=user_info.get('last_name'),
                oauth_provider=provider,
                oauth_id=user_info['id'],
                avatar_url=user_info.get('avatar_url'),
                is_active=True,
                is_verified=user_info.get('verified_email', True)
            )
            
            db.add(user)
            await db.flush()  # Get user ID
            
            # Create default organization
            from app.models.organization import Organization
            from app.models.organization_member import OrganizationMember
            from app.schemas.auth import UserRole
            
            org_name = f"{user.username}'s Organization"
            org_slug = f"{username}-org-{secrets.token_hex(4)}"
            
            organization = Organization(
                name=org_name,
                slug=org_slug,
                owner_id=user.id,
                subscription_plan="free",
                subscription_status="active"
            )
            
            db.add(organization)
            await db.flush()  # Get organization ID
            
            # Add user as owner
            membership = OrganizationMember(
                user_id=user.id,
                organization_id=organization.id,
                role=UserRole.OWNER.value,
                is_active="active"
            )
            
            db.add(membership)
            await db.commit()
            
            # Send welcome email
            email_service.send_welcome_email(user.email, user.username)
        
        # Create tokens
        tokens = await auth_service.create_tokens(user)
        
        # Redirect to frontend with tokens
        # In production, you might want to use a more secure method
        frontend_url = f"{settings.FRONTEND_URL}/auth/oauth/callback"
        redirect_url = f"{frontend_url}?access_token={tokens.access_token}&refresh_token={tokens.refresh_token}&token_type={tokens.token_type}"
        
        return RedirectResponse(url=redirect_url)
        
    except HTTPException:
        raise
    except Exception as e:
        # Redirect to frontend with error
        frontend_url = f"{settings.FRONTEND_URL}/auth/oauth/callback?error=oauth_failed"
        return RedirectResponse(url=frontend_url)


@router.post("/{provider}/login", response_model=Dict[str, str])
async def oauth_login_post(
    provider: str,
    oauth_data: OAuthLogin,
    request: Request
) -> Any:
    """
    Initiate OAuth login flow via POST request.
    
    Returns authorization URL for frontend to redirect to.
    """
    try:
        if not oauth_service.is_provider_configured(provider):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth provider '{provider}' not configured"
            )
        
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Store state in session for verification
        request.session["oauth_state"] = state
        
        # Append provider to redirect_uri to preserve context
        redirect_uri = oauth_data.redirect_uri or settings.OAUTH_REDIRECT_URI
        if "?" in redirect_uri:
            redirect_uri += f"&provider={provider}"
        else:
            redirect_uri += f"?provider={provider}"
        
        # Get authorization URL
        auth_url = await oauth_service.get_authorization_url(provider, redirect_uri, state, request)
        
        return {
            "authorization_url": auth_url,
            "state": state
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth login failed"
        )


@router.post("/callback", response_model=TokenResponse)
async def oauth_callback_post(
    callback_data: OAuthCallback,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Handle OAuth callback via POST request.
    
    Processes OAuth callback and returns JWT tokens.
    """
    try:
        if not oauth_service.is_provider_configured(callback_data.provider):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth provider '{callback_data.provider}' not configured"
            )
        
        # Verify state parameter for CSRF protection
        stored_state = request.session.get("oauth_state")
        if not stored_state or stored_state != callback_data.state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state parameter"
            )
        
        # Clear state from session
        request.session.pop("oauth_state", None)
        
        auth_service = AuthService(db)
        email_service = EmailService()
        
        # Get access token
        token = await oauth_service.get_access_token(
            callback_data.provider, 
            callback_data.code, 
            str(request.url),
            request
        )
        
        # Get user info
        user_info = await oauth_service.get_user_info(callback_data.provider, token)
        
        if not user_info.get('email'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not provided by OAuth provider"
            )
        
        # Check if user exists
        user = await auth_service.get_user_by_email(user_info['email'])
        
        if user:
            # Update OAuth info if needed
            if not user.oauth_provider:
                user.oauth_provider = callback_data.provider
                user.oauth_id = user_info['id']
                user.avatar_url = user_info.get('avatar_url')
                user.is_verified = user_info.get('verified_email', True)
                await db.commit()
        else:
            # Create new user
            username = user_info['email'].split('@')[0]
            # Ensure username is unique
            original_username = username
            counter = 1
            while True:
                from sqlalchemy import select
                result = await db.execute(select(User.id).where(User.username == username))
                if not result.scalar_one_or_none():
                    break
                username = f"{original_username}{counter}"
                counter += 1
            
            user = User(
                email=user_info['email'],
                username=username,
                first_name=user_info.get('first_name'),
                last_name=user_info.get('last_name'),
                oauth_provider=callback_data.provider,
                oauth_id=user_info['id'],
                avatar_url=user_info.get('avatar_url'),
                is_active=True,
                is_verified=user_info.get('verified_email', True)
            )
            
            db.add(user)
            await db.flush()  # Get user ID
            
            # Create default organization
            from app.models.organization import Organization
            from app.models.organization_member import OrganizationMember
            from app.schemas.auth import UserRole
            
            org_name = f"{user.username}'s Organization"
            org_slug = f"{username}-org-{secrets.token_hex(4)}"
            
            organization = Organization(
                name=org_name,
                slug=org_slug,
                owner_id=user.id,
                subscription_plan="free",
                subscription_status="active"
            )
            
            db.add(organization)
            await db.flush()  # Get organization ID
            
            # Add user as owner
            membership = OrganizationMember(
                user_id=user.id,
                organization_id=organization.id,
                role=UserRole.OWNER.value,
                is_active="active"
            )
            
            db.add(membership)
            await db.commit()
            
            # Send welcome email
            email_service.send_welcome_email(user.email, user.username)
        
        # Create tokens
        tokens = await auth_service.create_tokens(user)
        
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth callback failed"
        )


@router.get("/providers", response_model=Dict[str, bool])
async def get_oauth_providers() -> Any:
    """
    Get list of configured OAuth providers.
    
    Returns which OAuth providers are available for authentication.
    """
    providers = oauth_service.get_configured_providers()
    return {provider: True for provider in providers}


@router.post("/link/{provider}", response_model=MessageResponse)
async def link_oauth_account(
    provider: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Link OAuth account to existing user.
    
    Initiates OAuth flow to link additional OAuth provider to current user.
    """
    try:
        if not oauth_service.is_provider_configured(provider):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth provider '{provider}' not configured"
            )
        
        # Check if user already has this OAuth provider linked
        if current_user.oauth_provider == provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth provider '{provider}' already linked"
            )
        
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Store state with user ID for later verification
        # In production, use Redis or database to store state
        redirect_uri = f"{settings.OAUTH_REDIRECT_URI}?link=true&user_id={current_user.id}"
        
        # Get authorization URL
        auth_url = await oauth_service.get_authorization_url(provider, redirect_uri, state, request)
        
        return RedirectResponse(url=auth_url, status_code=302)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth account linking failed"
        )


@router.delete("/unlink/{provider}", response_model=MessageResponse)
async def unlink_oauth_account(
    provider: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Unlink OAuth account from user.
    
    Removes OAuth provider link from current user account.
    """
    try:
        if current_user.oauth_provider != provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth provider '{provider}' not linked to this account"
            )
        
        # Check if user has password (can't unlink if no other auth method)
        if not current_user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot unlink OAuth account without setting a password first"
            )
        
        # Unlink OAuth provider
        current_user.oauth_provider = None
        current_user.oauth_id = None
        current_user.avatar_url = None
        await db.commit()
        
        return MessageResponse(message=f"OAuth provider '{provider}' unlinked successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth account unlinking failed"
        )
