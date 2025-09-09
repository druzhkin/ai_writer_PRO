"""
Database initialization script for creating initial admin user and system setup.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.services.auth_service import AuthService
from app.schemas.auth import UserCreate, UserRole

logger = structlog.get_logger()


async def create_default_admin_user():
    """Create default admin user if none exists."""
    try:
        async for db in get_db():
            # Check if admin user already exists
            result = await db.execute(select(User).where(User.is_superuser == True))
            admin_user = result.scalar_one_or_none()
            
            if admin_user:
                logger.info("Admin user already exists", email=admin_user.email)
                return admin_user
            
            # Create default admin user
            auth_service = AuthService(db)
            
            admin_data = UserCreate(
                email="admin@aiwriter.com",
                username="admin",
                password="admin123456",
                first_name="Admin",
                last_name="User",
                organization_name="AI Writer Admin Organization"
            )
            
            try:
                user, organization = await auth_service.create_user(admin_data)
                user.is_superuser = True
                user.is_verified = True
                await db.commit()
                
                logger.info("Default admin user created successfully", 
                           email=user.email, 
                           user_id=str(user.id),
                           org_id=str(organization.id))
                
                return user
                
            except Exception as e:
                logger.error("Failed to create admin user", error=str(e))
                await db.rollback()
                raise
            
            break  # Exit the async generator
            
    except Exception as e:
        logger.error("Error in create_default_admin_user", error=str(e))
        raise


async def create_demo_users():
    """Create demo users for testing."""
    try:
        async for db in get_db():
            auth_service = AuthService(db)
            
            # Demo users data
            demo_users = [
                {
                    "email": "demo@aiwriter.com",
                    "username": "demo",
                    "password": "demo123456",
                    "first_name": "Demo",
                    "last_name": "User",
                    "organization_name": "Demo Organization"
                },
                {
                    "email": "editor@aiwriter.com",
                    "username": "editor",
                    "password": "editor123456",
                    "first_name": "Editor",
                    "last_name": "User",
                    "organization_name": "Editor Organization"
                },
                {
                    "email": "viewer@aiwriter.com",
                    "username": "viewer",
                    "password": "viewer123456",
                    "first_name": "Viewer",
                    "last_name": "User",
                    "organization_name": "Viewer Organization"
                }
            ]
            
            created_users = []
            
            for user_data in demo_users:
                try:
                    # Check if user already exists
                    existing_user = await auth_service.get_user_by_email(user_data["email"])
                    if existing_user:
                        logger.info("Demo user already exists", email=user_data["email"])
                        created_users.append(existing_user)
                        continue
                    
                    # Create user
                    user_create = UserCreate(**user_data)
                    user, organization = await auth_service.create_user(user_create)
                    user.is_verified = True  # Auto-verify demo users
                    await db.commit()
                    
                    created_users.append(user)
                    logger.info("Demo user created", 
                               email=user.email, 
                               user_id=str(user.id),
                               org_id=str(organization.id))
                    
                except Exception as e:
                    logger.error("Failed to create demo user", 
                               email=user_data["email"], 
                               error=str(e))
                    await db.rollback()
                    continue
            
            logger.info("Demo users creation completed", count=len(created_users))
            return created_users
            
            break  # Exit the async generator
            
    except Exception as e:
        logger.error("Error in create_demo_users", error=str(e))
        raise


async def setup_organization_memberships():
    """Setup organization memberships for demo users."""
    try:
        async for db in get_db():
            # Get demo users
            result = await db.execute(select(User).where(User.email.in_([
                "demo@aiwriter.com",
                "editor@aiwriter.com", 
                "viewer@aiwriter.com"
            ])))
            demo_users = result.scalars().all()
            
            if not demo_users:
                logger.info("No demo users found for membership setup")
                return
            
            # Get admin user's organization
            admin_result = await db.execute(select(User).where(User.email == "admin@aiwriter.com"))
            admin_user = admin_result.scalar_one_or_none()
            
            if not admin_user:
                logger.warning("Admin user not found for membership setup")
                return
            
            # Get admin's organization
            org_result = await db.execute(
                select(Organization).where(Organization.owner_id == admin_user.id)
            )
            admin_org = org_result.scalar_one_or_none()
            
            if not admin_org:
                logger.warning("Admin organization not found")
                return
            
            # Create memberships
            role_mapping = {
                "demo@aiwriter.com": UserRole.ADMIN,
                "editor@aiwriter.com": UserRole.EDITOR,
                "viewer@aiwriter.com": UserRole.VIEWER
            }
            
            for user in demo_users:
                # Check if membership already exists
                existing_membership = await db.execute(
                    select(OrganizationMember).where(
                        OrganizationMember.user_id == user.id,
                        OrganizationMember.organization_id == admin_org.id
                    )
                )
                if existing_membership.scalar_one_or_none():
                    logger.info("Membership already exists", 
                               user_email=user.email, 
                               org_name=admin_org.name)
                    continue
                
                # Create membership
                membership = OrganizationMember(
                    user_id=user.id,
                    organization_id=admin_org.id,
                    role=role_mapping.get(user.email, UserRole.VIEWER),
                    invited_by_id=admin_user.id,
                    is_active="active"
                )
                
                db.add(membership)
                await db.commit()
                
                logger.info("Organization membership created", 
                           user_email=user.email,
                           org_name=admin_org.name,
                           role=membership.role)
            
            logger.info("Organization memberships setup completed")
            
            break  # Exit the async generator
            
    except Exception as e:
        logger.error("Error in setup_organization_memberships", error=str(e))
        raise


async def initialize_database():
    """Initialize database with default data."""
    logger.info("Starting database initialization")
    
    try:
        # Create default admin user
        await create_default_admin_user()
        
        # Create demo users
        await create_demo_users()
        
        # Setup organization memberships
        await setup_organization_memberships()
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        raise


async def main():
    """Main function to run database initialization."""
    try:
        await initialize_database()
        print("✅ Database initialization completed successfully!")
        print("\nDefault users created:")
        print("  Admin: admin@aiwriter.com / admin123456")
        print("  Demo:  demo@aiwriter.com / demo123456")
        print("  Editor: editor@aiwriter.com / editor123456")
        print("  Viewer: viewer@aiwriter.com / viewer123456")
        print("\nYou can now start the application and login with any of these accounts.")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
