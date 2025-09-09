"""
OAuth configuration and client setup for Google and GitHub integration.
"""

from typing import Optional, Dict, Any
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.starlette_client import OAuthError
from starlette.config import Config
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# Initialize OAuth
oauth = OAuth()

# Configure OAuth providers
if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
    oauth.register(
        name='google',
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    logger.info("Google OAuth provider configured")

if settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET:
    oauth.register(
        name='github',
        client_id=settings.GITHUB_CLIENT_ID,
        client_secret=settings.GITHUB_CLIENT_SECRET,
        access_token_url='https://github.com/login/oauth/access_token',
        authorize_url='https://github.com/login/oauth/authorize',
        api_base_url='https://api.github.com/',
        client_kwargs={
            'scope': 'user:email'
        }
    )
    logger.info("GitHub OAuth provider configured")


class OAuthService:
    """OAuth service for handling OAuth flows."""
    
    def __init__(self):
        self.oauth = oauth
    
    async def get_authorization_url(self, provider: str, redirect_uri: str, state: str, request) -> str:
        """Get OAuth authorization URL."""
        try:
            client = self.oauth.create_client(provider)
            if not client:
                raise ValueError(f"OAuth provider '{provider}' not configured")
            
            authorization_url = await client.authorize_redirect(request, redirect_uri, state=state)
            return str(authorization_url)
            
        except Exception as e:
            logger.error("Error getting OAuth authorization URL", error=str(e), provider=provider)
            raise
    
    async def get_access_token(self, provider: str, authorization_code: str, redirect_uri: str, request) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        try:
            client = self.oauth.create_client(provider)
            if not client:
                raise ValueError(f"OAuth provider '{provider}' not configured")
            
            token = await client.authorize_access_token(request)
            return token
            
        except OAuthError as e:
            logger.error("OAuth error getting access token", error=str(e), provider=provider)
            raise ValueError(f"OAuth authorization failed: {str(e)}")
        except Exception as e:
            logger.error("Error getting OAuth access token", error=str(e), provider=provider)
            raise
    
    async def get_user_info(self, provider: str, token: Dict[str, Any]) -> Dict[str, Any]:
        """Get user information from OAuth provider."""
        try:
            client = self.oauth.create_client(provider)
            if not client:
                raise ValueError(f"OAuth provider '{provider}' not configured")
            
            # Set the token
            client.token = token
            
            # Get user info based on provider
            if provider == 'google':
                user_info = await client.get('https://www.googleapis.com/oauth2/v2/userinfo')
                user_data = user_info.json()
                
                return {
                    'id': user_data.get('id'),
                    'email': user_data.get('email'),
                    'name': user_data.get('name'),
                    'first_name': user_data.get('given_name'),
                    'last_name': user_data.get('family_name'),
                    'avatar_url': user_data.get('picture'),
                    'verified_email': user_data.get('verified_email', False)
                }
            
            elif provider == 'github':
                user_info = await client.get('user')
                user_data = user_info.json()
                
                # Get email from GitHub (might be private)
                email_data = await client.get('user/emails')
                emails = email_data.json()
                primary_email = None
                verified_email = None
                
                for email in emails:
                    if email.get('primary'):
                        primary_email = email.get('email')
                    if email.get('verified') and not primary_email:
                        verified_email = email.get('email')
                
                email = primary_email or verified_email or user_data.get('email')
                
                return {
                    'id': str(user_data.get('id')),
                    'email': email,
                    'name': user_data.get('name'),
                    'first_name': user_data.get('name', '').split(' ')[0] if user_data.get('name') else None,
                    'last_name': ' '.join(user_data.get('name', '').split(' ')[1:]) if user_data.get('name') and len(user_data.get('name', '').split(' ')) > 1 else None,
                    'avatar_url': user_data.get('avatar_url'),
                    'verified_email': True if email else False
                }
            
            else:
                raise ValueError(f"Unsupported OAuth provider: {provider}")
                
        except Exception as e:
            logger.error("Error getting user info from OAuth provider", error=str(e), provider=provider)
            raise
    
    def is_provider_configured(self, provider: str) -> bool:
        """Check if OAuth provider is configured."""
        return provider in self.oauth._clients
    
    def get_configured_providers(self) -> list[str]:
        """Get list of configured OAuth providers."""
        return list(self.oauth._clients.keys())


# Global OAuth service instance
oauth_service = OAuthService()


def get_oauth_service() -> OAuthService:
    """Get OAuth service instance."""
    return oauth_service
