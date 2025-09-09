"""
Comprehensive test configuration and fixtures for all services.
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
import tempfile
import os
from unittest.mock import Mock, AsyncMock
import factory
from factory.alchemy import SQLAlchemyModelFactory

from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.style_profile import StyleProfile
from app.models.reference_article import ReferenceArticle
from app.models.generated_content import GeneratedContent
from app.models.content_iteration import ContentIteration
from app.models.api_usage import APIUsage
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.email_service import EmailService
from app.services.content_service import ContentService
from app.services.style_service import StyleService
from app.services.openai_service import OpenAIService
from app.services.file_service import FileService

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        yield session
    
    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def client(db_session: AsyncSession) -> TestClient:
    """Create a test client with database session override."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.s.2a",  # "password123"
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
async def test_organization(db_session: AsyncSession, test_user: User) -> Organization:
    """Create a test organization."""
    organization = Organization(
        name="Test Organization",
        slug="test-org-1234",
        description="A test organization",
        owner_id=test_user.id,
        subscription_plan="free",
        subscription_status="active"
    )
    
    db_session.add(organization)
    await db_session.commit()
    await db_session.refresh(organization)
    
    return organization


@pytest.fixture
async def test_membership(db_session: AsyncSession, test_user: User, test_organization: Organization) -> OrganizationMember:
    """Create a test organization membership."""
    membership = OrganizationMember(
        user_id=test_user.id,
        organization_id=test_organization.id,
        role="owner",
        is_active="active"
    )
    
    db_session.add(membership)
    await db_session.commit()
    await db_session.refresh(membership)
    
    return membership


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user."""
    user = User(
        email="admin@example.com",
        username="admin",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.s.2a",  # "password123"
        first_name="Admin",
        last_name="User",
        is_active=True,
        is_verified=True,
        is_superuser=True
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest.fixture
def auth_service(db_session: AsyncSession) -> AuthService:
    """Create an auth service instance."""
    return AuthService(db_session)


@pytest.fixture
def user_service(db_session: AsyncSession) -> UserService:
    """Create a user service instance."""
    return UserService(db_session)


@pytest.fixture
def email_service() -> EmailService:
    """Create an email service instance."""
    return EmailService()


@pytest.fixture
def test_user_data():
    """Test user registration data."""
    return {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "password123",
        "first_name": "New",
        "last_name": "User",
        "organization_name": "New User's Organization"
    }


@pytest.fixture
def test_login_data():
    """Test user login data."""
    return {
        "email": "test@example.com",
        "password": "password123"
    }


@pytest.fixture
def test_organization_data():
    """Test organization creation data."""
    return {
        "name": "New Organization",
        "description": "A new test organization"
    }


@pytest.fixture
def test_invitation_data():
    """Test organization invitation data."""
    return {
        "email": "invited@example.com",
        "role": "editor",
        "message": "Welcome to our organization!"
    }


@pytest.fixture
def mock_oauth_user_info():
    """Mock OAuth user info."""
    return {
        "id": "123456789",
        "email": "oauth@example.com",
        "name": "OAuth User",
        "first_name": "OAuth",
        "last_name": "User",
        "avatar_url": "https://example.com/avatar.jpg",
        "verified_email": True
    }


@pytest.fixture
def mock_google_oauth_response():
    """Mock Google OAuth response."""
    return {
        "access_token": "mock_access_token",
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": "mock_refresh_token",
        "scope": "openid email profile"
    }


@pytest.fixture
def mock_github_oauth_response():
    """Mock GitHub OAuth response."""
    return {
        "access_token": "mock_access_token",
        "token_type": "bearer",
        "scope": "user:email"
    }


@pytest.fixture
def temp_env_file():
    """Create a temporary environment file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("""
# Test environment variables
ENVIRONMENT=testing
DEBUG=True
JWT_SECRET_KEY=test-secret-key-for-testing-only-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
SESSION_SECRET_KEY=test-session-secret-key-for-testing-only-32-chars
DATABASE_URL=sqlite+aiosqlite:///:memory:
SMTP_HOST=localhost
SMTP_PORT=587
SMTP_USERNAME=test@example.com
SMTP_PASSWORD=testpassword
EMAIL_FROM=test@example.com
EMAIL_FROM_NAME=Test AI Writer
        """)
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    try:
        os.unlink(temp_file)
    except OSError:
        pass


