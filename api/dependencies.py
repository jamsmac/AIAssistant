"""
Shared Dependencies for AI Assistant Platform
Common dependencies, validation, and utilities
"""
import os
import logging
from typing import Optional
from fastapi import Depends, HTTPException, Header
from agents.auth import verify_jwt_token, validate_secret_key

logger = logging.getLogger(__name__)


async def validate_environment():
    """
    Validate environment configuration on startup.
    Checks SECRET_KEY, API keys, and other critical settings.
    """
    environment = os.getenv("ENVIRONMENT", "development").lower()
    is_production = environment == "production"
    
    # Validate SECRET_KEY
    secret_key = os.getenv("SECRET_KEY")
    if secret_key:
        is_valid, error_message = validate_secret_key(secret_key, is_production)
        if not is_valid:
            if is_production:
                logger.error(f"SECRET_KEY validation failed: {error_message}")
                raise ValueError(f"Invalid SECRET_KEY: {error_message}")
            else:
                logger.warning(f"SECRET_KEY validation warning: {error_message}")
        else:
            logger.info("SECRET_KEY validated successfully")
    else:
        logger.error("SECRET_KEY is not set. Generate one with: python scripts/generate_secret_key.py")
        if is_production:
            raise ValueError("SECRET_KEY must be set in production environment")
    
    # Check for required API keys (warn only, don't fail)
    api_keys = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
    }
    
    missing_keys = [key for key, value in api_keys.items() if not value]
    if missing_keys:
        logger.warning(f"Missing API keys: {', '.join(missing_keys)}")
    else:
        logger.info("All API keys configured")
    
    logger.info(f"Environment validation complete (environment: {environment})")


async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Dependency to get current authenticated user from JWT token.
    
    Args:
        authorization: Authorization header with Bearer token
        
    Returns:
        User data from JWT token
        
    Raises:
        HTTPException: If token is missing or invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        user_data = verify_jwt_token(token)
        return user_data
    except Exception as e:
        logger.error(f"JWT verification failed: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )


async def get_optional_user(authorization: Optional[str] = Header(None)):
    """
    Dependency to get current user if authenticated, None otherwise.
    
    Args:
        authorization: Authorization header with Bearer token
        
    Returns:
        User data from JWT token or None
    """
    if not authorization:
        return None
    
    try:
        return await get_current_user(authorization)
    except HTTPException:
        return None


def require_admin(current_user: dict = Depends(get_current_user)):
    """
    Dependency to require admin role.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User data if admin
        
    Raises:
        HTTPException: If user is not admin
    """
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return current_user
