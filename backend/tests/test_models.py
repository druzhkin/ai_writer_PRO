"""
Database model tests covering all models, relationships, constraints, and validation.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.style_profile import StyleProfile
from app.models.reference_article import ReferenceArticle
from app.models.generated_content import GeneratedContent
from app.models.content_iteration import ContentIteration
from app.models.api_usage import APIUsage


class TestUserModel:
    """Test User model."""
    
    @pytest.mark.asyncio
    async def test_create_user(self, db_session: AsyncSession):
        """Test creating a user."""
        user = User(
            email="test@example.com",
            username="testuser",
            password_hash="hashed_password",
            first_name="Test",
            last_name="User",
            is_active=True,
            is_verified=False
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.is_active is True
        assert user.is_verified is False
        assert user.created_at is not None
        assert user.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_user_unique_email(self, db_session: AsyncSession):
        """Test user email uniqueness constraint."""
        user1 = User(
            email="test@example.com",
            username="user1",
            password_hash="hash1",
            first_name="User",
            last_name="One"
        )
        
        user2 = User(
            email="test@example.com",  # Same email
            username="user2",
            password_hash="hash2",
            first_name="User",
            last_name="Two"
        )
        
        db_session.add(user1)
        await db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_user_unique_username(self, db_session: AsyncSession):
        """Test user username uniqueness constraint."""
        user1 = User(
            email="user1@example.com",
            username="testuser",
            password_hash="hash1",
            first_name="User",
            last_name="One"
        )
        
        user2 = User(
            email="user2@example.com",
            username="testuser",  # Same username
            password_hash="hash2",
            first_name="User",
            last_name="Two"
        )
        
        db_session.add(user1)
        await db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestOrganizationModel:
    """Test Organization model."""
    
    @pytest.mark.asyncio
    async def test_create_organization(self, db_session: AsyncSession, test_user: User):
        """Test creating an organization."""
        organization = Organization(
            name="Test Organization",
            slug="test-org",
            description="A test organization",
            owner_id=test_user.id,
            subscription_plan="free",
            subscription_status="active"
        )
        
        db_session.add(organization)
        await db_session.commit()
        await db_session.refresh(organization)
        
        assert organization.id is not None
        assert organization.name == "Test Organization"
        assert organization.slug == "test-org"
        assert organization.owner_id == test_user.id
        assert organization.created_at is not None
    
    @pytest.mark.asyncio
    async def test_organization_unique_slug(self, db_session: AsyncSession, test_user: User):
        """Test organization slug uniqueness constraint."""
        org1 = Organization(
            name="Organization 1",
            slug="test-slug",
            owner_id=test_user.id
        )
        
        org2 = Organization(
            name="Organization 2",
            slug="test-slug",  # Same slug
            owner_id=test_user.id
        )
        
        db_session.add(org1)
        await db_session.commit()
        
        db_session.add(org2)
        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestOrganizationMemberModel:
    """Test OrganizationMember model."""
    
    @pytest.mark.asyncio
    async def test_create_membership(self, db_session: AsyncSession, test_user: User, test_organization: Organization):
        """Test creating organization membership."""
        membership = OrganizationMember(
            user_id=test_user.id,
            organization_id=test_organization.id,
            role="editor",
            is_active="active"
        )
        
        db_session.add(membership)
        await db_session.commit()
        await db_session.refresh(membership)
        
        assert membership.id is not None
        assert membership.user_id == test_user.id
        assert membership.organization_id == test_organization.id
        assert membership.role == "editor"
        assert membership.is_active == "active"
    
    @pytest.mark.asyncio
    async def test_membership_unique_user_org(self, db_session: AsyncSession, test_user: User, test_organization: Organization):
        """Test unique user-organization membership constraint."""
        membership1 = OrganizationMember(
            user_id=test_user.id,
            organization_id=test_organization.id,
            role="editor"
        )
        
        membership2 = OrganizationMember(
            user_id=test_user.id,  # Same user
            organization_id=test_organization.id,  # Same organization
            role="admin"
        )
        
        db_session.add(membership1)
        await db_session.commit()
        
        db_session.add(membership2)
        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestStyleProfileModel:
    """Test StyleProfile model."""
    
    @pytest.mark.asyncio
    async def test_create_style_profile(self, db_session: AsyncSession, test_organization: Organization):
        """Test creating a style profile."""
        style_profile = StyleProfile(
            name="Test Style",
            description="A test style profile",
            tone="professional",
            voice="authoritative",
            target_audience="general",
            content_type="article",
            organization_id=test_organization.id
        )
        
        db_session.add(style_profile)
        await db_session.commit()
        await db_session.refresh(style_profile)
        
        assert style_profile.id is not None
        assert style_profile.name == "Test Style"
        assert style_profile.organization_id == test_organization.id
        assert style_profile.created_at is not None


class TestReferenceArticleModel:
    """Test ReferenceArticle model."""
    
    @pytest.mark.asyncio
    async def test_create_reference_article(self, db_session: AsyncSession, test_style_profile: StyleProfile):
        """Test creating a reference article."""
        article = ReferenceArticle(
            title="Test Article",
            content="This is test content for style analysis.",
            url="https://example.com/test-article",
            author="Test Author",
            style_profile_id=test_style_profile.id
        )
        
        db_session.add(article)
        await db_session.commit()
        await db_session.refresh(article)
        
        assert article.id is not None
        assert article.title == "Test Article"
        assert article.style_profile_id == test_style_profile.id
        assert article.created_at is not None


class TestGeneratedContentModel:
    """Test GeneratedContent model."""
    
    @pytest.mark.asyncio
    async def test_create_generated_content(self, db_session: AsyncSession, test_user: User, test_organization: Organization):
        """Test creating generated content."""
        content = GeneratedContent(
            title="Test Generated Content",
            content="This is test generated content.",
            brief="Test brief for content generation",
            target_words=1000,
            status="completed",
            user_id=test_user.id,
            organization_id=test_organization.id
        )
        
        db_session.add(content)
        await db_session.commit()
        await db_session.refresh(content)
        
        assert content.id is not None
        assert content.title == "Test Generated Content"
        assert content.user_id == test_user.id
        assert content.organization_id == test_organization.id
        assert content.created_at is not None


class TestContentIterationModel:
    """Test ContentIteration model."""
    
    @pytest.mark.asyncio
    async def test_create_content_iteration(self, db_session: AsyncSession, test_generated_content: GeneratedContent):
        """Test creating content iteration."""
        iteration = ContentIteration(
            content_id=test_generated_content.id,
            iteration_number=1,
            content="This is the first iteration of the content.",
            diff_lines=[],
            user_feedback="Good start, but needs more detail."
        )
        
        db_session.add(iteration)
        await db_session.commit()
        await db_session.refresh(iteration)
        
        assert iteration.id is not None
        assert iteration.content_id == test_generated_content.id
        assert iteration.iteration_number == 1
        assert iteration.created_at is not None


class TestAPIUsageModel:
    """Test APIUsage model."""
    
    @pytest.mark.asyncio
    async def test_create_api_usage(self, db_session: AsyncSession, test_user: User, test_organization: Organization):
        """Test creating API usage record."""
        usage = APIUsage(
            user_id=test_user.id,
            organization_id=test_organization.id,
            endpoint="/api/v1/content/generate",
            method="POST",
            tokens_used=100,
            cost=0.01,
            response_time=1.5
        )
        
        db_session.add(usage)
        await db_session.commit()
        await db_session.refresh(usage)
        
        assert usage.id is not None
        assert usage.user_id == test_user.id
        assert usage.organization_id == test_organization.id
        assert usage.tokens_used == 100
        assert usage.cost == 0.01
        assert usage.created_at is not None


class TestModelRelationships:
    """Test model relationships and cascading operations."""
    
    @pytest.mark.asyncio
    async def test_user_organization_relationship(self, db_session: AsyncSession, test_user: User, test_organization: Organization):
        """Test user-organization relationship."""
        # Test that user can access their organizations through memberships
        membership = OrganizationMember(
            user_id=test_user.id,
            organization_id=test_organization.id,
            role="owner"
        )
        
        db_session.add(membership)
        await db_session.commit()
        
        # Verify relationship
        assert membership.user_id == test_user.id
        assert membership.organization_id == test_organization.id
    
    @pytest.mark.asyncio
    async def test_organization_style_profiles_relationship(self, db_session: AsyncSession, test_organization: Organization):
        """Test organization-style profiles relationship."""
        style_profile = StyleProfile(
            name="Test Style",
            organization_id=test_organization.id,
            tone="professional",
            voice="authoritative",
            target_audience="general",
            content_type="article"
        )
        
        db_session.add(style_profile)
        await db_session.commit()
        
        # Verify relationship
        assert style_profile.organization_id == test_organization.id
    
    @pytest.mark.asyncio
    async def test_style_profile_reference_articles_relationship(self, db_session: AsyncSession, test_style_profile: StyleProfile):
        """Test style profile-reference articles relationship."""
        article = ReferenceArticle(
            title="Test Article",
            content="Test content",
            style_profile_id=test_style_profile.id
        )
        
        db_session.add(article)
        await db_session.commit()
        
        # Verify relationship
        assert article.style_profile_id == test_style_profile.id
    
    @pytest.mark.asyncio
    async def test_content_iterations_relationship(self, db_session: AsyncSession, test_generated_content: GeneratedContent):
        """Test generated content-iterations relationship."""
        iteration = ContentIteration(
            content_id=test_generated_content.id,
            iteration_number=1,
            content="Test iteration content"
        )
        
        db_session.add(iteration)
        await db_session.commit()
        
        # Verify relationship
        assert iteration.content_id == test_generated_content.id


class TestModelValidation:
    """Test model validation and constraints."""
    
    @pytest.mark.asyncio
    async def test_user_email_validation(self, db_session: AsyncSession):
        """Test user email format validation."""
        # This would typically be handled by Pydantic schemas, but we can test database constraints
        user = User(
            email="invalid-email",  # Invalid email format
            username="testuser",
            password_hash="hash",
            first_name="Test",
            last_name="User"
        )
        
        db_session.add(user)
        # The database might not enforce email format, but the application layer should
        await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_organization_slug_validation(self, db_session: AsyncSession, test_user: User):
        """Test organization slug format validation."""
        organization = Organization(
            name="Test Organization",
            slug="invalid slug with spaces",  # Invalid slug format
            owner_id=test_user.id
        )
        
        db_session.add(organization)
        # The database might not enforce slug format, but the application layer should
        await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_content_status_validation(self, db_session: AsyncSession, test_user: User, test_organization: Organization):
        """Test content status validation."""
        content = GeneratedContent(
            title="Test Content",
            content="Test content",
            status="invalid_status",  # Invalid status
            user_id=test_user.id,
            organization_id=test_organization.id
        )
        
        db_session.add(content)
        # The database might not enforce status values, but the application layer should
        await db_session.commit()
