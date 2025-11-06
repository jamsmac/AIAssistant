"""
OAuth Authentication Handlers for Google and GitHub
Secure implementation with state validation and PKCE
"""
import os
import secrets
import hashlib
import base64
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
from fastapi import HTTPException, Request
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)


class OAuthProvider:
    """Base OAuth provider class"""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def generate_state(self) -> str:
        """Generate secure random state parameter"""
        return secrets.token_urlsafe(32)

    def generate_pkce(self) -> tuple[str, str]:
        """Generate PKCE challenge and verifier"""
        verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode()).digest()
        ).decode('utf-8').rstrip('=')
        return verifier, challenge

    async def exchange_code(self, code: str, **kwargs) -> Dict[str, Any]:
        """Exchange authorization code for tokens"""
        raise NotImplementedError

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user info from provider"""
        raise NotImplementedError


class GoogleOAuth(OAuthProvider):
    """Google OAuth 2.0 provider"""

    AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    def get_authorize_url(self, state: str, code_challenge: Optional[str] = None) -> str:
        """Get Google OAuth authorization URL"""
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'state': state,
            'access_type': 'offline',
            'prompt': 'consent'
        }

        if code_challenge:
            params.update({
                'code_challenge': code_challenge,
                'code_challenge_method': 'S256'
            })

        return f"{self.AUTHORIZE_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str, code_verifier: Optional[str] = None) -> Dict[str, Any]:
        """Exchange authorization code for tokens"""
        async with httpx.AsyncClient() as client:
            data = {
                'code': code,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': self.redirect_uri,
                'grant_type': 'authorization_code'
            }

            if code_verifier:
                data['code_verifier'] = code_verifier

            response = await client.post(self.TOKEN_URL, data=data)

            if response.status_code != 200:
                logger.error(f"Google token exchange failed: {response.text}")
                raise HTTPException(status_code=400, detail="Failed to exchange authorization code")

            return response.json()

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user info from Google"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.USERINFO_URL,
                headers={'Authorization': f'Bearer {access_token}'}
            )

            if response.status_code != 200:
                logger.error(f"Failed to get Google user info: {response.text}")
                raise HTTPException(status_code=400, detail="Failed to get user information")

            data = response.json()
            return {
                'provider': 'google',
                'provider_user_id': data['id'],
                'email': data['email'],
                'name': data.get('name'),
                'picture': data.get('picture'),
                'email_verified': data.get('verified_email', False)
            }

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh Google access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(self.TOKEN_URL, data={
                'refresh_token': refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'refresh_token'
            })

            if response.status_code != 200:
                logger.error(f"Failed to refresh Google token: {response.text}")
                raise HTTPException(status_code=400, detail="Failed to refresh access token")

            return response.json()


class GitHubOAuth(OAuthProvider):
    """GitHub OAuth 2.0 provider"""

    AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USER_URL = "https://api.github.com/user"
    EMAILS_URL = "https://api.github.com/user/emails"

    def get_authorize_url(self, state: str) -> str:
        """Get GitHub OAuth authorization URL"""
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'state': state,
            'scope': 'read:user user:email'
        }
        return f"{self.AUTHORIZE_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str, **kwargs) -> Dict[str, Any]:
        """Exchange authorization code for tokens"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'code': code,
                    'redirect_uri': self.redirect_uri
                },
                headers={'Accept': 'application/json'}
            )

            if response.status_code != 200:
                logger.error(f"GitHub token exchange failed: {response.text}")
                raise HTTPException(status_code=400, detail="Failed to exchange authorization code")

            data = response.json()
            if 'error' in data:
                logger.error(f"GitHub OAuth error: {data}")
                raise HTTPException(status_code=400, detail=data.get('error_description', 'OAuth error'))

            return data

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user info from GitHub"""
        async with httpx.AsyncClient() as client:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/vnd.github.v3+json'
            }

            # Get user info
            user_response = await client.get(self.USER_URL, headers=headers)
            if user_response.status_code != 200:
                logger.error(f"Failed to get GitHub user info: {user_response.text}")
                raise HTTPException(status_code=400, detail="Failed to get user information")

            user_data = user_response.json()

            # Get primary email
            emails_response = await client.get(self.EMAILS_URL, headers=headers)
            primary_email = None
            email_verified = False

            if emails_response.status_code == 200:
                emails = emails_response.json()
                for email in emails:
                    if email.get('primary'):
                        primary_email = email['email']
                        email_verified = email.get('verified', False)
                        break

            return {
                'provider': 'github',
                'provider_user_id': str(user_data['id']),
                'email': primary_email or user_data.get('email'),
                'name': user_data.get('name'),
                'username': user_data.get('login'),
                'picture': user_data.get('avatar_url'),
                'email_verified': email_verified
            }


class OAuthManager:
    """Manages OAuth providers and state"""

    def __init__(self):
        self.providers: Dict[str, OAuthProvider] = {}
        self.states: Dict[str, Dict[str, Any]] = {}  # In production, use Redis

        # Initialize providers from environment
        self._init_providers()

    def _init_providers(self):
        """Initialize OAuth providers from environment variables"""
        # Google OAuth
        google_client_id = os.getenv('GOOGLE_CLIENT_ID')
        google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        if google_client_id and google_client_secret:
            self.providers['google'] = GoogleOAuth(
                client_id=google_client_id,
                client_secret=google_client_secret,
                redirect_uri=os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/api/auth/callback/google')
            )
            logger.info("Google OAuth provider initialized")

        # GitHub OAuth
        github_client_id = os.getenv('GITHUB_CLIENT_ID')
        github_client_secret = os.getenv('GITHUB_CLIENT_SECRET')
        if github_client_id and github_client_secret:
            self.providers['github'] = GitHubOAuth(
                client_id=github_client_id,
                client_secret=github_client_secret,
                redirect_uri=os.getenv('GITHUB_REDIRECT_URI', 'http://localhost:8000/api/auth/callback/github')
            )
            logger.info("GitHub OAuth provider initialized")

    def get_provider(self, provider_name: str) -> OAuthProvider:
        """Get OAuth provider by name"""
        if provider_name not in self.providers:
            raise HTTPException(status_code=400, detail=f"OAuth provider {provider_name} not configured")
        return self.providers[provider_name]

    def create_authorization_url(self, provider_name: str, redirect_url: Optional[str] = None) -> Dict[str, str]:
        """Create authorization URL with state"""
        provider = self.get_provider(provider_name)
        state = provider.generate_state()

        # Store state with metadata (expires in 10 minutes)
        self.states[state] = {
            'provider': provider_name,
            'redirect_url': redirect_url,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        }

        # Generate PKCE for supported providers
        if isinstance(provider, GoogleOAuth):
            verifier, challenge = provider.generate_pkce()
            self.states[state]['code_verifier'] = verifier
            auth_url = provider.get_authorize_url(state, challenge)
        else:
            auth_url = provider.get_authorize_url(state)

        return {
            'auth_url': auth_url,
            'state': state
        }

    def verify_state(self, state: str) -> Dict[str, Any]:
        """Verify OAuth state parameter"""
        if state not in self.states:
            raise HTTPException(status_code=400, detail="Invalid OAuth state")

        state_data = self.states[state]

        # Check expiration
        expires_at = datetime.fromisoformat(state_data['expires_at'])
        if datetime.utcnow() > expires_at:
            del self.states[state]
            raise HTTPException(status_code=400, detail="OAuth state expired")

        # Remove state after verification (one-time use)
        del self.states[state]
        return state_data

    async def handle_callback(self, provider_name: str, code: str, state: str) -> Dict[str, Any]:
        """Handle OAuth callback"""
        # Verify state
        state_data = self.verify_state(state)
        if state_data['provider'] != provider_name:
            raise HTTPException(status_code=400, detail="Provider mismatch")

        provider = self.get_provider(provider_name)

        # Exchange code for tokens
        code_verifier = state_data.get('code_verifier')
        tokens = await provider.exchange_code(code, code_verifier=code_verifier)

        # Get user info
        user_info = await provider.get_user_info(tokens['access_token'])

        # Add tokens to user info
        user_info['access_token'] = tokens['access_token']
        user_info['refresh_token'] = tokens.get('refresh_token')
        user_info['expires_in'] = tokens.get('expires_in')
        user_info['redirect_url'] = state_data.get('redirect_url')

        return user_info

    def cleanup_expired_states(self):
        """Clean up expired OAuth states"""
        now = datetime.utcnow()
        expired_states = []

        for state, data in self.states.items():
            expires_at = datetime.fromisoformat(data['expires_at'])
            if now > expires_at:
                expired_states.append(state)

        for state in expired_states:
            del self.states[state]

        if expired_states:
            logger.info(f"Cleaned up {len(expired_states)} expired OAuth states")


# Global OAuth manager instance
oauth_manager = OAuthManager()