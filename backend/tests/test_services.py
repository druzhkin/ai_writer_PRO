"""
Comprehensive service layer tests for all business logic services.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.content_service import ContentService
from app.services.style_service import StyleService
from app.services.openai_service import OpenAIService
from app.services.file_service import FileService
from app.services.email_service import EmailService
from app.schemas.auth import UserCreate, UserUpdate
from app.schemas.content import ContentCreate, ContentUpdate
from app.schemas.style import StyleProfileCreate, StyleProfileUpdate
from app.models.user import User
from app.models.organization import Organization
from app.models.style_profile import StyleProfile
from app.models.generated_content import GeneratedContent


class TestAuthService:
    """Test authentication service."""
    
    @pytest.mark.asyncio
    async def test_create_user(self, auth_service: AuthService, test_user_data):
        """Test user creation."""
        user_data = UserCreate(**test_user_data)
        user, organization = await auth_service.create_user(user_data)
        
        assert user.email == test_user_data["email"]
        assert user.username == test_user_data["username"]
        assert user.is_active is True
        assert user.is_verified is False
        assert organization.name == test_user_data["organization_name"]
    
    @pytest.mark.asyncio
    async def test_authenticate_user(self, auth_service: AuthService, test_user: User):
        """Test user authentication."""
        user = await auth_service.authenticate_user("test@example.com", "password123")
        assert user is not None
        assert user.email == "test@example.com"
        
        # Test invalid password
        user = await auth_service.authenticate_user("test@example.com", "wrongpassword")
        assert user is None
    
    @pytest.mark.asyncio
    async def test_create_access_token(self, auth_service: AuthService, test_user: User):
        """Test access token creation."""
        token = auth_service.create_access_token(data={"sub": test_user.email})
        assert isinstance(token, str)
        assert len(token) > 0
    
    @pytest.mark.asyncio
    async def test_verify_token(self, auth_service: AuthService, test_user: User):
        """Test token verification."""
        token = auth_service.create_access_token(data={"sub": test_user.email})
        user = await auth_service.verify_token(token)
        assert user is not None
        assert user.email == test_user.email
    
    @pytest.mark.asyncio
    async def test_invalid_token(self, auth_service: AuthService):
        """Test invalid token verification."""
        user = await auth_service.verify_token("invalid_token")
        assert user is None


class TestUserService:
    """Test user management service."""
    
    @pytest.mark.asyncio
    async def test_get_user_by_id(self, user_service: UserService, test_user: User):
        """Test getting user by ID."""
        user = await user_service.get_user_by_id(test_user.id)
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email
    
    @pytest.mark.asyncio
    async def test_get_user_by_email(self, user_service: UserService, test_user: User):
        """Test getting user by email."""
        user = await user_service.get_user_by_email(test_user.email)
        assert user is not None
        assert user.email == test_user.email
    
    @pytest.mark.asyncio
    async def test_update_user(self, user_service: UserService, test_user: User):
        """Test updating user."""
        update_data = UserUpdate(first_name="Updated", last_name="Name")
        updated_user = await user_service.update_user(test_user.id, update_data)
        
        assert updated_user.first_name == "Updated"
        assert updated_user.last_name == "Name"
        assert updated_user.email == test_user.email  # Email should not change
    
    @pytest.mark.asyncio
    async def test_deactivate_user(self, user_service: UserService, test_user: User):
        """Test deactivating user."""
        await user_service.deactivate_user(test_user.id)
        user = await user_service.get_user_by_id(test_user.id)
        assert user.is_active is False


class TestContentService:
    """Test content generation service."""
    
    @pytest.mark.asyncio
    async def test_generate_content(self, content_service: ContentService, test_user: User, test_organization: Organization, test_style_profile: StyleProfile):
        """Test content generation."""
        content_data = ContentCreate(
            title="Test Article",
            brief="This is a test brief",
            target_words=1000,
            style_profile_id=test_style_profile.id,
            organization_id=test_organization.id
        )
        
        with patch('app.services.content_service.ContentService._generate_with_openai') as mock_generate:
            mock_generate.return_value = {
                "content": "Generated test content",
                "tokens_used": 100,
                "cost": 0.01
            }
            
            content = await content_service.generate_content(content_data, test_user.id)
            
            assert content.title == "Test Article"
            assert content.brief == "This is a test brief"
            assert content.target_words == 1000
            assert content.status == "completed"
    
    @pytest.mark.asyncio
    async def test_get_user_content(self, content_service: ContentService, test_user: User, test_organization: Organization):
        """Test getting user's content."""
        content_list = await content_service.get_user_content(test_user.id, test_organization.id)
        assert isinstance(content_list, list)
    
    @pytest.mark.asyncio
    async def test_update_content(self, content_service: ContentService, test_generated_content: GeneratedContent):
        """Test updating content."""
        update_data = ContentUpdate(title="Updated Title")
        updated_content = await content_service.update_content(test_generated_content.id, update_data)
        
        assert updated_content.title == "Updated Title"
        assert updated_content.id == test_generated_content.id
    
    @pytest.mark.asyncio
    async def test_delete_content(self, content_service: ContentService, test_generated_content: GeneratedContent):
        """Test deleting content."""
        result = await content_service.delete_content(test_generated_content.id)
        assert result is True
        
        # Verify content is deleted
        content = await content_service.get_content_by_id(test_generated_content.id)
        assert content is None


