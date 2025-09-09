"""
Tests for content generation functionality.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app

from app.models.generated_content import GeneratedContent
from app.models.content_iteration import ContentIteration
from app.models.style_profile import StyleProfile
from app.models.user import User
from app.models.organization import Organization
from app.schemas.content import (
    ContentGenerationRequest, ContentEditRequest, ContentType, EditType,
    ContentStatus
)
from app.services.content_service import ContentService
from app.services.openai_service import OpenAIService
from app.services.usage_service import UsageService


class TestContentService:
    """Test cases for ContentService."""
    
    @pytest.fixture
    async def content_service(self):
        """Create ContentService instance."""
        return ContentService()
    
    @pytest.fixture
    async def sample_organization(self, db_session: AsyncSession, sample_user):
        """Create sample organization."""
        org = Organization(
            name="Test Organization",
            slug="test-org",
            owner_id=sample_user.id
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
    async def sample_style_profile(self, db_session: AsyncSession, sample_organization):
        """Create sample style profile."""
        style_profile = StyleProfile(
            name="Test Style",
            description="Test style profile",
            organization_id=sample_organization.id,
            analysis={"tone": "professional", "formality": "formal"}
        )
        db_session.add(style_profile)
        await db_session.commit()
        await db_session.refresh(style_profile)
        return style_profile
    
    @pytest.fixture
    async def sample_content(self, db_session: AsyncSession, sample_organization, sample_user):
        """Create sample generated content."""
        content = GeneratedContent(
            organization_id=sample_organization.id,
            created_by_id=sample_user.id,
            title="Test Article",
            brief="Test brief",
            content_type="article",
            generated_text="This is a test article with some content.",
            word_count=10,
            character_count=50,
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            estimated_cost=0.01,
            model_used="gpt-4-turbo-preview",
            status="completed"
        )
        db_session.add(content)
        await db_session.commit()
        await db_session.refresh(content)
        return content
    
    @pytest.mark.asyncio
    async def test_generate_content_success(
        self,
        content_service: ContentService,
        db_session: AsyncSession,
        sample_organization: Organization,
        sample_user: User,
        sample_style_profile: StyleProfile
    ):
        """Test successful content generation."""
        # Mock OpenAI service
        with patch.object(content_service.openai_service, 'generate_content') as mock_generate:
            mock_generate.return_value = (
                True,
                "Success",
                {
                    "generated_text": "This is generated content.",
                    "word_count": 5,
                    "character_count": 25,
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "total_tokens": 150,
                    "estimated_cost": 0.01,
                    "model_used": "gpt-4-turbo-preview",
                    "generation_prompt": "Test prompt"
                }
            )
            
            # Mock usage service
            with patch.object(content_service.usage_service, 'track_usage') as mock_track:
                mock_track.return_value = AsyncMock()
                
                request = ContentGenerationRequest(
                    title="Test Article",
                    brief="Test brief",
                    content_type=ContentType.ARTICLE,
                    style_profile_id=sample_style_profile.id
                )
                
                success, error_msg, response = await content_service.generate_content(
                    db=db_session,
                    request=request,
                    organization_id=sample_organization.id,
                    user_id=sample_user.id
                )
                
                assert success is True
                assert error_msg == "Content generated successfully"
                assert response is not None
                assert response.title == "Test Article"
                assert response.word_count == 5
                assert response.estimated_cost == 0.01
    
    @pytest.mark.asyncio
    async def test_generate_content_openai_failure(
        self,
        content_service: ContentService,
        db_session: AsyncSession,
        sample_organization: Organization,
        sample_user: User
    ):
        """Test content generation with OpenAI failure."""
        # Mock OpenAI service failure
        with patch.object(content_service.openai_service, 'generate_content') as mock_generate:
            mock_generate.return_value = (False, "OpenAI API error", None)
            
            request = ContentGenerationRequest(
                title="Test Article",
                content_type=ContentType.ARTICLE
            )
            
            success, error_msg, response = await content_service.generate_content(
                db=db_session,
                request=request,
                organization_id=sample_organization.id,
                user_id=sample_user.id
            )
            
            assert success is False
            assert "OpenAI API error" in error_msg
            assert response is None
    
    @pytest.mark.asyncio
    async def test_edit_content_success(
        self,
        content_service: ContentService,
        db_session: AsyncSession,
        sample_organization: Organization,
        sample_user: User,
        sample_content: GeneratedContent
    ):
        """Test successful content editing."""
        # Mock OpenAI service
        with patch.object(content_service.openai_service, 'edit_content') as mock_edit:
            mock_edit.return_value = (
                True,
                "Success",
                {
                    "previous_text": "This is a test article with some content.",
                    "new_text": "This is an edited test article with some content.",
                    "previous_word_count": 10,
                    "new_word_count": 11,
                    "word_count_change": 1,
                    "previous_character_count": 50,
                    "new_character_count": 55,
                    "character_count_change": 5,
                    "diff_summary": "Content expanded by 1 word",
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "total_tokens": 150,
                    "estimated_cost": 0.01,
                    "model_used": "gpt-4-turbo-preview",
                    "generation_prompt": "Test edit prompt"
                }
            )
            
            # Mock usage service
            with patch.object(content_service.usage_service, 'track_usage') as mock_track:
                mock_track.return_value = AsyncMock()
                
                request = ContentEditRequest(
                    edit_prompt="Make it more engaging",
                    edit_type=EditType.GENERAL
                )
                
                success, error_msg, response = await content_service.edit_content(
                    db=db_session,
                    content_id=sample_content.id,
                    request=request,
                    organization_id=sample_organization.id,
                    user_id=sample_user.id
                )
                
                assert success is True
                assert error_msg == "Content edited successfully"
                assert response is not None
                assert response.iteration_number == 1
                assert response.word_count_change == 1
    
    @pytest.mark.asyncio
    async def test_get_content_success(
        self,
        content_service: ContentService,
        db_session: AsyncSession,
        sample_organization: Organization,
        sample_content: GeneratedContent
    ):
        """Test successful content retrieval."""
        response = await content_service.get_content(
            db=db_session,
            content_id=sample_content.id,
            organization_id=sample_organization.id
        )
        
        assert response is not None
        assert response.id == sample_content.id
        assert response.title == "Test Article"
        assert response.word_count == 10
    
    @pytest.mark.asyncio
    async def test_get_content_not_found(
        self,
        content_service: ContentService,
        db_session: AsyncSession,
        sample_organization: Organization
    ):
        """Test content retrieval with non-existent content."""
        non_existent_id = uuid.uuid4()
        
        response = await content_service.get_content(
            db=db_session,
            content_id=non_existent_id,
            organization_id=sample_organization.id
        )
        
        assert response is None
    
    @pytest.mark.asyncio
    async def test_list_content_with_filters(
        self,
        content_service: ContentService,
        db_session: AsyncSession,
        sample_organization: Organization,
        sample_content: GeneratedContent
    ):
        """Test content listing with filters."""
        from app.schemas.content import ContentSearchParams
        
        search_params = ContentSearchParams(
            query="Test",
            content_type=ContentType.ARTICLE,
            page=1,
            per_page=10
        )
        
        response = await content_service.list_content(
            db=db_session,
            organization_id=sample_organization.id,
            search_params=search_params
        )
        
        assert response.total >= 1
        assert len(response.content) >= 1
        assert response.content[0].title == "Test Article"
    
    @pytest.mark.asyncio
    async def test_update_content_success(
        self,
        content_service: ContentService,
        db_session: AsyncSession,
        sample_organization: Organization,
        sample_content: GeneratedContent
    ):
        """Test successful content update."""
        from app.schemas.content import ContentUpdateRequest
        
        request = ContentUpdateRequest(
            title="Updated Test Article",
            is_archived=True
        )
        
        success, error_msg, response = await content_service.update_content(
            db=db_session,
            content_id=sample_content.id,
            request=request,
            organization_id=sample_organization.id
        )
        
        assert success is True
        assert error_msg == "Content updated successfully"
        assert response.title == "Updated Test Article"
    
    @pytest.mark.asyncio
    async def test_delete_content_success(
        self,
        content_service: ContentService,
        db_session: AsyncSession,
        sample_organization: Organization,
        sample_content: GeneratedContent
    ):
        """Test successful content deletion."""
        success, error_msg = await content_service.delete_content(
            db=db_session,
            content_id=sample_content.id,
            organization_id=sample_organization.id
        )
        
        assert success is True
        assert error_msg == "Content deleted successfully"
    
    @pytest.mark.asyncio
    async def test_get_content_iterations(
        self,
        content_service: ContentService,
        db_session: AsyncSession,
        sample_organization: Organization,
        sample_user: User,
        sample_content: GeneratedContent
    ):
        """Test getting content iterations."""
        # Create a sample iteration
        iteration = ContentIteration(
            generated_content_id=sample_content.id,
            edited_by_id=sample_user.id,
            iteration_number=1,
            edit_prompt="Test edit",
            edit_type="general",
            previous_text="Original text",
            new_text="Edited text",
            previous_word_count=2,
            new_word_count=2,
            word_count_change=0,
            previous_character_count=13,
            new_character_count=12,
            character_count_change=-1,
            input_tokens=50,
            output_tokens=25,
            total_tokens=75,
            estimated_cost=0.005,
            model_used="gpt-4-turbo-preview",
            status="completed"
        )
        db_session.add(iteration)
        await db_session.commit()
        
        iterations = await content_service.get_content_iterations(
            db=db_session,
            content_id=sample_content.id,
            organization_id=sample_organization.id
        )
        
        assert len(iterations) == 1
        assert iterations[0].iteration_number == 1
        assert iterations[0].edit_prompt == "Test edit"
    
    @pytest.mark.asyncio
    async def test_get_content_stats(
        self,
        content_service: ContentService,
        db_session: AsyncSession,
        sample_organization: Organization,
        sample_content: GeneratedContent
    ):
        """Test getting content statistics."""
        stats = await content_service.get_content_stats(
            db=db_session,
            organization_id=sample_organization.id
        )
        
        assert stats.total_content >= 1
        assert stats.total_words >= 10
        assert stats.total_cost >= 0.01
        assert "article" in stats.content_by_type


class TestContentAPI:
    """Test cases for content API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self, sample_user: User):
        """Create authentication headers."""
        # This would normally create a JWT token
        return {"Authorization": f"Bearer test-token"}
    
    @pytest.mark.asyncio
    async def test_generate_content_endpoint(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_organization: Organization
    ):
        """Test content generation endpoint."""
        with patch('app.api.v1.endpoints.content.ContentService') as mock_service:
            mock_response = ContentGenerationResponse(
                id=uuid.uuid4(),
                title="Test Article",
                brief="Test brief",
                content_type=ContentType.ARTICLE,
                generated_text="This is test content.",
                word_count=100,
                character_count=500,
                version=1,
                status=ContentStatus.COMPLETED,
                input_tokens=50,
                output_tokens=100,
                total_tokens=150,
                estimated_cost=0.01,
                model_used="gpt-4-turbo-preview",
                generation_time_seconds=2.5,
                organization_id=sample_organization.id,
                created_by_id=uuid.uuid4(),
                style_profile_id=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            mock_service.return_value.generate_content = AsyncMock(return_value=(
                True,
                "Success",
                mock_response
            ))
            
            response = client.post(
                f"/api/v1/organizations/{sample_organization.id}/content/generate",
                json={
                    "title": "Test Article",
                    "content_type": "article",
                    "brief": "Test brief"
                },
                headers=auth_headers
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["title"] == "Test Article"
    
    @pytest.mark.asyncio
    async def test_list_content_endpoint(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_organization: Organization
    ):
        """Test content listing endpoint."""
        with patch('app.api.v1.endpoints.content.ContentService') as mock_service:
            from app.schemas.content import ContentSearchResponse, ContentListResponse
            mock_response = ContentSearchResponse(
                content=[],
                total=0,
                page=1,
                per_page=10,
                has_next=False,
                has_prev=False
            )
            mock_service.return_value.list_content = AsyncMock(return_value=mock_response)
            
            response = client.get(
                f"/api/v1/organizations/{sample_organization.id}/content/",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "content" in data
            assert "total" in data
    
    @pytest.mark.asyncio
    async def test_get_content_endpoint(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_organization: Organization,
        sample_content: GeneratedContent
    ):
        """Test content retrieval endpoint."""
        with patch('app.api.v1.endpoints.content.ContentService') as mock_service:
            from app.schemas.content import ContentDetailResponse
            mock_response = ContentDetailResponse(
                id=sample_content.id,
                title="Test Article",
                brief="Test brief",
                content_type=ContentType.ARTICLE,
                generated_text="This is test content.",
                word_count=100,
                character_count=500,
                version=1,
                status=ContentStatus.COMPLETED,
                input_tokens=50,
                output_tokens=100,
                total_tokens=150,
                estimated_cost=0.01,
                model_used="gpt-4-turbo-preview",
                generation_time_seconds=2.5,
                organization_id=sample_content.organization_id,
                created_by_id=sample_content.created_by_id,
                style_profile_id=None,
                created_at=sample_content.created_at,
                updated_at=sample_content.updated_at,
                is_archived=False,
                iteration_count=0,
                total_cost=0.01,
                total_tokens_all_versions=150,
                reading_time_minutes=1,
                style_profile_name=None,
                created_by_name="Test User"
            )
            mock_service.return_value.get_content = AsyncMock(return_value=mock_response)
            
            response = client.get(
                f"/api/v1/organizations/{sample_organization.id}/content/{sample_content.id}",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Test Article"
    
    @pytest.mark.asyncio
    async def test_edit_content_endpoint(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_organization: Organization,
        sample_content: GeneratedContent
    ):
        """Test content editing endpoint."""
        with patch('app.api.v1.endpoints.content.ContentService') as mock_service:
            from app.schemas.content import ContentEditResponse
            mock_response = ContentEditResponse(
                id=uuid.uuid4(),
                generated_content_id=sample_content.id,
                iteration_number=1,
                edit_prompt="Make it more engaging",
                edit_type=EditType.GENERAL,
                previous_text="Original text",
                new_text="Edited text",
                diff_summary="Content expanded by 5 words",
                previous_word_count=100,
                new_word_count=105,
                word_count_change=5,
                previous_character_count=500,
                new_character_count=525,
                character_count_change=25,
                input_tokens=50,
                output_tokens=25,
                total_tokens=75,
                estimated_cost=0.005,
                model_used="gpt-4-turbo-preview",
                generation_time_seconds=1.5,
                status=ContentStatus.COMPLETED,
                edited_by_id=uuid.uuid4(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            mock_service.return_value.edit_content = AsyncMock(return_value=(
                True,
                "Success",
                mock_response
            ))
            
            response = client.post(
                f"/api/v1/organizations/{sample_organization.id}/content/{sample_content.id}/edit",
                json={
                    "edit_prompt": "Make it more engaging",
                    "edit_type": "general"
                },
                headers=auth_headers
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["iteration_number"] == 1


class TestContentUtils:
    """Test cases for content utility functions."""
    
    def test_calculate_content_metrics(self):
        """Test content metrics calculation."""
        from app.utils.content_utils import calculate_content_metrics
        
        text = "This is a test article. It has multiple sentences. Each sentence has different lengths."
        metrics = calculate_content_metrics(text)
        
        assert metrics.word_count > 0
        assert metrics.character_count > 0
        assert metrics.sentence_count >= 3
        assert metrics.paragraph_count >= 1
        assert metrics.reading_time_minutes >= 1
    
    def test_validate_content_text(self):
        """Test content text validation."""
        from app.utils.content_utils import validate_content_text
        
        # Valid text
        valid_text = "This is a valid article with enough content to pass validation."
        is_valid, error = validate_content_text(valid_text)
        assert is_valid is True
        assert error is None
        
        # Too short text
        short_text = "Short"
        is_valid, error = validate_content_text(short_text)
        assert is_valid is False
        assert "at least" in error
    
    def test_calculate_text_diff(self):
        """Test text diff calculation."""
        from app.utils.content_utils import calculate_text_diff
        
        original = "This is the original text."
        new = "This is the updated text with more content."
        
        diff = calculate_text_diff(original, new)
        
        assert diff["has_changes"] is True
        assert diff["word_count_change"] > 0
        assert diff["change_type"] == "expansion"
    
    def test_extract_content_keywords(self):
        """Test keyword extraction."""
        from app.utils.content_utils import extract_content_keywords
        
        text = "This article discusses artificial intelligence and machine learning technologies."
        keywords = extract_content_keywords(text)
        
        assert len(keywords) > 0
        assert "artificial" in keywords or "intelligence" in keywords
    
    def test_generate_content_summary(self):
        """Test content summary generation."""
        from app.utils.content_utils import generate_content_summary
        
        text = "This is a long article with multiple sentences. It contains important information about various topics. The summary should capture the main points."
        summary = generate_content_summary(text, max_length=50)
        
        assert len(summary) <= 50
        assert len(summary) > 0
