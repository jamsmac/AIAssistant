"""
Database operations tests
"""
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import User, Project, WorkflowTemplate


class TestUserModel:
    """Test User model operations"""

    @pytest.mark.asyncio
    async def test_create_user(self, test_session: AsyncSession):
        """Test user creation"""
        user = User(
            email="newuser@example.com",
            hashed_password="hashed_pwd",
            is_active=True
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        assert user.id is not None
        assert user.email == "newuser@example.com"

    @pytest.mark.asyncio
    async def test_query_user(self, test_session: AsyncSession, test_user):
        """Test querying user"""
        result = await test_session.execute(
            select(User).where(User.email == test_user.email)
        )
        user = result.scalar_one()

        assert user.id == test_user.id

    @pytest.mark.asyncio
    async def test_update_user(self, test_session: AsyncSession, test_user):
        """Test updating user"""
        test_user.is_verified = True
        await test_session.commit()
        await test_session.refresh(test_user)

        assert test_user.is_verified is True


class TestProjectModel:
    """Test Project model operations"""

    @pytest.mark.asyncio
    async def test_create_project(self, test_session: AsyncSession, test_user):
        """Test project creation"""
        project = Project(
            name="Test Project",
            description="Description",
            user_id=test_user.id
        )
        test_session.add(project)
        await test_session.commit()
        await test_session.refresh(project)

        assert project.id is not None
        assert project.name == "Test Project"
