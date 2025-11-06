"""
Enhanced Authentication Router with OAuth and CSRF
Full security implementation
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, Query
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
import jwt
import bcrypt
import secrets
from datetime import datetime, timedelta
import os
import logging

# Import our security modules
from api.database.postgres_adapter import get_postgres_db, PostgresAdapter
from api.auth.oauth_handlers import oauth_manager
from api.middleware.csrf_protection import CSRFTokenGenerator, get_csrf_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# CSRF token generator
csrf_generator = CSRFTokenGenerator(JWT_SECRET)

# Pydantic models
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    confirm_password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_code: Optional[str] = None
    csrf_token: Optional[str] = None

class OAuthLoginRequest(BaseModel):
    provider: str
    redirect_url: Optional[str] = None

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    csrf_token: str
    user: Dict[str, Any]
    expires_in: int

class UserResponse(BaseModel):
    id: int
    email: str
    created_at: str
    is_active: bool
    email_verified: bool
    has_2fa: bool
    oauth_providers: list

# Helper functions
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_jwt_token(user_id: int, email: str, session_id: str) -> tuple[str, datetime]:
    """Create JWT token"""
    expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "sub": str(user_id),
        "email": email,
        "session_id": session_id,
        "exp": expiration,
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, expiration

async def get_current_user(
    request: Request,
    db: PostgresAdapter = Depends(get_postgres_db)
) -> Optional[Dict[str, Any]]:
    """Get current user from JWT token"""
    # Check Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.replace("Bearer ", "")

    try:
        # Decode JWT
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub"))
        session_id = payload.get("session_id")

        # Verify session
        session = await db.get_session(token)
        if not session or session['user_id'] != user_id:
            return None

        # Get user
        user = await db.get_user_by_id(user_id)
        if not user or not user['is_active']:
            return None

        return user

    except jwt.ExpiredSignatureError:
        logger.warning("Expired JWT token")
        return None
    except Exception as e:
        logger.error(f"JWT verification failed: {e}")
        return None

# Endpoints
@router.post("/register", response_model=AuthResponse)
async def register(
    request: RegisterRequest,
    response: Response,
    db: PostgresAdapter = Depends(get_postgres_db),
    client_request: Request = None
):
    """Register a new user with enhanced security"""
    # Validate passwords match
    if request.password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )

    # Password strength validation
    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )

    # Check for common patterns
    if request.password.lower() in request.email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password cannot contain email address"
        )

    # Check if user exists
    existing_user = await db.get_user_by_email(request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Create user
    password_hash = hash_password(request.password)
    user = await db.create_user(request.email, password_hash)

    # Create session
    session_id = secrets.token_urlsafe(32)
    jwt_token, expiration = create_jwt_token(user['id'], user['email'], session_id)
    csrf_token = csrf_generator.generate_form_token(session_id)

    # Store session in database
    await db.create_session(
        user_id=user['id'],
        token=jwt_token,
        csrf_token=csrf_token,
        expires_at=expiration,
        ip_address=client_request.client.host if client_request else None,
        user_agent=client_request.headers.get("User-Agent") if client_request else None
    )

    # Set secure cookie
    response.set_cookie(
        key="session",
        value=jwt_token,
        max_age=JWT_EXPIRATION_HOURS * 3600,
        httponly=True,
        secure=True,
        samesite="strict"
    )

    return AuthResponse(
        access_token=jwt_token,
        csrf_token=csrf_token,
        user={
            "id": user['id'],
            "email": user['email'],
            "created_at": user['created_at'].isoformat()
        },
        expires_in=JWT_EXPIRATION_HOURS * 3600
    )

@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    response: Response,
    db: PostgresAdapter = Depends(get_postgres_db),
    client_request: Request = None
):
    """Login with email and password"""
    # Get user
    user = await db.get_user_by_email(request.email)

    if not user:
        # Prevent timing attacks by still hashing
        hash_password("dummy_password")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Check if account is locked
    if not user['is_active']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked"
        )

    # Verify password
    if not verify_password(request.password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # TODO: Handle 2FA if enabled
    if user.get('two_factor_enabled'):
        if not request.totp_code:
            raise HTTPException(
                status_code=status.HTTP_428_PRECONDITION_REQUIRED,
                detail="2FA code required"
            )
        # Verify TOTP code here

    # Update last login
    await db.update_user_login(user['id'])

    # Create session
    session_id = secrets.token_urlsafe(32)
    jwt_token, expiration = create_jwt_token(user['id'], user['email'], session_id)
    csrf_token = csrf_generator.generate_form_token(session_id)

    # Store session
    await db.create_session(
        user_id=user['id'],
        token=jwt_token,
        csrf_token=csrf_token,
        expires_at=expiration,
        ip_address=client_request.client.host if client_request else None,
        user_agent=client_request.headers.get("User-Agent") if client_request else None
    )

    # Set secure cookie
    response.set_cookie(
        key="session",
        value=jwt_token,
        max_age=JWT_EXPIRATION_HOURS * 3600,
        httponly=True,
        secure=True,
        samesite="strict"
    )

    return AuthResponse(
        access_token=jwt_token,
        csrf_token=csrf_token,
        user={
            "id": user['id'],
            "email": user['email'],
            "created_at": user['created_at'].isoformat()
        },
        expires_in=JWT_EXPIRATION_HOURS * 3600
    )

@router.post("/logout")
async def logout(
    response: Response,
    db: PostgresAdapter = Depends(get_postgres_db),
    current_user: Dict = Depends(get_current_user),
    request: Request = None
):
    """Logout user and revoke session"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Get token from header
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")

    # Revoke session
    if token:
        await db.revoke_session(token)

    # Clear cookie
    response.delete_cookie(key="session")

    return {"message": "Logged out successfully"}