class TestStyleService:
    """Test style analysis service."""
    
    @pytest.mark.asyncio
    async def test_create_style_profile(self, style_service: StyleService, test_organization: Organization):
        """Test creating style profile."""
        style_data = StyleProfileCreate(
            name="Test Style",
            description="A test style profile",
            tone="professional",
            voice="authoritative",
            target_audience="general",
            content_type="article",
            organization_id=test_organization.id
        )
        
        style_profile = await style_service.create_style_profile(style_data)
        
        assert style_profile.name == "Test Style"
        assert style_profile.tone == "professional"
        assert style_profile.organization_id == test_organization.id
    
    @pytest.mark.asyncio
    async def test_analyze_reference_articles(self, style_service: StyleService, test_style_profile: StyleProfile):
        """Test analyzing reference articles."""
        with patch('app.services.style_service.StyleService._analyze_with_openai') as mock_analyze:
            mock_analyze.return_value = {
                "tone": "professional",
                "voice": "authoritative",
                "target_audience": "general"
            }
            
            analysis = await style_service.analyze_reference_articles(test_style_profile.id)
            
            assert analysis["tone"] == "professional"
            assert analysis["voice"] == "authoritative"
    
    @pytest.mark.asyncio
    async def test_get_organization_styles(self, style_service: StyleService, test_organization: Organization):
        """Test getting organization's style profiles."""
        styles = await style_service.get_organization_styles(test_organization.id)
        assert isinstance(styles, list)
    
    @pytest.mark.asyncio
    async def test_update_style_profile(self, style_service: StyleService, test_style_profile: StyleProfile):
        """Test updating style profile."""
        update_data = StyleProfileUpdate(description="Updated description")
        updated_style = await style_service.update_style_profile(test_style_profile.id, update_data)
        
        assert updated_style.description == "Updated description"
        assert updated_style.id == test_style_profile.id


class TestOpenAIService:
    """Test OpenAI integration service."""
    
    @pytest.mark.asyncio
    async def test_generate_content(self, mock_openai_service):
        """Test content generation with OpenAI."""
        result = await mock_openai_service.generate_content(
            prompt="Write a test article",
            max_tokens=1000,
            temperature=0.7
        )
        
        assert "content" in result
        assert "tokens_used" in result
        assert "cost" in result
        assert result["content"] == "Generated test content"
    
    @pytest.mark.asyncio
    async def test_analyze_style(self, mock_openai_service):
        """Test style analysis with OpenAI."""
        result = await mock_openai_service.analyze_style(
            content="This is test content for analysis"
        )
        
        assert "tone" in result
        assert "voice" in result
        assert "target_audience" in result
        assert result["tone"] == "professional"


class TestFileService:
    """Test file handling service."""
    
    @pytest.mark.asyncio
    async def test_upload_file(self, mock_file_service, test_file_content):
        """Test file upload."""
        result = await mock_file_service.upload_file(
            file_content=test_file_content,
            filename="test.txt",
            content_type="text/plain"
        )
        
        assert result == "https://example.com/file.pdf"
    
    @pytest.mark.asyncio
    async def test_extract_text(self, mock_file_service, test_file_content):
        """Test text extraction from file."""
        result = await mock_file_service.extract_text(
            file_content=test_file_content,
            content_type="text/plain"
        )
        
        assert result == "Extracted text content"
    
    @pytest.mark.asyncio
    async def test_delete_file(self, mock_file_service):
        """Test file deletion."""
        result = await mock_file_service.delete_file("https://example.com/file.pdf")
        assert result is True


class TestEmailService:
    """Test email service."""
    
    @pytest.mark.asyncio
    async def test_send_verification_email(self, mock_email_service, test_user: User):
        """Test sending verification email."""
        result = await mock_email_service.send_verification_email(test_user.email, "verification_token")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_send_password_reset_email(self, mock_email_service, test_user: User):
        """Test sending password reset email."""
        result = await mock_email_service.send_password_reset_email(test_user.email, "reset_token")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_send_email(self, mock_email_service):
        """Test sending generic email."""
        result = await mock_email_service.send_email(
            to="test@example.com",
            subject="Test Subject",
            body="Test Body"
        )
        assert result is True


class TestServiceIntegration:
    """Test service integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_content_generation_workflow(self, content_service: ContentService, style_service: StyleService, test_user: User, test_organization: Organization):
        """Test complete content generation workflow."""
        # Create style profile
        style_data = StyleProfileCreate(
            name="Test Style",
            description="A test style profile",
            tone="professional",
            voice="authoritative",
            target_audience="general",
            content_type="article",
            organization_id=test_organization.id
        )
        style_profile = await style_service.create_style_profile(style_data)
        
        # Generate content
        content_data = ContentCreate(
            title="Test Article",
            brief="This is a test brief",
            target_words=1000,
            style_profile_id=style_profile.id,
            organization_id=test_organization.id
        )
        
        with patch('app.services.content_service.ContentService._generate_with_openai') as mock_generate:
            mock_generate.return_value = {
                "content": "Generated test content",
                "tokens_used": 100,
                "cost": 0.01
            }
            
            content = await content_service.generate_content(content_data, test_user.id)
            
            assert content is not None
            assert content.style_profile_id == style_profile.id
    
    @pytest.mark.asyncio
    async def test_user_registration_workflow(self, auth_service: AuthService, user_service: UserService):
        """Test complete user registration workflow."""
        user_data = UserCreate(
            email="newuser@example.com",
            username="newuser",
            password="password123",
            first_name="New",
            last_name="User",
            organization_name="New User's Organization"
        )
        
        # Create user and organization
        user, organization = await auth_service.create_user(user_data)
        
        # Verify user was created
        retrieved_user = await user_service.get_user_by_id(user.id)
        assert retrieved_user.email == user_data.email
        
        # Verify organization was created
        assert organization.name == user_data.organization_name
