"""
Auth utilities: password hashing/verification and JWT creation/validation.

Dependencies:
- bcrypt
- PyJWT (import name: jwt)

SECRET_KEY is read from environment variable SECRET_KEY. Ensure it is set.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import bcrypt
import jwt


ALGORITHM = "HS256"


def _get_secret_key() -> str:
    """
    Fetch SECRET_KEY from environment.
    Validates that key is strong enough (minimum 32 characters).
    Raises a ValueError if not configured or too weak.
    """
    secret = os.getenv("SECRET_KEY")
    if not secret:
        raise ValueError("SECRET_KEY environment variable is not set")
    
    # Валидация: SECRET_KEY должен быть минимум 32 символа для production
    if len(secret) < 32:
        import warnings
        warnings.warn(
            f"SECRET_KEY is too short ({len(secret)} chars). "
            "For production, use at least 64 characters. "
            "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
        )
        # В development разрешаем короткие ключи, но предупреждаем
        if os.getenv("ENVIRONMENT", "development").lower() == "production":
            raise ValueError(
                f"SECRET_KEY is too short for production ({len(secret)} chars). "
                "Minimum 64 characters required. "
                "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
            )
    
    return secret


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt with automatically generated salt.

    Args:
        password: Plaintext password.

    Returns:
        Password hash as a UTF-8 string.
    """
    if password is None or password == "":
        raise ValueError("Password must be a non-empty string")

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.

    Args:
        password: Plaintext password.
        password_hash: Stored bcrypt hash.

    Returns:
        True if password matches the hash, otherwise False.
    """
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        # In case the stored hash is malformed or uses an unsupported format
        return False


def create_jwt_token(user_id: int, email: str, expires_hours: int = 24) -> str:
    """
    Create a signed JWT token containing user identity claims.

    Claims:
        - sub: user_id
        - email: user's email
        - iat: issued-at (UTC)
        - exp: expiration time (UTC)

    Args:
        user_id: Numeric user identifier.
        email: User email address.
        expires_hours: Expiration window in hours (default 24).

    Returns:
        Encoded JWT string.
    """
    if expires_hours <= 0:
        raise ValueError("expires_hours must be positive")

    now = datetime.now(timezone.utc)
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=expires_hours)).timestamp()),
    }

    token = jwt.encode(payload, _get_secret_key(), algorithm=ALGORITHM)
    # PyJWT >=2 returns str; older returns bytes
    return token if isinstance(token, str) else token.decode("utf-8")


def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token.

    Args:
        token: Encoded JWT string.

    Returns:
        Decoded claims dict if valid; None if invalid or expired.
    """
    if not token:
        return None
    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=[ALGORITHM])
        # Ensure minimum expected claims are present
        if not payload.get("sub") or not payload.get("email"):
            return None
        # Convert sub back to int for downstream use
        try:
            payload["sub"] = int(payload["sub"])
        except (ValueError, TypeError):
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_current_user(authorization: str = None, cookies: Dict[str, str] = None):
    """
    Extract and verify user from JWT token (from header or cookie).

    Args:
        authorization: Authorization header value (Bearer token)
        cookies: Request cookies dict

    Returns:
        User info dict with 'id' and 'email' or raises exception
    """
    token = None

    # Try to get token from Authorization header first
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")

    # Fallback to cookie if no header token
    if not token and cookies:
        token = cookies.get("auth_token")

    if not token:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Verify token
    payload = verify_jwt_token(token)
    if not payload:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {
        "id": payload["sub"],
        "email": payload["email"]
    }


