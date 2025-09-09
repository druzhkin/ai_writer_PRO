"""
Comprehensive test suite for authentication endpoints and services.
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.services.auth_service import AuthService
from app.services.user_service import UserService


class TestUserRegistration:
    """Test user registration functionality."""
    
    async def test_register_new_user(self, client: TestClient, test_user_data):
        """Test successful user registration."""
        response = client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["username"] == test_user_data["username"]
        assert data["first_name"] == test_user_data["first_name"]
        assert data["last_name"] == test_user_data["last_name"]
        assert "id" in data
        assert data["is_active"] is True
        assert data["is_verified"] is False
        assert "password_hash" not in data
    
    async def test_register_duplicate_email(self, client: TestClient, test_user: User, test_user_data):
        """Test registration with duplicate email."""
        test_user_data["email"] = test_user.email
        response = client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    async def test_register_duplicate_username(self, client: TestClient, test_user: User, test_user_data):
        """Test registration with duplicate username."""
        test_user_data["username"] = test_user.username
        response = client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 400
        assert "already taken" in response.json()["detail"]
    
    async def test_register_weak_password(self, client: TestClient, test_user_data):
        """Test registration with weak password."""
        test_user_data["password"] = "123"
        response = client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 422  # Validation error
        assert "password" in str(response.json())
    
    async def test_register_invalid_email(self, client: TestClient, test_user_data):
        """Test registration with invalid email."""
        test_user_data["email"] = "invalid-email"
        response = client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 422  # Validation error


class TestUserLogin:
    """Test user login functionality."""
    
    async def test_login_success(self, client: TestClient, test_user: User, test_login_data):
        """Test successful user login."""
        response = client.post("/api/v1/auth/login", json=test_login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    async def test_login_invalid_email(self, client: TestClient, test_login_data):
        """Test login with invalid email."""
        test_login_data["email"] = "nonexistent@example.com"
        response = client.post("/api/v1/auth/login", json=test_login_data)
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    async def test_login_invalid_password(self, client: TestClient, test_user: User, test_login_data):
        """Test login with invalid password."""
        test_login_data["password"] = "wrongpassword"
        response = client.post("/api/v1/auth/login", json=test_login_data)
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    async def test_login_inactive_user(self, client: TestClient, db_session: AsyncSession, test_login_data):
        """Test login with inactive user."""
        # Create inactive user
        user = User(
            email=test_login_data["email"],
            username="inactiveuser",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.s.2a",
            is_active=False
        )
        db_session.add(user)
        await db_session.commit()
        
        response = client.post("/api/v1/auth/login", json=test_login_data)
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]


class TestTokenManagement:
    """Test JWT token management."""
    
    async def test_refresh_token_success(self, client: TestClient, test_user: User, auth_service: AuthService):
        """Test successful token refresh."""
        # Create tokens
        tokens = await auth_service.create_tokens(test_user)
        
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens.refresh_token})
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_refresh_token_invalid(self, client: TestClient):
        """Test token refresh with invalid token."""
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid_token"})
        
        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]
    
    async def test_access_protected_endpoint(self, client: TestClient, test_user: User, auth_service: AuthService):
        """Test accessing protected endpoint with valid token."""
        tokens = await auth_service.create_tokens(test_user)
        
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tokens.access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
    
    async def test_access_protected_endpoint_invalid_token(self, client: TestClient):
        """Test accessing protected endpoint with invalid token."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]
    
    async def test_access_protected_endpoint_no_token(self, client: TestClient):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 403  # No authorization header


