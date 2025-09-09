"""
Authentication service for JWT tokens, password handling, and OAuth integration.
"""

import uuid
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import structlog

from app.core.config import settings
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.schemas.auth import UserCreate, UserLogin, TokenResponse, UserRole

logger = structlog.get_logger()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service for user management and JWT tokens."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            if payload.get("type") != token_type:
                return None
            return payload
        except JWTError:
            return None
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password."""
        try:
            result = await self.db.execute(
                select(User).where(and_(User.email == email, User.is_active == True))
            )
            user = result.scalar_one_or_none()
            
            if not user or not user.password_hash:
                return None
            
            if not self.verify_password(password, user.password_hash):
                return None
            
            # Update last login
            user.last_login = datetime.utcnow()
            await self.db.commit()
            
            logger.info("User authenticated successfully", user_id=str(user.id), email=user.email)
            return user
            
        except Exception as e:
            logger.error("Authentication error", error=str(e), email=email)
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            result = await self.db.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Error getting user by email", error=str(e), email=email)
            return None
    
    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID."""
        try:
            result = await self.db.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Error getting user by ID", error=str(e), user_id=str(user_id))
            return None
    
    async def create_user(self, user_data: UserCreate) -> Tuple[User, Organization]:
        """Create a new user and their default organization."""
        try:
            # Check if user already exists
            existing_user = await self.get_user_by_email(user_data.email)
            if existing_user:
                raise ValueError("User with this email already exists")
            
            # Check if username is taken
            result = await self.db.execute(select(User).where(User.username == user_data.username))
            if result.scalar_one_or_none():
                raise ValueError("Username already taken")
            
            # Create user
            user = User(
                email=user_data.email,
                username=user_data.username,
                password_hash=self.get_password_hash(user_data.password),
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                is_active=True,
                is_verified=False
            )
            
            self.db.add(user)
            await self.db.flush()  # Get the user ID
            
            # Create default organization
            org_name = user_data.organization_name or f"{user_data.username}'s Organization"
            org_slug = self._generate_org_slug(org_name)
            
            organization = Organization(
                name=org_name,
                slug=org_slug,
                owner_id=user.id,
                subscription_plan="free",
                subscription_status="active"
            )
            
            self.db.add(organization)
            await self.db.flush()  # Get the organization ID
            
            # Add user as owner of the organization
            membership = OrganizationMember(
                user_id=user.id,
                organization_id=organization.id,
                role=UserRole.OWNER.value,
                is_active="active"
            )
            
            self.db.add(membership)
            await self.db.commit()
            
            logger.info("User and organization created successfully", 
                       user_id=str(user.id), org_id=str(organization.id))
            
            return user, organization
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Error creating user", error=str(e))
            raise
    
    def _generate_org_slug(self, name: str) -> str:
        """Generate a unique organization slug."""
        import re
        slug = re.sub(r'[^a-zA-Z0-9-]', '-', name.lower())
        slug = re.sub(r'-+', '-', slug).strip('-')
        return f"{slug}-{secrets.token_hex(4)}"
    
    async def create_tokens(self, user: User) -> TokenResponse:
        """Create access and refresh tokens for a user."""
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "username": user.username,
            "is_verified": user.is_verified,
            "is_superuser": user.is_superuser
        }
        
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token(token_data)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    async def refresh_tokens(self, refresh_token: str) -> Optional[TokenResponse]:
        """Refresh access token using refresh token."""
        payload = self.verify_token(refresh_token, "refresh")
        if not payload:
            return None
        
        user_id = uuid.UUID(payload.get("sub"))
        user = await self.get_user_by_id(user_id)
        
        if not user or not user.is_active:
            return None
        
        return await self.create_tokens(user)
    
    async def generate_email_verification_token(self, user: User) -> str:
        """Generate email verification token."""
        token = secrets.token_urlsafe(32)
        user.email_verification_token = token
        user.email_verification_expires = datetime.utcnow() + timedelta(hours=24)
        
        await self.db.commit()
        return token
    
    async def verify_email_token(self, token: str) -> Optional[User]:
        """Verify email verification token."""
        try:
            result = await self.db.execute(
                select(User).where(
                    and_(
                        User.email_verification_token == token,
                        User.email_verification_expires > datetime.utcnow()
                    )
                )
            )
            user = result.scalar_one_or_none()
            
            if user:
                user.is_verified = True
                user.email_verification_token = None
                user.email_verification_expires = None
                await self.db.commit()
                
                logger.info("Email verified successfully", user_id=str(user.id))
                return user
            
            return None
            
        except Exception as e:
            logger.error("Error verifying email token", error=str(e))
            return None
    
    async def generate_password_reset_token(self, user: User) -> str:
        """Generate password reset token."""
        token = secrets.token_urlsafe(32)
        user.password_reset_token = token
        user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        
        await self.db.commit()
        return token
    
    async def reset_password(self, token: str, new_password: str) -> Optional[User]:
        """Reset password using reset token."""
        try:
            result = await self.db.execute(
                select(User).where(
                    and_(
                        User.password_reset_token == token,
                        User.password_reset_expires > datetime.utcnow()
                    )
                )
            )
            user = result.scalar_one_or_none()
            
            if user:
                user.password_hash = self.get_password_hash(new_password)
                user.password_reset_token = None
                user.password_reset_expires = None
                await self.db.commit()
                
                logger.info("Password reset successfully", user_id=str(user.id))
                return user
            
            return None
            
        except Exception as e:
            logger.error("Error resetting password", error=str(e))
            return None
    
    async def change_password(self, user: User, current_password: str, new_password: str) -> bool:
        """Change user password."""
        try:
            if not self.verify_password(current_password, user.password_hash):
                return False
            
            user.password_hash = self.get_password_hash(new_password)
            await self.db.commit()
            
            logger.info("Password changed successfully", user_id=str(user.id))
            return True
            
        except Exception as e:
            logger.error("Error changing password", error=str(e), user_id=str(user.id))
            return False
    
    async def get_user_organizations(self, user: User) -> list[Organization]:
        """Get all organizations a user belongs to."""
        try:
            result = await self.db.execute(
                select(Organization)
                .join(OrganizationMember)
                .where(OrganizationMember.user_id == user.id)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error("Error getting user organizations", error=str(e), user_id=str(user.id))
            return []
