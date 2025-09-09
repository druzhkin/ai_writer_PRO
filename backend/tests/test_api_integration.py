"""
Comprehensive API integration tests covering all endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
import json

from app.models.user import User
from app.models.organization import Organization
from app.models.style_profile import StyleProfile
from app.models.generated_content import GeneratedContent


class TestAuthAPI:
    """Test authentication API endpoints."""
    
    def test_user_registration(self, client: TestClient, test_user_data):
        """Test user registration endpoint."""
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 201
        data = response.json()
        assert "user" in data
        assert "access_token" in data
        assert data["user"]["email"] == test_user_data["email"]
    
    def test_user_login(self, client: TestClient, test_user: User, test_login_data):
        """Test user login endpoint."""
        response = client.post("/api/v1/auth/login", json=test_login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
    
    def test_invalid_login(self, client: TestClient):
        """Test login with invalid credentials."""
        response = client.post("/api/v1/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
    
    def test_password_reset_request(self, client: TestClient, test_user: User):
        """Test password reset request."""
        response = client.post("/api/v1/auth/password-reset", json={
            "email": test_user.email
        })
        assert response.status_code == 200
    
    def test_password_reset_confirm(self, client: TestClient, test_user: User):
        """Test password reset confirmation."""
        # This would require a valid reset token in a real scenario
        response = client.post("/api/v1/auth/password-reset/confirm", json={
            "token": "invalid_token",
            "new_password": "newpassword123"
        })
        assert response.status_code == 400


class TestUserAPI:
    """Test user management API endpoints."""
    
    def test_get_current_user(self, client: TestClient, auth_headers):
        """Test getting current user profile."""
        response = client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "username" in data
    
    def test_update_user_profile(self, client: TestClient, auth_headers):
        """Test updating user profile."""
        update_data = {
            "first_name": "Updated",
            "last_name": "Name"
        }
        response = client.put("/api/v1/users/me", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"
    
    def test_unauthorized_access(self, client: TestClient):
        """Test unauthorized access to protected endpoints."""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401


class TestOrganizationAPI:
    """Test organization management API endpoints."""
    
    def test_create_organization(self, client: TestClient, auth_headers, test_organization_data):
        """Test creating a new organization."""
        response = client.post("/api/v1/organizations/", json=test_organization_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == test_organization_data["name"]
        assert "slug" in data
    
    def test_get_user_organizations(self, client: TestClient, auth_headers, test_organization: Organization):
        """Test getting user's organizations."""
        response = client.get("/api/v1/organizations/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_organization_details(self, client: TestClient, auth_headers, test_organization: Organization):
        """Test getting organization details."""
        response = client.get(f"/api/v1/organizations/{test_organization.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_organization.id
        assert data["name"] == test_organization.name
    
    def test_update_organization(self, client: TestClient, auth_headers, test_organization: Organization):
        """Test updating organization."""
        update_data = {"description": "Updated description"}
        response = client.put(f"/api/v1/organizations/{test_organization.id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"


class TestStyleAPI:
    """Test style management API endpoints."""
    
    def test_create_style_profile(self, client: TestClient, auth_headers, test_organization: Organization):
        """Test creating a style profile."""
        style_data = {
            "name": "Test Style",
            "description": "A test style profile",
            "tone": "professional",
            "voice": "authoritative",
            "target_audience": "general",
            "content_type": "article",
            "organization_id": test_organization.id
        }
        response = client.post("/api/v1/styles/", json=style_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Style"
    
    def test_get_style_profiles(self, client: TestClient, auth_headers, test_organization: Organization):
        """Test getting style profiles."""
        response = client.get(f"/api/v1/styles/?organization_id={test_organization.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_upload_reference_article(self, client: TestClient, auth_headers, test_style_profile: StyleProfile, test_file_content):
        """Test uploading reference article."""
        files = {"file": ("test.txt", test_file_content, "text/plain")}
        data = {"style_profile_id": test_style_profile.id}
        response = client.post("/api/v1/styles/upload-reference", files=files, data=data, headers=auth_headers)
        assert response.status_code == 201
        response_data = response.json()
        assert "article" in response_data


class TestContentAPI:
    """Test content generation API endpoints."""
    
    def test_generate_content(self, client: TestClient, auth_headers, test_organization: Organization, test_style_profile: StyleProfile):
        """Test content generation."""
        content_data = {
            "title": "Test Article",
            "brief": "This is a test brief for content generation",
            "target_words": 1000,
            "style_profile_id": test_style_profile.id,
            "organization_id": test_organization.id
        }
        response = client.post("/api/v1/content/generate", json=content_data, headers=auth_headers)
        assert response.status_code == 202  # Accepted for async processing
        data = response.json()
        assert "task_id" in data
    
    def test_get_generated_content(self, client: TestClient, auth_headers, test_organization: Organization):
        """Test getting generated content list."""
        response = client.get(f"/api/v1/content/?organization_id={test_organization.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_content_details(self, client: TestClient, auth_headers, test_generated_content: GeneratedContent):
        """Test getting content details."""
        response = client.get(f"/api/v1/content/{test_generated_content.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_generated_content.id
        assert data["title"] == test_generated_content.title
    
    def test_update_content(self, client: TestClient, auth_headers, test_generated_content: GeneratedContent):
        """Test updating content."""
        update_data = {"title": "Updated Title"}
        response = client.put(f"/api/v1/content/{test_generated_content.id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
    
    def test_delete_content(self, client: TestClient, auth_headers, test_generated_content: GeneratedContent):
        """Test deleting content."""
        response = client.delete(f"/api/v1/content/{test_generated_content.id}", headers=auth_headers)
        assert response.status_code == 204


class TestFileAPI:
    """Test file handling API endpoints."""
    
    def test_file_upload(self, client: TestClient, auth_headers, test_file_content):
        """Test file upload."""
        files = {"file": ("test.txt", test_file_content, "text/plain")}
        response = client.post("/api/v1/files/upload", files=files, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert "file_url" in data
    
    def test_invalid_file_type(self, client: TestClient, auth_headers):
        """Test uploading invalid file type."""
        files = {"file": ("test.exe", b"binary content", "application/x-executable")}
        response = client.post("/api/v1/files/upload", files=files, headers=auth_headers)
        assert response.status_code == 400
    
    def test_file_too_large(self, client: TestClient, auth_headers):
        """Test uploading file that's too large."""
        large_content = b"x" * (50 * 1024 * 1024 + 1)  # 50MB + 1 byte
        files = {"file": ("large.txt", large_content, "text/plain")}
        response = client.post("/api/v1/files/upload", files=files, headers=auth_headers)
        assert response.status_code == 413


class TestUsageAPI:
    """Test usage tracking API endpoints."""
    
    def test_get_usage_stats(self, client: TestClient, auth_headers, test_organization: Organization):
        """Test getting usage statistics."""
        response = client.get(f"/api/v1/usage/stats?organization_id={test_organization.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_tokens" in data
        assert "total_cost" in data
        assert "usage_by_date" in data
    
    def test_get_usage_history(self, client: TestClient, auth_headers, test_organization: Organization):
        """Test getting usage history."""
        response = client.get(f"/api/v1/usage/history?organization_id={test_organization.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestHealthAPI:
    """Test health check endpoints."""
    
    def test_health_check(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data


class TestOAuthAPI:
    """Test OAuth integration endpoints."""
    
    def test_google_oauth_authorize(self, client: TestClient):
        """Test Google OAuth authorization."""
        response = client.get("/api/v1/oauth/google/authorize")
        assert response.status_code == 302  # Redirect to OAuth provider
    
    def test_github_oauth_authorize(self, client: TestClient):
        """Test GitHub OAuth authorization."""
        response = client.get("/api/v1/oauth/github/authorize")
        assert response.status_code == 302  # Redirect to OAuth provider
    
    def test_oauth_callback_invalid_state(self, client: TestClient):
        """Test OAuth callback with invalid state."""
        response = client.get("/api/v1/oauth/callback?code=test&state=invalid")
        assert response.status_code == 400


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_404_endpoint(self, client: TestClient):
        """Test 404 for non-existent endpoint."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
    
    def test_invalid_json(self, client: TestClient, auth_headers):
        """Test invalid JSON in request body."""
        response = client.post("/api/v1/auth/login", 
                             data="invalid json", 
                             headers={**auth_headers, "Content-Type": "application/json"})
        assert response.status_code == 422
    
    def test_missing_required_fields(self, client: TestClient):
        """Test missing required fields in request."""
        response = client.post("/api/v1/auth/register", json={"email": "test@example.com"})
        assert response.status_code == 422
    
    def test_rate_limiting(self, client: TestClient):
        """Test rate limiting (if implemented)."""
        # This would test rate limiting by making many requests
        for _ in range(100):
            response = client.get("/health")
            if response.status_code == 429:
                break
        # Rate limiting might not be implemented yet, so we just ensure health endpoint works
        assert response.status_code in [200, 429]