class TestPasswordReset:
    """Test password reset functionality."""
    
    async def test_forgot_password_success(self, client: TestClient, test_user: User):
        """Test successful password reset request."""
        response = client.post("/api/v1/auth/forgot-password", json={"email": test_user.email})
        
        assert response.status_code == 200
        assert "password reset link has been sent" in response.json()["message"]
    
    async def test_forgot_password_nonexistent_email(self, client: TestClient):
        """Test password reset request with nonexistent email."""
        response = client.post("/api/v1/auth/forgot-password", json={"email": "nonexistent@example.com"})
        
        # Should still return success to prevent email enumeration
        assert response.status_code == 200
        assert "password reset link has been sent" in response.json()["message"]
    
    async def test_reset_password_success(self, client: TestClient, test_user: User, auth_service: AuthService):
        """Test successful password reset."""
        # Generate reset token
        reset_token = await auth_service.generate_password_reset_token(test_user)
        
        response = client.post("/api/v1/auth/reset-password", json={
            "token": reset_token,
            "new_password": "newpassword123"
        })
        
        assert response.status_code == 200
        assert "Password reset successfully" in response.json()["message"]
    
    async def test_reset_password_invalid_token(self, client: TestClient):
        """Test password reset with invalid token."""
        response = client.post("/api/v1/auth/reset-password", json={
            "token": "invalid_token",
            "new_password": "newpassword123"
        })
        
        assert response.status_code == 400
        assert "Invalid or expired reset token" in response.json()["detail"]


class TestEmailVerification:
    """Test email verification functionality."""
    
    async def test_verify_email_success(self, client: TestClient, test_user: User, auth_service: AuthService):
        """Test successful email verification."""
        # Generate verification token
        verification_token = await auth_service.generate_email_verification_token(test_user)
        
        response = client.post("/api/v1/auth/verify-email", json={"token": verification_token})
        
        assert response.status_code == 200
        assert "Email verified successfully" in response.json()["message"]
    
    async def test_verify_email_invalid_token(self, client: TestClient):
        """Test email verification with invalid token."""
        response = client.post("/api/v1/auth/verify-email", json={"token": "invalid_token"})
        
        assert response.status_code == 400
        assert "Invalid or expired verification token" in response.json()["detail"]
    
    async def test_resend_verification_email(self, client: TestClient, test_user: User, auth_service: AuthService):
        """Test resending verification email."""
        # Create tokens for authenticated request
        tokens = await auth_service.create_tokens(test_user)
        
        response = client.post(
            "/api/v1/auth/resend-verification",
            headers={"Authorization": f"Bearer {tokens.access_token}"}
        )
        
        assert response.status_code == 200
        assert "Verification email sent" in response.json()["message"]


class TestPasswordChange:
    """Test password change functionality."""
    
    async def test_change_password_success(self, client: TestClient, test_user: User, auth_service: AuthService):
        """Test successful password change."""
        tokens = await auth_service.create_tokens(test_user)
        
        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "password123",
                "new_password": "newpassword123"
            },
            headers={"Authorization": f"Bearer {tokens.access_token}"}
        )
        
        assert response.status_code == 200
        assert "Password changed successfully" in response.json()["message"]
    
    async def test_change_password_wrong_current(self, client: TestClient, test_user: User, auth_service: AuthService):
        """Test password change with wrong current password."""
        tokens = await auth_service.create_tokens(test_user)
        
        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "wrongpassword",
                "new_password": "newpassword123"
            },
            headers={"Authorization": f"Bearer {tokens.access_token}"}
        )
        
        assert response.status_code == 400
        assert "Current password is incorrect" in response.json()["detail"]


