"""
Base Connector Class for API Gateway
All data source connectors inherit from this base class
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import asyncpg
import json
import os


class ConnectionStatus(Enum):
    """Connection status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    TESTING = "testing"


class SyncType(Enum):
    """Sync operation type"""
    FULL = "full"
    INCREMENTAL = "incremental"
    MANUAL = "manual"


@dataclass
class ConnectionConfig:
    """Connection configuration data class"""
    id: Optional[str] = None
    name: str = ""
    type: str = ""
    description: str = ""
    config: Dict[str, Any] = None
    credentials: Dict[str, Any] = None
    status: ConnectionStatus = ConnectionStatus.INACTIVE
    auto_sync: bool = False
    sync_frequency: str = "manual"

    def __post_init__(self):
        if self.config is None:
            self.config = {}
        if self.credentials is None:
            self.credentials = {}


@dataclass
class SyncResult:
    """Result of a sync operation"""
    success: bool
    records_fetched: int = 0
    records_processed: int = 0
    records_success: int = 0
    records_failed: int = 0
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    duration_ms: int = 0
    data: Optional[List[Dict[str, Any]]] = None

    def __post_init__(self):
        if self.data is None:
            self.data = []


class BaseConnector(ABC):
    """
    Abstract base class for all data source connectors

    All connectors must implement:
    - test_connection(): Test if connection is valid
    - fetch_data(): Fetch data from external source
    - sync(): Synchronize data with internal database
    """

    def __init__(self, config: ConnectionConfig, db_pool: asyncpg.Pool):
        """
        Initialize connector

        Args:
            config: Connection configuration
            db_pool: Database connection pool
        """
        self.config = config
        self.db_pool = db_pool
        self.last_sync: Optional[datetime] = None
        self.error_count: int = 0

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test if the connection is valid and working

        Returns:
            bool: True if connection is successful, False otherwise
        """
        pass

    @abstractmethod
    async def fetch_data(self, **kwargs) -> SyncResult:
        """
        Fetch data from the external source

        Args:
            **kwargs: Connector-specific parameters

        Returns:
            SyncResult: Result containing fetched data and metadata
        """
        pass

    @abstractmethod
    async def sync(self, mapping_id: Optional[str] = None, **kwargs) -> SyncResult:
        """
        Synchronize data from external source to internal database

        Args:
            mapping_id: Optional data mapping ID to use
            **kwargs: Connector-specific parameters

        Returns:
            SyncResult: Result of sync operation
        """
        pass

    async def save_connection(self) -> str:
        """
        Save or update connection configuration in database

        Returns:
            str: Connection ID
        """
        try:
            if self.config.id:
                # Update existing connection
                query = """
                UPDATE gateway_connections
                SET name = $1, description = $2, config = $3,
                    credentials_encrypted = $4, status = $5,
                    auto_sync = $6, sync_frequency = $7,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $8
                RETURNING id
                """
                result = await self.db_pool.fetchrow(
                    query,
                    self.config.name,
                    self.config.description,
                    json.dumps(self.config.config),
                    self._encrypt_credentials(self.config.credentials),
                    self.config.status.value,
                    self.config.auto_sync,
                    self.config.sync_frequency,
                    self.config.id
                )
                return str(result['id'])
            else:
                # Create new connection
                query = """
                INSERT INTO gateway_connections
                (name, type, description, config, credentials_encrypted,
                 status, auto_sync, sync_frequency)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
                """
                result = await self.db_pool.fetchrow(
                    query,
                    self.config.name,
                    self.config.type,
                    self.config.description,
                    json.dumps(self.config.config),
                    self._encrypt_credentials(self.config.credentials),
                    self.config.status.value,
                    self.config.auto_sync,
                    self.config.sync_frequency
                )
                self.config.id = str(result['id'])
                return self.config.id

        except Exception as e:
            raise Exception(f"Failed to save connection: {str(e)}")

    async def log_sync_history(self, result: SyncResult, sync_type: SyncType = SyncType.MANUAL,
                               triggered_by: str = "manual") -> None:
        """
        Log sync operation to history

        Args:
            result: Sync result to log
            sync_type: Type of sync operation
            triggered_by: Who/what triggered the sync
        """
        if not self.config.id:
            return

        try:
            query = """
            INSERT INTO gateway_sync_history
            (connection_id, sync_type, records_fetched, records_processed,
             records_success, records_failed, success, error_message,
             error_details, completed_at, duration_ms, triggered_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, CURRENT_TIMESTAMP, $10, $11)
            """
            await self.db_pool.execute(
                query,
                self.config.id,
                sync_type.value,
                result.records_fetched,
                result.records_processed,
                result.records_success,
                result.records_failed,
                result.success,
                result.error_message,
                json.dumps(result.error_details) if result.error_details else None,
                result.duration_ms,
                triggered_by
            )
        except Exception as e:
            print(f"Failed to log sync history: {str(e)}")

    async def get_rate_limit(self) -> Optional[Dict[str, Any]]:
        """
        Get current rate limit status for this connection

        Returns:
            Dict with rate limit info or None
        """
        if not self.config.id:
            return None

        try:
            query = """
            SELECT * FROM gateway_rate_limits
            WHERE connection_id = $1
            AND window_end > CURRENT_TIMESTAMP
            ORDER BY window_end DESC
            LIMIT 1
            """
            result = await self.db_pool.fetchrow(query, self.config.id)
            return dict(result) if result else None
        except Exception:
            return None

    async def check_rate_limit(self, max_requests: int, window_seconds: int = 60) -> bool:
        """
        Check if we're within rate limits

        Args:
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            bool: True if within limits, False if exceeded
        """
        current_limit = await self.get_rate_limit()

        if not current_limit:
            # Create new rate limit window
            await self._create_rate_limit_window(max_requests, window_seconds)
            return True

        if current_limit['current_count'] >= max_requests:
            return False

        # Increment counter
        await self._increment_rate_limit(current_limit['id'])
        return True

    async def _create_rate_limit_window(self, max_requests: int, window_seconds: int):
        """Create a new rate limit window"""
        if not self.config.id:
            return

        query = """
        INSERT INTO gateway_rate_limits
        (connection_id, limit_type, max_requests, current_count, window_start, window_end)
        VALUES ($1, 'custom', $2, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '%s seconds')
        """ % window_seconds

        await self.db_pool.execute(query, self.config.id, max_requests)

    async def _increment_rate_limit(self, limit_id: str):
        """Increment rate limit counter"""
        query = """
        UPDATE gateway_rate_limits
        SET current_count = current_count + 1
        WHERE id = $1
        """
        await self.db_pool.execute(query, limit_id)

    async def cache_data(self, cache_key: str, data: Any, ttl_seconds: int = 3600) -> None:
        """
        Cache data for faster retrieval

        Args:
            cache_key: Unique key for this data
            data: Data to cache (will be JSON serialized)
            ttl_seconds: Time to live in seconds
        """
        if not self.config.id:
            return

        try:
            query = """
            INSERT INTO gateway_data_cache
            (connection_id, cache_key, data, ttl_seconds, expires_at)
            VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP + INTERVAL '%s seconds')
            ON CONFLICT (connection_id, cache_key)
            DO UPDATE SET
                data = EXCLUDED.data,
                created_at = CURRENT_TIMESTAMP,
                expires_at = CURRENT_TIMESTAMP + INTERVAL '%s seconds',
                access_count = gateway_data_cache.access_count + 1
            """ % (ttl_seconds, ttl_seconds)

            await self.db_pool.execute(
                query,
                self.config.id,
                cache_key,
                json.dumps(data)
            )
        except Exception as e:
            print(f"Failed to cache data: {str(e)}")

    async def get_cached_data(self, cache_key: str) -> Optional[Any]:
        """
        Retrieve cached data if available and not expired

        Args:
            cache_key: Cache key to look up

        Returns:
            Cached data or None if not found/expired
        """
        if not self.config.id:
            return None

        try:
            query = """
            SELECT data FROM gateway_data_cache
            WHERE connection_id = $1
            AND cache_key = $2
            AND expires_at > CURRENT_TIMESTAMP
            """
            result = await self.db_pool.fetchrow(query, self.config.id, cache_key)

            if result:
                # Update access stats
                await self.db_pool.execute("""
                    UPDATE gateway_data_cache
                    SET access_count = access_count + 1,
                        last_accessed = CURRENT_TIMESTAMP
                    WHERE connection_id = $1 AND cache_key = $2
                """, self.config.id, cache_key)

                return json.loads(result['data'])

            return None
        except Exception:
            return None

    def _encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """
        Encrypt credentials (simple base64 for now, should use proper encryption)

        Args:
            credentials: Credentials dictionary

        Returns:
            str: Encrypted credentials string
        """
        import base64
        if not credentials:
            return ""

        # In production, use proper encryption with Fernet or similar
        creds_json = json.dumps(credentials)
        return base64.b64encode(creds_json.encode()).decode()

    def _decrypt_credentials(self, encrypted: str) -> Dict[str, Any]:
        """
        Decrypt credentials

        Args:
            encrypted: Encrypted credentials string

        Returns:
            Dict: Decrypted credentials
        """
        import base64
        if not encrypted:
            return {}

        try:
            decrypted = base64.b64decode(encrypted.encode()).decode()
            return json.loads(decrypted)
        except Exception:
            return {}

    @classmethod
    async def load_from_database(cls, connection_id: str, db_pool: asyncpg.Pool):
        """
        Load a connection from database by ID

        Args:
            connection_id: Connection UUID
            db_pool: Database pool

        Returns:
            BaseConnector instance
        """
        query = """
        SELECT * FROM gateway_connections WHERE id = $1
        """
        row = await db_pool.fetchrow(query, connection_id)

        if not row:
            raise Exception(f"Connection {connection_id} not found")

        config = ConnectionConfig(
            id=str(row['id']),
            name=row['name'],
            type=row['type'],
            description=row['description'],
            config=json.loads(row['config']) if row['config'] else {},
            credentials={},  # Will be decrypted
            status=ConnectionStatus(row['status']),
            auto_sync=row['auto_sync'],
            sync_frequency=row['sync_frequency']
        )

        # Create appropriate connector instance
        connector = cls(config, db_pool)

        # Decrypt credentials
        if row['credentials_encrypted']:
            config.credentials = connector._decrypt_credentials(row['credentials_encrypted'])

        return connector

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.config.name}', type='{self.config.type}')"

    def __repr__(self) -> str:
        return self.__str__()