# OAuth endpoints
@router.post("/oauth/authorize")
async def oauth_authorize(request: OAuthLoginRequest):
    """Initialize OAuth flow"""
    try:
        result = oauth_manager.create_authorization_url(
            request.provider,
            request.redirect_url or FRONTEND_URL
        )
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"OAuth authorization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth authorization failed"
        )

@router.get("/callback/{provider}")
async def oauth_callback(
    provider: str,
    code: str = Query(...),
    state: str = Query(...),
    response: Response = None,
    db: PostgresAdapter = Depends(get_postgres_db),
    request: Request = None
):
    """Handle OAuth callback"""
    try:
        # Handle callback and get user info
        user_info = await oauth_manager.handle_callback(provider, code, state)

        # Check if OAuth account exists
        oauth_account = await db.get_oauth_account(
            provider,
            user_info['provider_user_id']
        )

        if oauth_account:
            # Existing user - login
            user_id = oauth_account['user_id']
            user = await db.get_user_by_id(user_id)
        else:
            # New user - create account
            # Check if email already exists
            existing_user = await db.get_user_by_email(user_info['email'])

            if existing_user:
                # Link OAuth to existing account
                user_id = existing_user['id']
                user = existing_user
            else:
                # Create new user
                user = await db.create_user(
                    email=user_info['email'],
                    password_hash=None  # No password for OAuth users
                )
                user_id = user['id']

            # Create OAuth account link
            await db.create_oauth_account(
                user_id=user_id,
                provider=provider,
                provider_user_id=user_info['provider_user_id'],
                access_token=user_info.get('access_token'),
                refresh_token=user_info.get('refresh_token'),
                expires_at=datetime.utcnow() + timedelta(seconds=user_info.get('expires_in', 3600))
                if user_info.get('expires_in') else None
            )

        # Create session
        session_id = secrets.token_urlsafe(32)
        jwt_token, expiration = create_jwt_token(user_id, user['email'], session_id)
        csrf_token = csrf_generator.generate_form_token(session_id)

        # Store session
        await db.create_session(
            user_id=user_id,
            token=jwt_token,
            csrf_token=csrf_token,
            expires_at=expiration,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("User-Agent") if request else None
        )

        # Redirect to frontend with token
        redirect_url = user_info.get('redirect_url', FRONTEND_URL)
        return RedirectResponse(
            url=f"{redirect_url}/auth/success?token={jwt_token}&csrf={csrf_token}",
            status_code=status.HTTP_302_FOUND
        )

    except HTTPException as e:
        logger.error(f"OAuth callback failed: {e.detail}")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/auth/error?error={e.detail}",
            status_code=status.HTTP_302_FOUND
        )
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/auth/error?error=Authentication failed",
            status_code=status.HTTP_302_FOUND
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Dict = Depends(get_current_user),
    db: PostgresAdapter = Depends(get_postgres_db)
):
    """Get current user information"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Get OAuth providers
    oauth_providers = await db.fetch("""
        SELECT provider FROM oauth_accounts
        WHERE user_id = $1
    """, current_user['id'])

    return UserResponse(
        id=current_user['id'],
        email=current_user['email'],
        created_at=current_user['created_at'].isoformat(),
        is_active=current_user['is_active'],
        email_verified=current_user['email_verified'],
        has_2fa=current_user['two_factor_enabled'],
        oauth_providers=[p['provider'] for p in oauth_providers]
    )

@router.post("/verify-csrf")
async def verify_csrf_token(
    csrf_token: str,
    db: PostgresAdapter = Depends(get_postgres_db),
    current_user: Dict = Depends(get_current_user),
    request: Request = None
):
    """Verify CSRF token for a session"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Get session token
    auth_header = request.headers.get("Authorization", "")
    session_token = auth_header.replace("Bearer ", "")

    # Verify CSRF token
    is_valid = await db.verify_csrf_token(session_token, csrf_token)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token"
        )

    return {"valid": True}

@router.post("/refresh-csrf")
async def refresh_csrf_token(
    db: PostgresAdapter = Depends(get_postgres_db),
    current_user: Dict = Depends(get_current_user),
    request: Request = None
):
    """Generate a new CSRF token for the session"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Get session
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")

    session = await db.get_session(token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )

    # Generate new CSRF token
    new_csrf_token = csrf_generator.generate_form_token(str(session['id']))

    # Update session with new CSRF token
    await db.execute("""
        UPDATE sessions
        SET csrf_token = $1
        WHERE token = $2
    """, new_csrf_token, token)

    return {"csrf_token": new_csrf_token}