@pytest.fixture
def mock_smtp_server(monkeypatch):
    """Mock SMTP server for email testing."""
    class MockSMTP:
        def __init__(self, host, port):
            self.host = host
            self.port = port
            self.starttls_called = False
            self.login_called = False
            self.send_message_called = False
        
        def starttls(self):
            self.starttls_called = True
        
        def login(self, username, password):
            self.login_called = True
        
        def send_message(self, msg):
            self.send_message_called = True
        
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
    
    monkeypatch.setattr("smtplib.SMTP", MockSMTP)
    return MockSMTP


@pytest.fixture
def mock_oauth_provider(monkeypatch):
    """Mock OAuth provider for testing."""
    class MockOAuthClient:
        def __init__(self, *args, **kwargs):
            pass
        
        async def authorize_redirect(self, request, redirect_uri, state=None):
            return f"https://oauth.provider.com/authorize?redirect_uri={redirect_uri}&state={state}"
        
        async def authorize_access_token(self, request):
            return {
                "access_token": "mock_access_token",
                "token_type": "Bearer",
                "expires_in": 3600
            }
        
        async def get(self, url):
            class MockResponse:
                def json(self):
                    return {
                        "id": "123456789",
                        "email": "oauth@example.com",
                        "name": "OAuth User",
                        "given_name": "OAuth",
                        "family_name": "User",
                        "picture": "https://example.com/avatar.jpg",
                        "verified_email": True
                    }
            
            return MockResponse()
    
    # Mock the OAuth service methods
    monkeypatch.setattr("app.core.oauth.oauth_service.is_provider_configured", lambda provider: True)
    monkeypatch.setattr("app.core.oauth.oauth_service.get_authorization_url", 
                       lambda provider, redirect_uri, state, request: f"https://oauth.provider.com/authorize?redirect_uri={redirect_uri}&state={state}")
    monkeypatch.setattr("app.core.oauth.oauth_service.get_access_token", 
                       lambda provider, code, redirect_uri, request: {"access_token": "mock_access_token", "token_type": "Bearer"})
    monkeypatch.setattr("app.core.oauth.oauth_service.get_user_info", 
                       lambda provider, token: {
                           "id": "123456789",
                           "email": "oauth@example.com",
                           "name": "OAuth User",
                           "first_name": "OAuth",
                           "last_name": "User",
                           "avatar_url": "https://example.com/avatar.jpg",
                           "verified_email": True
                       })
    
    return MockOAuthClient


# Factory Boy factories for test data generation
class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"
    
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    username = factory.Sequence(lambda n: f"user{n}")
    password_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.s.2a"  # "password123"
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_verified = True
    is_superuser = False


class OrganizationFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Organization
        sqlalchemy_session_persistence = "commit"
    
    name = factory.Faker("company")
    slug = factory.Sequence(lambda n: f"org-{n}")
    description = factory.Faker("text", max_nb_chars=200)
    subscription_plan = "free"
    subscription_status = "active"


class StyleProfileFactory(SQLAlchemyModelFactory):
    class Meta:
        model = StyleProfile
        sqlalchemy_session_persistence = "commit"
    
    name = factory.Faker("word")
    description = factory.Faker("text", max_nb_chars=500)
    tone = "professional"
    voice = "authoritative"
    target_audience = "general"
    content_type = "article"


class ReferenceArticleFactory(SQLAlchemyModelFactory):
    class Meta:
        model = ReferenceArticle
        sqlalchemy_session_persistence = "commit"
    
    title = factory.Faker("sentence", nb_words=6)
    content = factory.Faker("text", max_nb_chars=2000)
    url = factory.Faker("url")
    author = factory.Faker("name")
    publication_date = factory.Faker("date")


