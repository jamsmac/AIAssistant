"""
Auth utilities: password hashing/verification and JWT creation/validation.

Dependencies:
- bcrypt
- PyJWT (import name: jwt)

SECRET_KEY is read from environment variable SECRET_KEY. Ensure it is set.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple

import bcrypt
import jwt
from fastapi import Request, HTTPException


ALGORITHM = "HS256"


def generate_secret_key(length: int = 64) -> str:
    """
    Генерирует криптографически стойкий SECRET_KEY.
    
    Args:
        length: Длина ключа в байтах (по умолчанию 64, что даёт ~86 символов в base64)
        
    Returns:
        Случайный URL-safe base64 ключ
    """
    import secrets
    return secrets.token_urlsafe(length)


def validate_secret_key(secret: str, is_production: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Валидирует SECRET_KEY на соответствие требованиям безопасности.
    
    Args:
        secret: SECRET_KEY для валидации
        is_production: True если это production окружение
        
    Returns:
        Tuple (is_valid, error_message)
        - is_valid: True если ключ валиден
        - error_message: Сообщение об ошибке или None
    """
    if not secret:
        return False, "SECRET_KEY is not set"
    
    if not isinstance(secret, str):
        return False, "SECRET_KEY must be a string"
    
    # Минимальная длина зависит от окружения
    min_length = 64 if is_production else 32
    
    if len(secret) < min_length:
        return False, (
            f"SECRET_KEY is too short ({len(secret)} chars). "
            f"Minimum {min_length} characters required for {'production' if is_production else 'development'}. "
            f"Generate with: python scripts/generate_secret_key.py"
        )
    
    # Проверка энтропии: ключ должен содержать разные типы символов
    has_lower = any(c.islower() for c in secret)
    has_upper = any(c.isupper() for c in secret)
    has_digit = any(c.isdigit() for c in secret)
    has_special = any(c in "-_" for c in secret)  # URL-safe base64 characters
    
    # В production требуем более высокую энтропию
    if is_production:
        if not (has_lower or has_upper) or not has_digit:
            return False, (
                "SECRET_KEY has insufficient entropy for production. "
                "Key should contain a mix of letters, numbers, and special characters."
            )
    
    # Проверка на слабые паттерны
    weak_patterns = [
        "password", "secret", "key", "admin", "test",
        "12345", "abcdef", "qwerty", "00000", "aaaaa"
    ]
    secret_lower = secret.lower()
    for pattern in weak_patterns:
        if pattern in secret_lower:
            return False, f"SECRET_KEY contains weak pattern: '{pattern}'"
    
    return True, None


def _get_secret_key() -> str:
    """
    Fetch SECRET_KEY from environment.
    Validates that key is strong enough (minimum 32 chars for dev, 64 for production).
    Raises a ValueError if not configured or too weak.
    """
    secret = os.getenv("SECRET_KEY")
    if not secret:
        raise ValueError(
            "SECRET_KEY environment variable is not set. "
            "Generate one with: python scripts/generate_secret_key.py"
        )
    
    # Определяем окружение
    environment = os.getenv("ENVIRONMENT", "development").lower()
    is_production = environment == "production"
    
    # Валидируем ключ
    is_valid, error_message = validate_secret_key(secret, is_production)
    
    if not is_valid:
        if is_production:
            # В production строго требуем валидный ключ
            raise ValueError(error_message)
        else:
            # В development предупреждаем, но разрешаем
            import warnings
            warnings.warn(f"SECRET_KEY validation warning: {error_message}")
    
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


def verify_reset_token(token: str) -> Optional[str]:
    """
    Verify a password reset token.
    
    Args:
        token: Reset token string.
        
    Returns:
        Email address if token is valid, None otherwise.
    """
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=[ALGORITHM])
        # Reset tokens should have email and reset action
        if payload.get("action") != "password_reset":
            return None
        return payload.get("email")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def generate_reset_token(email: str, expires_hours: int = 1) -> str:
    """
    Generate a password reset token for a user.
    
    Args:
        email: User email address.
        expires_hours: Token expiration time in hours (default 1 hour).
        
    Returns:
        Encoded reset token string.
    """
    if expires_hours <= 0:
        raise ValueError("expires_hours must be positive")
    
    now = datetime.now(timezone.utc)
    payload: Dict[str, Any] = {
        "email": email,
        "action": "password_reset",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=expires_hours)).timestamp()),
    }
    
    token = jwt.encode(payload, _get_secret_key(), algorithm=ALGORITHM)
    return token if isinstance(token, str) else token.decode("utf-8")


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
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Verify token
    payload = verify_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Fetch user role from database
    user_id = payload["sub"]
    role = "user"  # Default role

    try:
        import sqlite3
        from pathlib import Path
        db_path = Path(__file__).parent.parent / "data" / "history.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        if result and result[0]:
            role = result[0]
        conn.close()
    except Exception as e:
        # If role fetch fails, continue with default role
        pass

    return {
        "id": payload["sub"],
        "email": payload["email"],
        "role": role
    }


def get_current_user_from_token(request: Request) -> Dict[str, Any]:
    """FastAPI dependency wrapper to extract user from cookies/headers."""
    authorization = request.headers.get("Authorization")
    cookies = dict(request.cookies) if request.cookies else {}
    user = get_current_user(authorization=authorization, cookies=cookies)
    return {
        "id": user["id"],
        "email": user["email"],
        "role": user.get("role"),
        "user_id": user.get("id"),
    }


