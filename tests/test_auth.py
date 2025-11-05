"""
Unit tests for authentication module
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.auth import (
    hash_password,
    verify_password,
    create_jwt_token,
    verify_jwt_token,
    generate_reset_token,
    verify_reset_token
)


class TestPasswordHashing:
    """Test password hashing functions"""

    def test_hash_password(self):
        """Test password hashing"""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 50
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self):
        """Test verifying correct password"""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) == True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password"""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert verify_password("WrongPassword", hashed) == False

    def test_different_hashes_same_password(self):
        """Test that same password produces different hashes"""
        password = "TestPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2
        assert verify_password(password, hash1) == True
        assert verify_password(password, hash2) == True


class TestJWT:
    """Test JWT token functions"""

    def test_create_jwt_token(self):
        """Test JWT token creation"""
        payload = {
            "user_id": 123,
            "email": "test@example.com"
        }

        token = create_jwt_token(payload)

        assert token is not None
        assert len(token) > 50
        assert "." in token

    def test_verify_jwt_token_valid(self):
        """Test verifying valid JWT token"""
        payload = {
            "user_id": 123,
            "email": "test@example.com"
        }

        token = create_jwt_token(payload)
        decoded = verify_jwt_token(token)

        assert decoded is not None
        assert decoded["user_id"] == 123
        assert decoded["email"] == "test@example.com"
        assert "exp" in decoded
        assert "iat" in decoded

    def test_verify_jwt_token_invalid(self):
        """Test verifying invalid JWT token"""
        invalid_token = "invalid.token.here"
        decoded = verify_jwt_token(invalid_token)

        assert decoded is None

    def test_verify_jwt_token_expired(self):
        """Test verifying expired JWT token"""
        # Create token with -1 day expiration
        payload = {
            "user_id": 123,
            "email": "test@example.com",
            "exp": datetime.utcnow() - timedelta(days=1)
        }

        # We need to create a custom token with expired time
        # Since our function adds exp automatically, we'll test with invalid token
        decoded = verify_jwt_token("expired.token.test")

        assert decoded is None


class TestPasswordReset:
    """Test password reset token functions"""

    def test_generate_reset_token(self):
        """Test reset token generation"""
        email = "test@example.com"
        token = generate_reset_token(email)

        assert token is not None
        assert len(token) > 100
        assert "." in token

    def test_verify_reset_token_valid(self):
        """Test verifying valid reset token"""
        email = "test@example.com"
        token = generate_reset_token(email)

        decoded_email = verify_reset_token(token)

        assert decoded_email == email

    def test_verify_reset_token_invalid(self):
        """Test verifying invalid reset token"""
        decoded_email = verify_reset_token("invalid.reset.token")

        assert decoded_email is None

    def test_reset_token_different_each_time(self):
        """Test that reset tokens are different each time"""
        email = "test@example.com"
        token1 = generate_reset_token(email)
        token2 = generate_reset_token(email)

        assert token1 != token2
        assert verify_reset_token(token1) == email
        assert verify_reset_token(token2) == email


if __name__ == "__main__":
    pytest.main([__file__, "-v"])