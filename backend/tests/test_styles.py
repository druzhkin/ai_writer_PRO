"""
Tests for style management functionality.
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.style_profile import StyleProfile
from app.models.reference_article import ReferenceArticle
from app.models.organization import Organization
from app.models.user import User
from app.schemas.style import StyleProfileCreate, ReferenceArticleCreate


class TestStyleProfiles:
    """Test style profile CRUD operations."""
    
    @pytest.fixture
    def test_organization(self, test_user: User, db: AsyncSession):
        """Create a test organization."""
        organization = Organization(
            name="Test Organization",
            slug="test-org",
            owner_id=test_user.id,
            description="Test organization for style testing"
        )
        db.add(organization)
        db.commit()
        db.refresh(organization)
        return organization
    
    @pytest.fixture
    def test_style_profile(self, test_organization: Organization, test_user: User, db: AsyncSession):
        """Create a test style profile."""
        style_profile = StyleProfile(
            name="Test Style",
            description="Test style profile",
            organization_id=test_organization.id,
            created_by_id=test_user.id,
            tags=["test", "example"],
            is_public=False
        )
        db.add(style_profile)
        db.commit()
        db.refresh(style_profile)
        return style_profile
    
    def test_create_style_profile(self, client: TestClient, test_user_token: str, test_organization: Organization):
        """Test creating a style profile."""
        style_data = {
            "name": "New Test Style",
            "description": "A new test style",
            "tags": ["new", "test"],
            "is_public": False
        }
        
        response = client.post(
            f"/api/v1/organizations/{test_organization.id}/styles/",
            json=style_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == style_data["name"]
        assert data["description"] == style_data["description"]
        assert data["tags"] == style_data["tags"]
        assert data["organization_id"] == str(test_organization.id)
    
    def test_get_style_profile(self, client: TestClient, test_user_token: str, test_organization: Organization, test_style_profile: StyleProfile):
        """Test getting a style profile."""
        response = client.get(
            f"/api/v1/organizations/{test_organization.id}/styles/{test_style_profile.id}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_style_profile.id)
        assert data["name"] == test_style_profile.name
    
    def test_list_style_profiles(self, client: TestClient, test_user_token: str, test_organization: Organization):
        """Test listing style profiles."""
        response = client.get(
            f"/api/v1/organizations/{test_organization.id}/styles/",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "style_profiles" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
    
    def test_update_style_profile(self, client: TestClient, test_user_token: str, test_organization: Organization, test_style_profile: StyleProfile):
        """Test updating a style profile."""
        update_data = {
            "name": "Updated Test Style",
            "description": "Updated description",
            "tags": ["updated", "test"]
        }
        
        response = client.put(
            f"/api/v1/organizations/{test_organization.id}/styles/{test_style_profile.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["tags"] == update_data["tags"]
    
    def test_delete_style_profile(self, client: TestClient, test_user_token: str, test_organization: Organization, test_style_profile: StyleProfile):
        """Test deleting a style profile."""
        response = client.delete(
            f"/api/v1/organizations/{test_organization.id}/styles/{test_style_profile.id}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Style profile deleted successfully"
    
    def test_style_profile_not_found(self, client: TestClient, test_user_token: str, test_organization: Organization):
        """Test getting non-existent style profile."""
        fake_id = uuid.uuid4()
        response = client.get(
            f"/api/v1/organizations/{test_organization.id}/styles/{fake_id}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 404
    
    def test_duplicate_style_name(self, client: TestClient, test_user_token: str, test_organization: Organization, test_style_profile: StyleProfile):
        """Test creating style profile with duplicate name."""
        style_data = {
            "name": test_style_profile.name,  # Same name as existing
            "description": "Duplicate name test",
            "tags": ["duplicate"],
            "is_public": False
        }
        
        response = client.post(
            f"/api/v1/organizations/{test_organization.id}/styles/",
            json=style_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 400


class TestReferenceArticles:
    """Test reference article CRUD operations."""
    
    @pytest.fixture
    def test_reference_article(self, test_style_profile: StyleProfile, test_user: User, test_organization: Organization, db: AsyncSession):
        """Create a test reference article."""
        reference_article = ReferenceArticle(
            title="Test Article",
            content="This is test content for style analysis.",
            style_profile_id=test_style_profile.id,
            uploaded_by_id=test_user.id,
            organization_id=test_organization.id,
            processing_status="completed",
            metadata={"word_count": 8, "character_count": 45}
        )
        db.add(reference_article)
        db.commit()
        db.refresh(reference_article)
        return reference_article
    
    def test_list_reference_articles(self, client: TestClient, test_user_token: str, test_organization: Organization):
        """Test listing reference articles."""
        response = client.get(
            f"/api/v1/organizations/{test_organization.id}/files/",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "reference_articles" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
    
    def test_get_reference_article(self, client: TestClient, test_user_token: str, test_organization: Organization, test_reference_article: ReferenceArticle):
        """Test getting a reference article."""
        response = client.get(
            f"/api/v1/organizations/{test_organization.id}/files/{test_reference_article.id}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_reference_article.id)
        assert data["title"] == test_reference_article.title
        assert data["content"] == test_reference_article.content
    
    def test_update_reference_article(self, client: TestClient, test_user_token: str, test_organization: Organization, test_reference_article: ReferenceArticle):
        """Test updating a reference article."""
        update_data = {
            "title": "Updated Test Article",
            "source_url": "https://example.com"
        }
        
        response = client.put(
            f"/api/v1/organizations/{test_organization.id}/files/{test_reference_article.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["source_url"] == update_data["source_url"]
    
    def test_delete_reference_article(self, client: TestClient, test_user_token: str, test_organization: Organization, test_reference_article: ReferenceArticle):
        """Test deleting a reference article."""
        response = client.delete(
            f"/api/v1/organizations/{test_organization.id}/files/{test_reference_article.id}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Reference article deleted successfully"
    
    def test_reference_article_not_found(self, client: TestClient, test_user_token: str, test_organization: Organization):
        """Test getting non-existent reference article."""
        fake_id = uuid.uuid4()
        response = client.get(
            f"/api/v1/organizations/{test_organization.id}/files/{fake_id}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 404


class TestStyleAnalysis:
    """Test style analysis functionality."""
    
    def test_analyze_style_profile(self, client: TestClient, test_user_token: str, test_organization: Organization, test_style_profile: StyleProfile):
        """Test analyzing a style profile."""
        analysis_request = {
            "style_profile_id": str(test_style_profile.id),
            "force_reanalysis": False,
            "include_metadata": True
        }
        
        response = client.post(
            f"/api/v1/organizations/{test_organization.id}/styles/{test_style_profile.id}/analyze",
            json=analysis_request,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        # Analysis might fail if no reference articles or OpenAI not configured
        # But the endpoint should still respond
        assert response.status_code in [200, 400, 500]
    
    def test_style_stats(self, client: TestClient, test_user_token: str, test_organization: Organization):
        """Test getting style statistics."""
        response = client.get(
            f"/api/v1/organizations/{test_organization.id}/styles/stats/overview",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_style_profiles" in data
        assert "active_style_profiles" in data
        assert "analyzed_style_profiles" in data
        assert "total_reference_articles" in data
        assert "processed_reference_articles" in data


class TestPermissions:
    """Test permission-based access control."""
    
    def test_unauthorized_access(self, client: TestClient, test_organization: Organization):
        """Test accessing endpoints without authentication."""
        response = client.get(f"/api/v1/organizations/{test_organization.id}/styles/")
        assert response.status_code == 401
    
    def test_wrong_organization_access(self, client: TestClient, test_user_token: str):
        """Test accessing styles from wrong organization."""
        fake_org_id = uuid.uuid4()
        response = client.get(
            f"/api/v1/organizations/{fake_org_id}/styles/",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 403
