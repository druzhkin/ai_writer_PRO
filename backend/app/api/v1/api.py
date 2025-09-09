"""
API v1 router configuration.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, oauth, users, organizations, styles, files, content, usage

api_router = APIRouter()

# Include health check endpoint
api_router.include_router(health.router, prefix="/health", tags=["health"])

# Include authentication endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(oauth.router, prefix="/oauth", tags=["oauth"])

# Include user management endpoints
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])

# Include style and file management endpoints
api_router.include_router(styles.router, prefix="/organizations/{organization_id}/styles", tags=["styles"])
api_router.include_router(files.router, prefix="/organizations/{organization_id}/files", tags=["files"])

# Include content generation and usage analytics endpoints
api_router.include_router(content.router, prefix="/organizations/{organization_id}/content", tags=["content"])
api_router.include_router(usage.router, prefix="/organizations/{organization_id}/usage", tags=["usage"])
