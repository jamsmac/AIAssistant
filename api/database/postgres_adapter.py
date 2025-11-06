"""
PostgreSQL Database Adapter with Connection Pooling
Secure implementation with proper query parameterization
"""
import os
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncpg
from asyncpg.pool import Pool
import json
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class PostgresAdapter:
    """Thread-safe PostgreSQL adapter with connection pooling"""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")

        self.pool: Optional[Pool] = None
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initialize connection pool"""
        async with self._lock:
            if self.pool is None:
                self.pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=5,
                    max_size=20,
                    max_inactive_connection_lifetime=300,
                    command_timeout=60,
                    server_settings={
                        'application_name': 'aiassistant',
                        'jit': 'off'
                    }
                )
                logger.info("PostgreSQL connection pool initialized")

    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("PostgreSQL connection pool closed")

    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool"""
        if not self.pool:
            await self.initialize()

        async with self.pool.acquire() as connection:
            yield connection

    @asynccontextmanager
    async def transaction(self):
        """Execute operations in a transaction"""
        async with self.acquire() as conn:
            async with conn.transaction():
                yield conn

    # User Management
    async def create_user(self, email: str, password_hash: str, **kwargs) -> Dict[str, Any]:
        """Create a new user"""
        async with self.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO users (email, password_hash, created_at, updated_at, is_active, email_verified)
                VALUES ($1, $2, NOW(), NOW(), true, false)
                RETURNING id, email, created_at, updated_at, is_active, email_verified
            """, email, password_hash)

            return dict(row)

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        async with self.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, email, password_hash, created_at, updated_at,
                       is_active, email_verified, two_factor_enabled, last_login_at
                FROM users
                WHERE email = $1
            """, email)

            return dict(row) if row else None

    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        async with self.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, email, created_at, updated_at,
                       is_active, email_verified, two_factor_enabled, last_login_at
                FROM users
                WHERE id = $1
            """, user_id)

            return dict(row) if row else None

    async def update_user_login(self, user_id: int):
        """Update user's last login timestamp"""
        async with self.acquire() as conn:
            await conn.execute("""
                UPDATE users
                SET last_login_at = NOW()
                WHERE id = $1
            """, user_id)

    # OAuth Management
    async def create_oauth_account(self, user_id: int, provider: str,
                                  provider_user_id: str, access_token: str,
                                  refresh_token: Optional[str] = None,
                                  expires_at: Optional[datetime] = None) -> Dict[str, Any]:
        """Create OAuth account link"""
        async with self.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO oauth_accounts
                (user_id, provider, provider_user_id, access_token,
                 refresh_token, expires_at, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
                RETURNING id, user_id, provider, provider_user_id, created_at
            """, user_id, provider, provider_user_id, access_token,
                refresh_token, expires_at)

            return dict(row)

    async def get_oauth_account(self, provider: str, provider_user_id: str) -> Optional[Dict[str, Any]]:
        """Get OAuth account by provider and provider user ID"""
        async with self.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT o.*, u.email, u.is_active
                FROM oauth_accounts o
                JOIN users u ON o.user_id = u.id
                WHERE o.provider = $1 AND o.provider_user_id = $2
            """, provider, provider_user_id)

            return dict(row) if row else None

    # Session Management
    async def create_session(self, user_id: int, token: str, csrf_token: str,
                           expires_at: datetime, ip_address: Optional[str] = None,
                           user_agent: Optional[str] = None) -> Dict[str, Any]:
        """Create a new session"""
        async with self.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO sessions
                (user_id, token, csrf_token, expires_at, ip_address, user_agent, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                RETURNING id, user_id, token, csrf_token, expires_at, created_at
            """, user_id, token, csrf_token, expires_at, ip_address, user_agent)

            return dict(row)

    async def get_session(self, token: str) -> Optional[Dict[str, Any]]:
        """Get session by token"""
        async with self.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT s.*, u.email, u.is_active
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.token = $1 AND s.expires_at > NOW() AND s.revoked = false
            """, token)

            return dict(row) if row else None

    async def revoke_session(self, token: str):
        """Revoke a session"""
        async with self.acquire() as conn:
            await conn.execute("""
                UPDATE sessions
                SET revoked = true, revoked_at = NOW()
                WHERE token = $1
            """, token)

    async def verify_csrf_token(self, session_token: str, csrf_token: str) -> bool:
        """Verify CSRF token for a session"""
        async with self.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT 1 FROM sessions
                WHERE token = $1 AND csrf_token = $2
                AND expires_at > NOW() AND revoked = false
            """, session_token, csrf_token)

            return row is not None

    # Chat History
    async def create_chat_session(self, user_id: int, title: str = "New Chat") -> Dict[str, Any]:
        """Create a new chat session"""
        async with self.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO chat_sessions (user_id, title, created_at, updated_at)
                VALUES ($1, $2, NOW(), NOW())
                RETURNING id, user_id, title, created_at, updated_at
            """, user_id, title)

            return dict(row)

    async def add_chat_message(self, session_id: int, role: str,
                              content: str, model: Optional[str] = None,
                              metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Add a message to chat history"""
        async with self.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO chat_messages
                (session_id, role, content, model, metadata, created_at)
                VALUES ($1, $2, $3, $4, $5, NOW())
                RETURNING id, session_id, role, content, model, created_at
            """, session_id, role, content, model,
                json.dumps(metadata) if metadata else None)

            return dict(row)

    async def get_chat_history(self, user_id: int, session_id: int,
                              limit: int = 50) -> List[Dict[str, Any]]:
        """Get chat history for a session"""
        async with self.acquire() as conn:
            # Verify user owns the session
            session = await conn.fetchrow("""
                SELECT 1 FROM chat_sessions
                WHERE id = $1 AND user_id = $2
            """, session_id, user_id)

            if not session:
                return []

            rows = await conn.fetch("""
                SELECT id, role, content, model, metadata, created_at
                FROM chat_messages
                WHERE session_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """, session_id, limit)

            return [dict(row) for row in reversed(rows)]

    # Projects and Databases
    async def create_project(self, user_id: int, name: str,
                           description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new project"""
        async with self.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO projects (user_id, name, description, created_at, updated_at)
                VALUES ($1, $2, $3, NOW(), NOW())
                RETURNING id, user_id, name, description, created_at, updated_at
            """, user_id, name, description)

            return dict(row)

    async def get_user_projects(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all projects for a user"""
        async with self.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, name, description, created_at, updated_at
                FROM projects
                WHERE user_id = $1
                ORDER BY updated_at DESC
            """, user_id)

            return [dict(row) for row in rows]

    # Model Rankings
    async def update_model_ranking(self, model: str, provider: str,
                                  score: float, response_time: float):
        """Update model ranking based on performance"""
        async with self.acquire() as conn:
            await conn.execute("""
                INSERT INTO model_rankings
                (model, provider, total_score, total_requests, avg_response_time, last_updated)
                VALUES ($1, $2, $3, 1, $4, NOW())
                ON CONFLICT (model, provider) DO UPDATE
                SET total_score = model_rankings.total_score + $3,
                    total_requests = model_rankings.total_requests + 1,
                    avg_response_time = (model_rankings.avg_response_time * model_rankings.total_requests + $4)
                                       / (model_rankings.total_requests + 1),
                    last_updated = NOW()
            """, model, provider, score, response_time)

    async def get_model_rankings(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top ranked models"""
        async with self.acquire() as conn:
            rows = await conn.fetch("""
                SELECT model, provider,
                       total_score / NULLIF(total_requests, 0) as avg_score,
                       total_requests, avg_response_time
                FROM model_rankings
                ORDER BY avg_score DESC NULLS LAST
                LIMIT $1
            """, limit)

            return [dict(row) for row in rows]

    # Migration Support
    async def create_tables(self):
        """Create all required tables"""
        async with self.transaction() as conn:
            # Users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255),
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    is_active BOOLEAN DEFAULT true,
                    email_verified BOOLEAN DEFAULT false,
                    two_factor_enabled BOOLEAN DEFAULT false,
                    two_factor_secret VARCHAR(255),
                    last_login_at TIMESTAMP
                )
            """)

            # OAuth accounts
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS oauth_accounts (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    provider VARCHAR(50) NOT NULL,
                    provider_user_id VARCHAR(255) NOT NULL,
                    access_token TEXT,
                    refresh_token TEXT,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    UNIQUE(provider, provider_user_id)
                )
            """)

            # Sessions
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    token VARCHAR(255) UNIQUE NOT NULL,
                    csrf_token VARCHAR(255) NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    ip_address INET,
                    user_agent TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    revoked BOOLEAN DEFAULT false,
                    revoked_at TIMESTAMP,
                    INDEX idx_sessions_token (token),
                    INDEX idx_sessions_user_id (user_id)
                )
            """)

            # Chat sessions
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    title VARCHAR(255),
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """)

            # Chat messages
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id SERIAL PRIMARY KEY,
                    session_id INTEGER REFERENCES chat_sessions(id) ON DELETE CASCADE,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    model VARCHAR(100),
                    metadata JSONB,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    INDEX idx_messages_session (session_id)
                )
            """)

            # Projects
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """)

            # Model rankings
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS model_rankings (
                    model VARCHAR(100),
                    provider VARCHAR(50),
                    total_score FLOAT DEFAULT 0,
                    total_requests INTEGER DEFAULT 0,
                    avg_response_time FLOAT DEFAULT 0,
                    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (model, provider)
                )
            """)

            logger.info("All PostgreSQL tables created successfully")


# Global instance
_db: Optional[PostgresAdapter] = None


async def get_postgres_db() -> PostgresAdapter:
    """Get or create PostgreSQL database instance"""
    global _db
    if _db is None:
        _db = PostgresAdapter()
        await _db.initialize()
    return _db


async def close_postgres_db():
    """Close PostgreSQL database connection"""
    global _db
    if _db:
        await _db.close()
        _db = None