class TestUserProfile:
    """Test user profile management."""
    
    async def test_get_my_profile(self, client: TestClient, test_user: User, auth_service: AuthService):
        """Test getting current user profile."""
        tokens = await auth_service.create_tokens(test_user)
        
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {tokens.access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
        assert "organizations" in data
    
    async def test_update_my_profile(self, client: TestClient, test_user: User, auth_service: AuthService):
        """Test updating current user profile."""
        tokens = await auth_service.create_tokens(test_user)
        
        update_data = {
            "first_name": "Updated",
            "last_name": "Name"
        }
        
        response = client.put(
            "/api/v1/users/me",
            json=update_data,
            headers={"Authorization": f"Bearer {tokens.access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"
    
    async def test_update_username_duplicate(self, client: TestClient, test_user: User, db_session: AsyncSession, auth_service: AuthService):
        """Test updating username to duplicate."""
        # Create another user
        other_user = User(
            email="other@example.com",
            username="otheruser",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.s.2a"
        )
        db_session.add(other_user)
        await db_session.commit()
        
        tokens = await auth_service.create_tokens(test_user)
        
        update_data = {"username": "otheruser"}
        
        response = client.put(
            "/api/v1/users/me",
            json=update_data,
            headers={"Authorization": f"Bearer {tokens.access_token}"}
        )
        
        assert response.status_code == 400
        assert "Username already taken" in response.json()["detail"]


class TestOrganizationManagement:
    """Test organization management functionality."""
    
    async def test_create_organization(self, client: TestClient, test_user: User, auth_service: AuthService, test_organization_data):
        """Test creating a new organization."""
        tokens = await auth_service.create_tokens(test_user)
        
        response = client.post(
            "/api/v1/organizations/",
            json=test_organization_data,
            headers={"Authorization": f"Bearer {tokens.access_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == test_organization_data["name"]
        assert data["description"] == test_organization_data["description"]
        assert data["owner_id"] == str(test_user.id)
    
    async def test_get_my_organizations(self, client: TestClient, test_user: User, test_organization: Organization, auth_service: AuthService):
        """Test getting user's organizations."""
        tokens = await auth_service.create_tokens(test_user)
        
        response = client.get(
            "/api/v1/organizations/",
            headers={"Authorization": f"Bearer {tokens.access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == test_organization.name
    
    async def test_get_organization_by_id(self, client: TestClient, test_user: User, test_organization: Organization, auth_service: AuthService):
        """Test getting organization by ID."""
        tokens = await auth_service.create_tokens(test_user)
        
        response = client.get(
            f"/api/v1/organizations/{test_organization.id}",
            headers={"Authorization": f"Bearer {tokens.access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == test_organization.name
        assert data["id"] == str(test_organization.id)
    
    async def test_update_organization(self, client: TestClient, test_user: User, test_organization: Organization, auth_service: AuthService):
        """Test updating organization."""
        tokens = await auth_service.create_tokens(test_user)
        
        update_data = {
            "name": "Updated Organization",
            "description": "Updated description"
        }
        
        response = client.put(
            f"/api/v1/organizations/{test_organization.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {tokens.access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Organization"
        assert data["description"] == "Updated description"


class TestOrganizationInvitations:
    """Test organization invitation functionality."""
    
    async def test_invite_user_to_organization(self, client: TestClient, test_user: User, test_organization: Organization, auth_service: AuthService, test_invitation_data):
        """Test inviting user to organization."""
        tokens = await auth_service.create_tokens(test_user)
        
        response = client.post(
            f"/api/v1/organizations/{test_organization.id}/invite",
            json=test_invitation_data,
            headers={"Authorization": f"Bearer {tokens.access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_invitation_data["email"]
        assert data["role"] == test_invitation_data["role"]
        assert data["organization_id"] == str(test_organization.id)
    
    async def test_accept_organization_invitation(self, client: TestClient, test_user: User, test_organization: Organization, user_service: UserService):
        """Test accepting organization invitation."""
        # Create invitation
        membership = await user_service.invite_user_to_organization(
            test_organization, test_user, "invited@example.com", "editor"
        )
        
        response = client.post("/api/v1/organizations/invite/accept", json={
            "token": membership.invitation_token,
            "password": "password123"
        })
        
        assert response.status_code == 200
        assert "Invitation accepted successfully" in response.json()["message"]
    
    async def test_accept_invitation_invalid_token(self, client: TestClient):
        """Test accepting invitation with invalid token."""
        response = client.post("/api/v1/organizations/invite/accept", json={
            "token": "invalid_token",
            "password": "password123"
        })
        
        assert response.status_code == 400
        assert "Invalid or expired invitation token" in response.json()["detail"]


class TestAdminEndpoints:
    """Test admin-only endpoints."""
    
    async def test_search_users_admin(self, client: TestClient, admin_user: User, auth_service: AuthService):
        """Test searching users as admin."""
        tokens = await auth_service.create_tokens(admin_user)
        
        response = client.get(
            "/api/v1/users/?query=test",
            headers={"Authorization": f"Bearer {tokens.access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
    
    async def test_search_users_non_admin(self, client: TestClient, test_user: User, auth_service: AuthService):
        """Test searching users as non-admin (should fail)."""
        tokens = await auth_service.create_tokens(test_user)
        
        response = client.get(
            "/api/v1/users/?query=test",
            headers={"Authorization": f"Bearer {tokens.access_token}"}
        )
        
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]
    
    async def test_get_user_by_id_admin(self, client: TestClient, admin_user: User, test_user: User, auth_service: AuthService):
        """Test getting user by ID as admin."""
        tokens = await auth_service.create_tokens(admin_user)
        
        response = client.get(
            f"/api/v1/users/{test_user.id}",
            headers={"Authorization": f"Bearer {tokens.access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
    
    async def test_bulk_user_action_admin(self, client: TestClient, admin_user: User, test_user: User, auth_service: AuthService):
        """Test bulk user action as admin."""
        tokens = await auth_service.create_tokens(admin_user)
        
        response = client.post(
            "/api/v1/users/bulk-action",
            json={
                "user_ids": [str(test_user.id)],
                "action": "deactivate"
            },
            headers={"Authorization": f"Bearer {tokens.access_token}"}
        )
        
        assert response.status_code == 200
        assert "Bulk action 'deactivate' completed" in response.json()["message"]


class TestOAuthEndpoints:
    """Test OAuth endpoints."""
    
    async def test_get_oauth_providers(self, client: TestClient, mock_oauth_provider):
        """Test getting configured OAuth providers."""
        response = client.get("/api/v1/oauth/providers")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    async def test_oauth_login_redirect(self, client: TestClient, mock_oauth_provider):
        """Test OAuth login redirect."""
        response = client.get("/api/v1/oauth/google/login")
        
        # Should redirect to OAuth provider
        assert response.status_code in [302, 307]  # Redirect status codes
    
    async def test_oauth_login_post(self, client: TestClient, mock_oauth_provider):
        """Test OAuth login via POST."""
        response = client.post("/api/v1/oauth/google/login", json={
            "provider": "google",
            "redirect_uri": "http://localhost:3000/callback"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "state" in data
    
    async def test_oauth_callback_post(self, client: TestClient, mock_oauth_provider):
        """Test OAuth callback via POST."""
        # First, initiate OAuth flow to set session state
        login_response = client.post("/api/v1/oauth/google/login", json={
            "provider": "google",
            "redirect_uri": "http://localhost:3000/callback"
        })
        
        assert login_response.status_code == 200
        login_data = login_response.json()
        state = login_data["state"]
        
        # Now test callback
        response = client.post("/api/v1/oauth/callback", json={
            "code": "mock_auth_code",
            "state": state,
            "provider": "google"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    async def test_invalid_json_request(self, client: TestClient):
        """Test request with invalid JSON."""
        response = client.post(
            "/api/v1/auth/register",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    async def test_missing_required_fields(self, client: TestClient):
        """Test request with missing required fields."""
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com"
            # Missing username, password, etc.
        })
        
        assert response.status_code == 422
    
    async def test_unauthorized_access(self, client: TestClient):
        """Test accessing protected endpoint without authentication."""
        response = client.get("/api/v1/users/me")
        
        assert response.status_code == 403
    
    async def test_nonexistent_endpoint(self, client: TestClient):
        """Test accessing nonexistent endpoint."""
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404
