"""
Role-Based Access Control (RBAC) Middleware
Provides decorators and dependencies for role-based authorization
"""

from functools import wraps
from typing import List, Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os

from agents.auth import ALGORITHM


security = HTTPBearer()


# Role hierarchy (higher number = more permissions)
ROLE_HIERARCHY = {
    "user": 1,
    "admin": 2,
    "superadmin": 3
}


def _get_secret_key() -> str:
    """Get SECRET_KEY from environment"""
    secret = os.getenv("SECRET_KEY")
    if not secret:
        raise ValueError("SECRET_KEY environment variable is not set")
    return secret


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency to get current user from JWT token
    
    Args:
        credentials: HTTP Authorization credentials
        
    Returns:
        User data from JWT token
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(token, _get_secret_key(), algorithms=[ALGORITHM])
        
        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role", "user")
        
        if not user_id or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "id": user_id,
            "email": email,
            "role": role,
            "name": payload.get("name", ""),
        }
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency to get current active user
    
    Args:
        current_user: Current user from JWT token
        
    Returns:
        User data if active
        
    Raises:
        HTTPException: If user is inactive
    """
    # TODO: Check user status in database
    # For now, assume all users are active
    return current_user


def require_role(required_role: str):
    """
    Dependency factory to require specific role
    
    Args:
        required_role: Minimum required role (user, admin, superadmin)
        
    Returns:
        Dependency function that checks user role
        
    Example:
        @router.get("/admin/dashboard")
        async def dashboard(user = Depends(require_role("admin"))):
            return {"message": "Admin dashboard"}
    """
    async def role_checker(current_user: dict = Depends(get_current_active_user)) -> dict:
        user_role = current_user.get("role", "user")
        
        user_level = ROLE_HIERARCHY.get(user_role, 0)
        required_level = ROLE_HIERARCHY.get(required_role, 999)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}, your role: {user_role}"
            )
        
        return current_user
    
    return role_checker


def require_any_role(allowed_roles: List[str]):
    """
    Dependency factory to require any of the specified roles
    
    Args:
        allowed_roles: List of allowed roles
        
    Returns:
        Dependency function that checks if user has any of the allowed roles
        
    Example:
        @router.get("/admin/users")
        async def users(user = Depends(require_any_role(["admin", "superadmin"]))):
            return {"users": []}
    """
    async def role_checker(current_user: dict = Depends(get_current_active_user)) -> dict:
        user_role = current_user.get("role", "user")
        
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required one of: {', '.join(allowed_roles)}, your role: {user_role}"
            )
        
        return current_user
    
    return role_checker


# Convenience dependencies for common role checks
require_user = require_role("user")
require_admin = require_role("admin")
require_superadmin = require_role("superadmin")


def can_modify_user(current_user: dict, target_user_role: str) -> bool:
    """
    Check if current user can modify a user with target role
    
    Rules:
    - Superadmin can modify anyone
    - Admin can modify users and other admins (but not superadmins)
    - Users cannot modify anyone
    
    Args:
        current_user: Current user data
        target_user_role: Role of the user to be modified
        
    Returns:
        True if modification is allowed
    """
    current_role = current_user.get("role", "user")
    
    if current_role == "superadmin":
        return True
    
    if current_role == "admin":
        return target_user_role in ["user", "admin"]
    
    return False


def can_delete_user(current_user: dict, target_user_role: str) -> bool:
    """
    Check if current user can delete a user with target role
    
    Rules:
    - Superadmin can delete anyone except other superadmins
    - Admin can delete users only
    - Users cannot delete anyone
    
    Args:
        current_user: Current user data
        target_user_role: Role of the user to be deleted
        
    Returns:
        True if deletion is allowed
    """
    current_role = current_user.get("role", "user")
    
    if current_role == "superadmin":
        return target_user_role != "superadmin"
    
    if current_role == "admin":
        return target_user_role == "user"
    
    return False


def can_change_role(current_user: dict, target_user_role: str, new_role: str) -> bool:
    """
    Check if current user can change a user's role
    
    Rules:
    - Superadmin can change anyone's role to anything
    - Admin can promote users to admin (but not to superadmin)
    - Admin can demote admins to user
    - Users cannot change roles
    
    Args:
        current_user: Current user data
        target_user_role: Current role of the target user
        new_role: New role to assign
        
    Returns:
        True if role change is allowed
    """
    current_role = current_user.get("role", "user")
    
    if current_role == "superadmin":
        return True
    
    if current_role == "admin":
        # Admin cannot create superadmins
        if new_role == "superadmin":
            return False
        # Admin cannot modify superadmins
        if target_user_role == "superadmin":
            return False
        return True
    
    return False


# Audit logging decorator
def audit_log(action: str):
    """
    Decorator to log admin actions for audit trail
    
    Args:
        action: Description of the action being performed
        
    Example:
        @audit_log("delete_user")
        async def delete_user(user_id: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # TODO: Implement actual audit logging to database
            # For now, just print
            print(f"[AUDIT] Action: {action}, Args: {args}, Kwargs: {kwargs}")
            return await func(*args, **kwargs)
        return wrapper
    return decorator
