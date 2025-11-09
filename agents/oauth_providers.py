"""
OAuth Provider Configuration and Handlers
Supports Google, GitHub, and Microsoft OAuth flows
"""

import os
import json
import hashlib
import secrets
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import httpx
from urllib.parse import urlencode
import jwt

class OAuthProvider:
    """Base OAuth provider class"""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.state_store: Dict[str, Dict] = {}  # In production, use Redis

    def generate_state(self, user_data: Optional[Dict] = None) -> str:
        """Generate secure state parameter"""
        state = secrets.token_urlsafe(32)
        self.state_store[state] = {
            "created_at": datetime.utcnow().isoformat(),
            "user_data": user_data or {}
        }
        return state

    def verify_state(self, state: str) -> bool:
        """Verify state parameter and check expiry"""
        if state not in self.state_store:
            return False

        state_data = self.state_store[state]
        created_at = datetime.fromisoformat(state_data["created_at"])

        # State expires after 10 minutes
        if datetime.utcnow() - created_at > timedelta(minutes=10):
            del self.state_store[state]
            return False

        return True

    def get_authorization_url(self, scope: list, state: Optional[str] = None) -> str:
        """Get OAuth authorization URL"""
        raise NotImplementedError

    async def exchange_code_for_token(self, code: str) -> Dict:
        """Exchange authorization code for access token"""
        raise NotImplementedError

    async def get_user_info(self, access_token: str) -> Dict:
        """Get user information using access token"""
        raise NotImplementedError


class GoogleOAuthProvider(OAuthProvider):
    """Google OAuth 2.0 provider"""

    AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    def get_authorization_url(self, scope: list = None, state: Optional[str] = None) -> str:
        """Generate Google OAuth authorization URL"""
        if scope is None:
            scope = ["openid", "email", "profile"]

        if state is None:
            state = self.generate_state()

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(scope),
            "state": state,
            "access_type": "offline",
            "prompt": "consent"
        }

        return f"{self.AUTHORIZATION_URL}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> Dict:
        """Exchange authorization code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri
                }
            )
            response.raise_for_status()
            return response.json()

    async def get_user_info(self, access_token: str) -> Dict:
        """Get Google user information"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.USER_INFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()


class GitHubOAuthProvider(OAuthProvider):
    """GitHub OAuth 2.0 provider"""

    AUTHORIZATION_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USER_INFO_URL = "https://api.github.com/user"

    def get_authorization_url(self, scope: list = None, state: Optional[str] = None) -> str:
        """Generate GitHub OAuth authorization URL"""
        if scope is None:
            scope = ["user:email", "read:user"]

        if state is None:
            state = self.generate_state()

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(scope),
            "state": state
        }

        return f"{self.AUTHORIZATION_URL}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> Dict:
        """Exchange authorization code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                headers={"Accept": "application/json"},
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri
                }
            )
            response.raise_for_status()
            return response.json()

    async def get_user_info(self, access_token: str) -> Dict:
        """Get GitHub user information"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.USER_INFO_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            response.raise_for_status()
            user_data = response.json()

            # Get primary email if not public
            if not user_data.get("email"):
                email_response = await client.get(
                    "https://api.github.com/user/emails",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                )
                if email_response.status_code == 200:
                    emails = email_response.json()
                    primary_email = next(
                        (e["email"] for e in emails if e["primary"]),
                        None
                    )
                    if primary_email:
                        user_data["email"] = primary_email

            return user_data


class MicrosoftOAuthProvider(OAuthProvider):
    """Microsoft OAuth 2.0 provider"""

    TENANT = "common"  # Use 'common' for multi-tenant
    AUTHORIZATION_URL = f"https://login.microsoftonline.com/{TENANT}/oauth2/v2.0/authorize"
    TOKEN_URL = f"https://login.microsoftonline.com/{TENANT}/oauth2/v2.0/token"
    USER_INFO_URL = "https://graph.microsoft.com/v1.0/me"

    def get_authorization_url(self, scope: list = None, state: Optional[str] = None) -> str:
        """Generate Microsoft OAuth authorization URL"""
        if scope is None:
            scope = ["openid", "email", "profile", "User.Read"]

        if state is None:
            state = self.generate_state()

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(scope),
            "state": state,
            "response_mode": "query"
        }

        return f"{self.AUTHORIZATION_URL}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> Dict:
        """Exchange authorization code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri
                }
            )
            response.raise_for_status()
            return response.json()

    async def get_user_info(self, access_token: str) -> Dict:
        """Get Microsoft user information"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.USER_INFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()