class GeneratedContentFactory(SQLAlchemyModelFactory):
    class Meta:
        model = GeneratedContent
        sqlalchemy_session_persistence = "commit"
    
    title = factory.Faker("sentence", nb_words=6)
    content = factory.Faker("text", max_nb_chars=3000)
    brief = factory.Faker("text", max_nb_chars=500)
    target_words = 1000
    status = "completed"


# Additional test fixtures
@pytest.fixture
def mock_openai_service():
    """Mock OpenAI service for testing."""
    mock_service = Mock(spec=OpenAIService)
    mock_service.generate_content = AsyncMock(return_value={
        "content": "Generated test content",
        "tokens_used": 100,
        "cost": 0.01
    })
    mock_service.analyze_style = AsyncMock(return_value={
        "tone": "professional",
        "voice": "authoritative",
        "target_audience": "general"
    })
    return mock_service


@pytest.fixture
def mock_file_service():
    """Mock file service for testing."""
    mock_service = Mock(spec=FileService)
    mock_service.upload_file = AsyncMock(return_value="https://example.com/file.pdf")
    mock_service.delete_file = AsyncMock(return_value=True)
    mock_service.extract_text = AsyncMock(return_value="Extracted text content")
    return mock_service


@pytest.fixture
def mock_email_service():
    """Mock email service for testing."""
    mock_service = Mock(spec=EmailService)
    mock_service.send_email = AsyncMock(return_value=True)
    mock_service.send_verification_email = AsyncMock(return_value=True)
    mock_service.send_password_reset_email = AsyncMock(return_value=True)
    return mock_service


@pytest.fixture
def content_service(db_session: AsyncSession, mock_openai_service, mock_file_service):
    """Create a content service instance with mocked dependencies."""
    return ContentService(db_session, mock_openai_service, mock_file_service)


@pytest.fixture
def style_service(db_session: AsyncSession, mock_openai_service, mock_file_service):
    """Create a style service instance with mocked dependencies."""
    return StyleService(db_session, mock_openai_service, mock_file_service)


@pytest.fixture
def test_style_profile(db_session: AsyncSession, test_organization: Organization) -> StyleProfile:
    """Create a test style profile."""
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
    
    return style_profile


@pytest.fixture
def test_reference_article(db_session: AsyncSession, test_style_profile: StyleProfile) -> ReferenceArticle:
    """Create a test reference article."""
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
    
    return article


@pytest.fixture
def test_generated_content(db_session: AsyncSession, test_user: User, test_organization: Organization) -> GeneratedContent:
    """Create test generated content."""
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
    
    return content


@pytest.fixture
def test_content_iteration(db_session: AsyncSession, test_generated_content: GeneratedContent) -> ContentIteration:
    """Create test content iteration."""
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
    
    return iteration


@pytest.fixture
def test_api_usage(db_session: AsyncSession, test_user: User, test_organization: Organization) -> APIUsage:
    """Create test API usage record."""
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
    
    return usage


@pytest.fixture
def auth_headers(test_user: User, auth_service: AuthService):
    """Create authentication headers for API requests."""
    access_token = auth_service.create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_auth_headers(admin_user: User, auth_service: AuthService):
    """Create admin authentication headers for API requests."""
    access_token = auth_service.create_access_token(data={"sub": admin_user.email})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def test_file_content():
    """Test file content for upload testing."""
    return b"This is test file content for upload testing."


@pytest.fixture
def test_file_data():
    """Test file data for upload testing."""
    return {
        "filename": "test.txt",
        "content_type": "text/plain",
        "size": 1024
    }


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    mock_redis = Mock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=True)
    mock_redis.exists = AsyncMock(return_value=False)
    return mock_redis


@pytest.fixture
def mock_celery():
    """Mock Celery for testing."""
    mock_celery = Mock()
    mock_celery.send_task = Mock(return_value=Mock(id="test-task-id"))
    return mock_celery
