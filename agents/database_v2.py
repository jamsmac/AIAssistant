"""
Enhanced Database Module with Connection Pooling
High-performance database operations with connection pooling
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
import logging
from contextlib import contextmanager

from agents.database_pool import ConnectionPool, get_connection_pool

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "history.db"
DB_PATH.parent.mkdir(exist_ok=True)


class PooledDatabase:
    """
    Database class using connection pooling for better performance
    """

    def __init__(self, pool: ConnectionPool = None):
        """Initialize with connection pool"""
        self.pool = pool or get_connection_pool()
        self._init_db()

    def _init_db(self):
        """Initialize database tables"""
        with self.pool.acquire() as conn:
            # Create all necessary tables
            conn.executescript("""
                -- Requests table
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    response TEXT NOT NULL,
                    model TEXT NOT NULL,
                    task_type TEXT,
                    complexity INTEGER,
                    budget TEXT,
                    tokens INTEGER,
                    cost REAL,
                    error INTEGER DEFAULT 0,
                    user_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                -- Users table
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_login_at TEXT,
                    is_active INTEGER DEFAULT 1,
                    has_2fa INTEGER DEFAULT 0,
                    totp_secret TEXT,
                    backup_codes TEXT
                );

                -- Projects table
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    settings TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

                -- Databases table
                CREATE TABLE IF NOT EXISTS databases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    schema_json TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                -- Database records table
                CREATE TABLE IF NOT EXISTS database_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    database_id INTEGER NOT NULL,
                    data_json TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT,
                    FOREIGN KEY (database_id) REFERENCES databases(id) ON DELETE CASCADE
                );

                -- Workflows table
                CREATE TABLE IF NOT EXISTS workflows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    trigger_json TEXT NOT NULL,
                    actions_json TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

                -- Workflow executions table
                CREATE TABLE IF NOT EXISTS workflow_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT,
                    result_json TEXT,
                    error TEXT,
                    input_data TEXT,
                    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
                );

                -- Integration tokens table
                CREATE TABLE IF NOT EXISTS integration_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    service TEXT NOT NULL,
                    access_token TEXT NOT NULL,
                    refresh_token TEXT,
                    expires_at TEXT,
                    account_info TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT,
                    UNIQUE(user_id, service),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

                -- Chat sessions table
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

                -- Session messages table
                CREATE TABLE IF NOT EXISTS session_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    model TEXT,
                    tokens_used INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
                );

                -- Request cache table
                CREATE TABLE IF NOT EXISTS request_cache (
                    prompt_hash TEXT PRIMARY KEY,
                    prompt TEXT NOT NULL,
                    task_type TEXT,
                    response TEXT NOT NULL,
                    model TEXT NOT NULL,
                    tokens_used INTEGER,
                    cost REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    expires_at TEXT
                );

                -- AI model rankings table
                CREATE TABLE IF NOT EXISTS ai_model_rankings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    category TEXT NOT NULL,
                    rank INTEGER,
                    score REAL,
                    source TEXT,
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(model_name, category, source)
                );

                -- Create indexes for better performance
                CREATE INDEX IF NOT EXISTS idx_requests_user ON requests(user_id);
                CREATE INDEX IF NOT EXISTS idx_requests_timestamp ON requests(timestamp);
                CREATE INDEX IF NOT EXISTS idx_projects_user ON projects(user_id);
                CREATE INDEX IF NOT EXISTS idx_databases_project ON databases(project_id);
                CREATE INDEX IF NOT EXISTS idx_records_database ON database_records(database_id);
                CREATE INDEX IF NOT EXISTS idx_workflows_user ON workflows(user_id);
                CREATE INDEX IF NOT EXISTS idx_executions_workflow ON workflow_executions(workflow_id);
                CREATE INDEX IF NOT EXISTS idx_tokens_user ON integration_tokens(user_id);
                CREATE INDEX IF NOT EXISTS idx_sessions_user ON chat_sessions(user_id);
                CREATE INDEX IF NOT EXISTS idx_messages_session ON session_messages(session_id);
                CREATE INDEX IF NOT EXISTS idx_cache_hash ON request_cache(prompt_hash);
                CREATE INDEX IF NOT EXISTS idx_cache_expires ON request_cache(expires_at);
            """)

            logger.info("Database tables initialized with indexes")

    # User management methods
    def create_user(self, email: str, password_hash: str) -> int:
        """Create a new user"""
        query = "INSERT INTO users (email, password_hash) VALUES (?, ?)"
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (email.lower().strip(), password_hash))
            conn.commit()
            return cursor.lastrowid

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        query = """
            SELECT id, email, password_hash, created_at, last_login_at,
                   is_active, has_2fa, totp_secret
            FROM users WHERE email = ?
        """
        result = self.pool.execute(query, (email.lower().strip(),))
        if result:
            row = result[0]
            return {
                'id': row[0],
                'email': row[1],
                'password_hash': row[2],
                'created_at': row[3],
                'last_login_at': row[4],
                'is_active': bool(row[5]),
                'has_2fa': bool(row[6]),
                'totp_secret': row[7]
            }
        return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        query = """
            SELECT id, email, created_at, last_login_at, is_active, has_2fa
            FROM users WHERE id = ?
        """
        result = self.pool.execute(query, (user_id,))
        if result:
            row = result[0]
            return {
                'id': row[0],
                'email': row[1],
                'created_at': row[2],
                'last_login_at': row[3],
                'is_active': bool(row[4]),
                'has_2fa': bool(row[5])
            }
        return None

    def update_last_login(self, user_id: int):
        """Update user's last login time"""
        query = "UPDATE users SET last_login_at = ? WHERE id = ?"
        self.pool.execute(query, (datetime.now().isoformat(), user_id))

    # Project management methods
    def create_project(self, user_id: int, name: str, description: str = None, settings: str = None) -> int:
        """Create a new project"""
        query = """
            INSERT INTO projects (user_id, name, description, settings)
            VALUES (?, ?, ?, ?)
        """
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (user_id, name, description, settings))
            conn.commit()
            return cursor.lastrowid

    def get_user_projects(self, user_id: int) -> List[Dict]:
        """Get all projects for a user"""
        query = """
            SELECT id, user_id, name, description, settings, created_at, updated_at
            FROM projects WHERE user_id = ?
            ORDER BY created_at DESC
        """
        results = self.pool.execute(query, (user_id,))
        return [
            {
                'id': row[0],
                'user_id': row[1],
                'name': row[2],
                'description': row[3],
                'settings': row[4],
                'created_at': row[5],
                'updated_at': row[6]
            }
            for row in results
        ]

    def get_project(self, project_id: int, user_id: int) -> Optional[Dict]:
        """Get a specific project"""
        query = """
            SELECT id, user_id, name, description, settings, created_at, updated_at
            FROM projects WHERE id = ? AND user_id = ?
        """
        result = self.pool.execute(query, (project_id, user_id))
        if result:
            row = result[0]
            return {
                'id': row[0],
                'user_id': row[1],
                'name': row[2],
                'description': row[3],
                'settings': row[4],
                'created_at': row[5],
                'updated_at': row[6]
            }
        return None

    # Database operations
    def create_database(self, project_id: int, name: str, schema_json: str) -> int:
        """Create a new database in a project"""
        query = """
            INSERT INTO databases (project_id, name, schema_json)
            VALUES (?, ?, ?)
        """
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (project_id, name, schema_json))
            conn.commit()
            return cursor.lastrowid

    def get_project_databases(self, project_id: int) -> List[Dict]:
        """Get all databases for a project"""
        query = """
            SELECT id, project_id, name, schema_json, created_at, updated_at
            FROM databases WHERE project_id = ?
            ORDER BY created_at DESC
        """
        results = self.pool.execute(query, (project_id,))
        return [
            {
                'id': row[0],
                'project_id': row[1],
                'name': row[2],
                'schema_json': row[3],
                'created_at': row[4],
                'updated_at': row[5]
            }
            for row in results
        ]

    # Session management
    def create_chat_session(self, user_id: int, name: str, description: str = None) -> str:
        """Create a new chat session"""
        import uuid
        session_id = str(uuid.uuid4())
        query = """
            INSERT INTO chat_sessions (id, user_id, name, description)
            VALUES (?, ?, ?, ?)
        """
        self.pool.execute(query, (session_id, user_id, name, description))
        return session_id

    def get_user_sessions(self, user_id: int) -> List[Dict]:
        """Get all chat sessions for a user"""
        query = """
            SELECT s.id, s.name, s.description, s.created_at,
                   COUNT(m.id) as message_count
            FROM chat_sessions s
            LEFT JOIN session_messages m ON s.id = m.session_id
            WHERE s.user_id = ?
            GROUP BY s.id
            ORDER BY s.created_at DESC
        """
        results = self.pool.execute(query, (user_id,))
        return [
            {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'created_at': row[3],
                'message_count': row[4]
            }
            for row in results
        ]

    # Pool statistics
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        return self.pool.get_stats()


# Global instance
_pooled_db: Optional[PooledDatabase] = None


def get_pooled_db() -> PooledDatabase:
    """Get or create global pooled database instance"""
    global _pooled_db
    if _pooled_db is None:
        _pooled_db = PooledDatabase()
    return _pooled_db