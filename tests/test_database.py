"""
Unit tests for database module
"""

import pytest
import sys
import tempfile
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.database import Database


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    db = Database(db_path)
    yield db

    # Cleanup
    db.close()
    os.unlink(db_path)


class TestDatabaseConnection:
    """Test database connection and basic operations"""

    def test_database_creation(self, temp_db):
        """Test database is created successfully"""
        assert temp_db is not None
        assert temp_db.conn is not None

    def test_execute_query(self, temp_db):
        """Test executing a simple query"""
        temp_db.execute_query("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)

        # Check table exists
        result = temp_db.fetch_one("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='test_table'
        """)

        assert result is not None
        assert result['name'] == 'test_table'


class TestUserOperations:
    """Test user-related database operations"""

    def test_create_user(self, temp_db):
        """Test creating a new user"""
        user_id = temp_db.create_user(
            email="test@example.com",
            password_hash="hashed_password",
            username="testuser"
        )

        assert user_id is not None
        assert user_id > 0

    def test_get_user_by_email(self, temp_db):
        """Test retrieving user by email"""
        # Create user
        email = "test@example.com"
        temp_db.create_user(
            email=email,
            password_hash="hashed_password",
            username="testuser"
        )

        # Retrieve user
        user = temp_db.get_user_by_email(email)

        assert user is not None
        assert user['email'] == email
        assert user['username'] == "testuser"

    def test_get_user_by_email_not_found(self, temp_db):
        """Test retrieving non-existent user"""
        user = temp_db.get_user_by_email("nonexistent@example.com")
        assert user is None

    def test_duplicate_email(self, temp_db):
        """Test that duplicate emails are rejected"""
        email = "test@example.com"

        # Create first user
        user_id1 = temp_db.create_user(
            email=email,
            password_hash="hash1",
            username="user1"
        )

        # Try to create second user with same email
        user_id2 = temp_db.create_user(
            email=email,
            password_hash="hash2",
            username="user2"
        )

        assert user_id1 is not None
        assert user_id2 is None  # Should fail due to unique constraint


class TestCacheOperations:
    """Test cache-related operations"""

    def test_cache_response(self, temp_db):
        """Test caching a response"""
        success = temp_db.cache_response(
            prompt="Test prompt",
            response="Test response",
            model="test-model",
            task_type="test"
        )

        assert success == True

    def test_get_cached_response(self, temp_db):
        """Test retrieving cached response"""
        prompt = "Test prompt"
        response = "Test response"
        task_type = "test"

        # Cache response
        temp_db.cache_response(
            prompt=prompt,
            response=response,
            model="test-model",
            task_type=task_type
        )

        # Retrieve cached response
        cached = temp_db.get_cached_response(prompt, task_type)

        assert cached is not None
        assert cached['response'] == response
        assert cached['model'] == "test-model"

    def test_get_cached_response_not_found(self, temp_db):
        """Test retrieving non-existent cached response"""
        cached = temp_db.get_cached_response("nonexistent", "test")
        assert cached is None

    def test_cache_expiry(self, temp_db):
        """Test that expired cache entries are not returned"""
        prompt = "Test prompt"

        # Cache with 0 hours TTL (immediate expiry)
        temp_db.cache_response(
            prompt=prompt,
            response="Test response",
            model="test-model",
            task_type="test",
            ttl_hours=0
        )

        # Try to retrieve - should be expired
        cached = temp_db.get_cached_response(prompt, "test")
        assert cached is None


class TestSessionOperations:
    """Test session-related operations"""

    def test_create_session(self, temp_db):
        """Test creating a new session"""
        # First create a user
        user_id = temp_db.create_user(
            email="test@example.com",
            password_hash="hash",
            username="test"
        )

        # Create session
        session = temp_db.create_session(user_id)

        assert session is not None
        assert 'session_id' in session
        assert 'expires_at' in session

    def test_get_session(self, temp_db):
        """Test retrieving a session"""
        # Create user and session
        user_id = temp_db.create_user(
            email="test@example.com",
            password_hash="hash",
            username="test"
        )
        session = temp_db.create_session(user_id)

        # Retrieve session
        retrieved = temp_db.get_session(session['session_id'])

        assert retrieved is not None
        assert retrieved['user_id'] == user_id

    def test_delete_session(self, temp_db):
        """Test deleting a session"""
        # Create user and session
        user_id = temp_db.create_user(
            email="test@example.com",
            password_hash="hash",
            username="test"
        )
        session = temp_db.create_session(user_id)

        # Delete session
        temp_db.delete_session(session['session_id'])

        # Try to retrieve - should be None
        retrieved = temp_db.get_session(session['session_id'])
        assert retrieved is None


class TestHistoryOperations:
    """Test history tracking operations"""

    def test_add_history(self, temp_db):
        """Test adding history entry"""
        temp_db.add_history(
            prompt="Test prompt",
            response="Test response",
            model="test-model",
            tokens=100,
            cost=0.01
        )

        # Retrieve history
        history = temp_db.get_history(limit=1)

        assert len(history) == 1
        assert history[0]['prompt'] == "Test prompt"
        assert history[0]['response'] == "Test response"
        assert history[0]['model'] == "test-model"
        assert history[0]['tokens'] == 100
        assert history[0]['cost'] == 0.01

    def test_get_history_limit(self, temp_db):
        """Test history limit"""
        # Add multiple entries
        for i in range(10):
            temp_db.add_history(
                prompt=f"Prompt {i}",
                response=f"Response {i}",
                model="test-model",
                tokens=100,
                cost=0.01
            )

        # Get limited history
        history = temp_db.get_history(limit=5)

        assert len(history) == 5

    def test_get_history_offset(self, temp_db):
        """Test history offset"""
        # Add multiple entries
        for i in range(10):
            temp_db.add_history(
                prompt=f"Prompt {i}",
                response=f"Response {i}",
                model="test-model",
                tokens=100,
                cost=0.01
            )

        # Get history with offset
        history = temp_db.get_history(limit=5, offset=5)

        assert len(history) == 5
        # Should get older entries due to offset


if __name__ == "__main__":
    pytest.main([__file__, "-v"])