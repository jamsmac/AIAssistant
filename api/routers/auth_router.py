"""
Authentication Router
Handles all authentication-related endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
import jwt
import bcrypt
from datetime import datetime, timedelta
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.database import HistoryDatabase, get_db
from agents.auth import get_current_user, create_jwt_token
from agents.two_factor_auth import TwoFactorAuth
from agents.csrf_protection import CSRFProtection

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Initialize services
db = get_db()
tfa = TwoFactorAuth(db)
csrf = CSRFProtection()

# Pydantic models
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    confirm_password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_code: Optional[str] = None

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserInfo(BaseModel):
    id: int
    email: str
    created_at: str
    is_active: bool
    has_2fa: bool = False

# Endpoints
@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """Register a new user"""
    if request.password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )

    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )

    # Check if user exists
    existing_user = db.get_user_by_email(request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password
    password_hash = bcrypt.hashpw(
        request.password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

    # Create user
    user_id = db.create_user(request.email, password_hash)

    # Create access token
    access_token = create_jwt_token(user_id=user_id, email=request.email)

    return AuthResponse(
        access_token=access_token,
        user={"id": user_id, "email": request.email}
    )

@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, response: Response):
    """Login user"""
    user = db.get_user_by_email(request.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Verify password
    if not bcrypt.checkpw(
        request.password.encode('utf-8'),
        user['password_hash'].encode('utf-8')
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Check 2FA if enabled
    if user.get('has_2fa'):
        if not request.totp_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA code required"
            )

        is_valid = await tfa.verify_totp(user['id'], request.totp_code)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 2FA code"
            )

    # Update last login
    db.update_last_login(user['id'])

    # Create access token
    access_token = create_jwt_token(user_id=user['id'], email=user['email'])

    # Set secure cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=86400  # 24 hours
    )

    return AuthResponse(
        access_token=access_token,
        user={"id": user['id'], "email": user['email']}
    )

@router.post("/logout")
async def logout(response: Response):
    """Logout user"""
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserInfo)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    user = db.get_user_by_id(current_user['id'])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserInfo(
        id=user['id'],
        email=user['email'],
        created_at=user['created_at'],
        is_active=user['is_active'],
        has_2fa=user.get('has_2fa', False)
    )

@router.get("/csrf-token")
async def get_csrf_token(request: Request):
    """Get CSRF token for forms"""
    token = csrf.generate_token(request)
    return {"csrf_token": token}

# 2FA endpoints
@router.post("/2fa/setup")
async def setup_2fa(current_user: dict = Depends(get_current_user)):
    """Setup 2FA for current user"""
    result = await tfa.setup_2fa(current_user['id'])
    return result

@router.post("/2fa/enable")
async def enable_2fa(
    totp_code: str,
    current_user: dict = Depends(get_current_user)
):
    """Enable 2FA with TOTP code verification"""
    result = await tfa.enable_2fa(current_user['id'], totp_code)
    return result

@router.post("/2fa/disable")
async def disable_2fa(
    password: str,
    current_user: dict = Depends(get_current_user)
):
    """Disable 2FA with password verification"""
    user = db.get_user_by_id(current_user['id'])

    # Verify password
    if not bcrypt.checkpw(
        password.encode('utf-8'),
        user['password_hash'].encode('utf-8')
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )

    result = await tfa.disable_2fa(current_user['id'])
    return result

@router.get("/2fa/backup-codes")
async def get_backup_codes(current_user: dict = Depends(get_current_user)):
    """Get 2FA backup codes"""
    codes = await tfa.get_backup_codes(current_user['id'])
    return {"backup_codes": codes}

@router.post("/2fa/regenerate-backup-codes")
async def regenerate_backup_codes(current_user: dict = Depends(get_current_user)):
    """Regenerate 2FA backup codes"""
    codes = await tfa.regenerate_backup_codes(current_user['id'])
    return {"backup_codes": codes}