class OAuthManager:
    """Manage OAuth providers and flows"""

    def __init__(self):
        self.providers: Dict[str, OAuthProvider] = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize OAuth providers from environment variables"""
        # Получаем базовый URL для production (для callback URLs)
        base_url = os.getenv("FRONTEND_URL", os.getenv("BASE_URL", "http://localhost:3000"))
        
        # Google OAuth
        if all([
            os.getenv("GOOGLE_CLIENT_ID"),
            os.getenv("GOOGLE_CLIENT_SECRET")
        ]):
            # Используем явный GOOGLE_REDIRECT_URI или формируем из базового URL
            google_redirect = os.getenv(
                "GOOGLE_REDIRECT_URI",
                f"{base_url}/api/auth/callback/google"
            )
            self.providers["google"] = GoogleOAuthProvider(
                client_id=os.getenv("GOOGLE_CLIENT_ID"),
                client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
                redirect_uri=google_redirect
            )

        # GitHub OAuth
        if all([
            os.getenv("GITHUB_CLIENT_ID"),
            os.getenv("GITHUB_CLIENT_SECRET")
        ]):
            github_redirect = os.getenv(
                "GITHUB_REDIRECT_URI",
                f"{base_url}/api/auth/callback/github"
            )
            self.providers["github"] = GitHubOAuthProvider(
                client_id=os.getenv("GITHUB_CLIENT_ID"),
                client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
                redirect_uri=github_redirect
            )

        # Microsoft OAuth
        if all([
            os.getenv("MICROSOFT_CLIENT_ID"),
            os.getenv("MICROSOFT_CLIENT_SECRET")
        ]):
            microsoft_redirect = os.getenv(
                "MICROSOFT_REDIRECT_URI",
                f"{base_url}/api/auth/callback/microsoft"
            )
            self.providers["microsoft"] = MicrosoftOAuthProvider(
                client_id=os.getenv("MICROSOFT_CLIENT_ID"),
                client_secret=os.getenv("MICROSOFT_CLIENT_SECRET"),
                redirect_uri=microsoft_redirect
            )

    def get_provider(self, provider_name: str) -> Optional[OAuthProvider]:
        """Get OAuth provider by name"""
        return self.providers.get(provider_name.lower())

    def list_available_providers(self) -> list:
        """List all available OAuth providers"""
        return list(self.providers.keys())

    async def handle_callback(self, provider_name: str, code: str, state: str) -> Dict:
        """Handle OAuth callback"""
        provider = self.get_provider(provider_name)
        if not provider:
            raise ValueError(f"Provider {provider_name} not configured")

        # Verify state
        if not provider.verify_state(state):
            raise ValueError("Invalid or expired state parameter")

        # Exchange code for token
        token_data = await provider.exchange_code_for_token(code)

        # Get user info
        user_info = await provider.get_user_info(token_data["access_token"])

        # Clean up state
        if state in provider.state_store:
            del provider.state_store[state]

        return {
            "provider": provider_name,
            "user_info": user_info,
            "access_token": token_data.get("access_token"),
            "refresh_token": token_data.get("refresh_token"),
            "expires_in": token_data.get("expires_in")
        }


# Singleton instance
oauth_manager = OAuthManager()


class _OAuthProviderAdapter:
    """Adapter to maintain backward compatibility with legacy router interface."""

    def __init__(self, provider: OAuthProvider):
        self._provider = provider

    def _with_redirect(self, redirect_uri: str):
        class _RedirectCtx:
            def __init__(self, outer, new_uri):
                self.outer = outer
                self.new_uri = new_uri
                self.original = outer._provider.redirect_uri

            def __enter__(self):
                self.outer._provider.redirect_uri = self.new_uri

            def __exit__(self, exc_type, exc, tb):
                self.outer._provider.redirect_uri = self.original

        return _RedirectCtx(self, redirect_uri)

    def get_auth_url(self, redirect_uri: str, state: str):
        with self._with_redirect(redirect_uri):
            return self._provider.get_authorization_url(state=state)

    async def exchange_code(self, code: str, redirect_uri: str):
        with self._with_redirect(redirect_uri):
            token_data = await self._provider.exchange_code_for_token(code)
        if "expires_at" not in token_data and "expires_in" in token_data:
            token_data["expires_at"] = None
        return token_data

    async def get_account_info(self, access_token: str):
        return await self._provider.get_user_info(access_token)


class OAuthProviderFactory:
    """Legacy factory retained for integration router compatibility."""

    SERVICE_MAP = {
        "gmail": "google",
        "google_drive": "google",
        "google": "google",
        "github": "github",
        "microsoft": "microsoft",
    }

    def __init__(self):
        self.manager = oauth_manager

    def get_provider(self, service: str):
        canonical = self.SERVICE_MAP.get(service.lower())
        if not canonical:
            return None
        provider = self.manager.get_provider(canonical)
        if not provider:
            return None
        return _OAuthProviderAdapter(provider)

    def list_providers(self):
        return self.manager.list_available_providers()