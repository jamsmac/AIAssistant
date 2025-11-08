"""
API Gateway Router
Endpoints for managing data source connections and syncing data
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import asyncpg
import json

from ..gateway import RESTConnector, JSONConnector, ConnectionConfig, ConnectionStatus
from ..db_pool import get_db_pool


router = APIRouter(prefix="/api/gateway", tags=["gateway"])


# ============================================================================
# Pydantic Models
# ============================================================================

class ConnectionCreate(BaseModel):
    name: str
    type: str  # 'rest', 'json', 'sql', 'graphql', 'csv', 'webhook'
    description: Optional[str] = None
    config: Dict[str, Any]
    credentials: Optional[Dict[str, Any]] = None
    auto_sync: bool = False
    sync_frequency: str = "manual"


class ConnectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    credentials: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    auto_sync: Optional[bool] = None
    sync_frequency: Optional[str] = None


class ConnectionResponse(BaseModel):
    id: str
    name: str
    type: str
    description: Optional[str]
    status: str
    last_sync: Optional[datetime]
    auto_sync: bool
    sync_frequency: str
    error_count: int
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime


class SyncRequest(BaseModel):
    mapping_id: Optional[str] = None
    params: Optional[Dict[str, Any]] = None


class SyncHistoryResponse(BaseModel):
    id: str
    connection_id: str
    sync_type: str
    records_fetched: int
    records_processed: int
    records_success: int
    records_failed: int
    success: bool
    error_message: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: int


class DataMappingCreate(BaseModel):
    connection_id: str
    name: str
    source_schema: Dict[str, Any]
    target_table: Optional[str] = None
    target_schema: Dict[str, Any]
    transformation_rules: Optional[Dict[str, Any]] = None
    filter_rules: Optional[Dict[str, Any]] = None


class WebhookCreate(BaseModel):
    connection_id: str
    name: str
    endpoint_path: str
    secret_token: Optional[str] = None
    http_method: str = "POST"
    expected_headers: Optional[Dict[str, Any]] = None
    payload_schema: Optional[Dict[str, Any]] = None


# ============================================================================
# Connection Management Endpoints
# ============================================================================

@router.post("/connections", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_connection(
    connection_data: ConnectionCreate,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Create a new gateway connection
    """
    try:
        # Create connection config
        config = ConnectionConfig(
            name=connection_data.name,
            type=connection_data.type,
            description=connection_data.description or "",
            config=connection_data.config,
            credentials=connection_data.credentials or {},
            auto_sync=connection_data.auto_sync,
            sync_frequency=connection_data.sync_frequency
        )

        # Create appropriate connector
        connector = _create_connector(config, pool)

        # Test connection
        connection_ok = await connector.test_connection()

        if not connection_ok:
            config.status = ConnectionStatus.ERROR
        else:
            config.status = ConnectionStatus.ACTIVE

        # Save to database
        connection_id = await connector.save_connection()

        # Fetch and return the created connection
        return await get_connection(connection_id, pool)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create connection: {str(e)}"
        )


@router.get("/connections", response_model=List[ConnectionResponse])
async def list_connections(
    type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    List all gateway connections with optional filtering
    """
    try:
        conditions = []
        params = []
        param_count = 1

        if type:
            conditions.append(f"type = ${param_count}")
            params.append(type)
            param_count += 1

        if status:
            conditions.append(f"status = ${param_count}")
            params.append(status)
            param_count += 1

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query = f"""
        SELECT * FROM gateway_connections
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ${param_count} OFFSET ${param_count + 1}
        """
        params.extend([limit, offset])

        rows = await pool.fetch(query, *params)

        return [
            ConnectionResponse(
                id=str(row['id']),
                name=row['name'],
                type=row['type'],
                description=row['description'],
                status=row['status'],
                last_sync=row['last_sync'],
                auto_sync=row['auto_sync'],
                sync_frequency=row['sync_frequency'],
                error_count=row['error_count'],
                last_error=row['last_error'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            for row in rows
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list connections: {str(e)}"
        )


@router.get("/connections/{connection_id}", response_model=ConnectionResponse)
async def get_connection(
    connection_id: str,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Get a specific gateway connection by ID
    """
    try:
        query = "SELECT * FROM gateway_connections WHERE id = $1"
        row = await pool.fetchrow(query, connection_id)

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Connection {connection_id} not found"
            )

        return ConnectionResponse(
            id=str(row['id']),
            name=row['name'],
            type=row['type'],
            description=row['description'],
            status=row['status'],
            last_sync=row['last_sync'],
            auto_sync=row['auto_sync'],
            sync_frequency=row['sync_frequency'],
            error_count=row['error_count'],
            last_error=row['last_error'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get connection: {str(e)}"
        )


@router.patch("/connections/{connection_id}", response_model=ConnectionResponse)
async def update_connection(
    connection_id: str,
    update_data: ConnectionUpdate,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Update a gateway connection
    """
    try:
        # Build update query dynamically
        updates = []
        params = []
        param_count = 1

        if update_data.name is not None:
            updates.append(f"name = ${param_count}")
            params.append(update_data.name)
            param_count += 1

        if update_data.description is not None:
            updates.append(f"description = ${param_count}")
            params.append(update_data.description)
            param_count += 1

        if update_data.config is not None:
            updates.append(f"config = ${param_count}")
            params.append(json.dumps(update_data.config))
            param_count += 1

        if update_data.status is not None:
            updates.append(f"status = ${param_count}")
            params.append(update_data.status)
            param_count += 1

        if update_data.auto_sync is not None:
            updates.append(f"auto_sync = ${param_count}")
            params.append(update_data.auto_sync)
            param_count += 1

        if update_data.sync_frequency is not None:
            updates.append(f"sync_frequency = ${param_count}")
            params.append(update_data.sync_frequency)
            param_count += 1

        if not updates:
            return await get_connection(connection_id, pool)

        updates.append("updated_at = CURRENT_TIMESTAMP")

        query = f"""
        UPDATE gateway_connections
        SET {', '.join(updates)}
        WHERE id = ${param_count}
        RETURNING id
        """
        params.append(connection_id)

        result = await pool.fetchrow(query, *params)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Connection {connection_id} not found"
            )

        return await get_connection(connection_id, pool)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update connection: {str(e)}"
        )


@router.delete("/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: str,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Delete a gateway connection
    """
    try:
        query = "DELETE FROM gateway_connections WHERE id = $1 RETURNING id"
        result = await pool.fetchrow(query, connection_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Connection {connection_id} not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete connection: {str(e)}"
        )


# ============================================================================
# Data Synchronization Endpoints
# ============================================================================

@router.post("/connections/{connection_id}/test")
async def test_connection(
    connection_id: str,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Test a gateway connection
    """
    try:
        connector = await _load_connector(connection_id, pool)
        success = await connector.test_connection()

        return {
            "success": success,
            "message": "Connection successful" if success else "Connection failed"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test connection: {str(e)}"
        )


@router.post("/connections/{connection_id}/sync")
async def sync_connection(
    connection_id: str,
    sync_request: Optional[SyncRequest] = None,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Synchronize data from a gateway connection
    """
    try:
        connector = await _load_connector(connection_id, pool)

        params = sync_request.params if sync_request and sync_request.params else {}
        mapping_id = sync_request.mapping_id if sync_request else None

        result = await connector.sync(mapping_id=mapping_id, **params)

        return {
            "success": result.success,
            "records_fetched": result.records_fetched,
            "records_processed": result.records_processed,
            "records_success": result.records_success,
            "records_failed": result.records_failed,
            "duration_ms": result.duration_ms,
            "error_message": result.error_message
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync connection: {str(e)}"
        )


@router.post("/connections/{connection_id}/fetch")
async def fetch_data(
    connection_id: str,
    params: Optional[Dict[str, Any]] = None,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Fetch data from connection without saving to database
    """
    try:
        connector = await _load_connector(connection_id, pool)

        fetch_params = params or {}
        result = await connector.fetch_data(**fetch_params)

        if not result.success:
            return {
                "success": False,
                "error_message": result.error_message,
                "data": None
            }

        return {
            "success": True,
            "data": result.data,
            "records_fetched": result.records_fetched,
            "duration_ms": result.duration_ms
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch data: {str(e)}"
        )


@router.get("/connections/{connection_id}/history", response_model=List[SyncHistoryResponse])
async def get_sync_history(
    connection_id: str,
    limit: int = 50,
    offset: int = 0,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Get sync history for a connection
    """
    try:
        query = """
        SELECT * FROM gateway_sync_history
        WHERE connection_id = $1
        ORDER BY started_at DESC
        LIMIT $2 OFFSET $3
        """
        rows = await pool.fetch(query, connection_id, limit, offset)

        return [
            SyncHistoryResponse(
                id=str(row['id']),
                connection_id=str(row['connection_id']),
                sync_type=row['sync_type'],
                records_fetched=row['records_fetched'],
                records_processed=row['records_processed'],
                records_success=row['records_success'],
                records_failed=row['records_failed'],
                success=row['success'],
                error_message=row['error_message'],
                started_at=row['started_at'],
                completed_at=row['completed_at'],
                duration_ms=row['duration_ms']
            )
            for row in rows
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync history: {str(e)}"
        )


# ============================================================================
# Statistics and Analytics
# ============================================================================

@router.get("/stats")
async def get_gateway_stats(pool: asyncpg.Pool = Depends(get_db_pool)):
    """
    Get overall gateway statistics
    """
    try:
        stats_query = """
        SELECT
            COUNT(*) as total_connections,
            COUNT(CASE WHEN status = 'active' THEN 1 END) as active_connections,
            COUNT(CASE WHEN status = 'error' THEN 1 END) as error_connections,
            SUM(error_count) as total_errors
        FROM gateway_connections
        """
        stats = await pool.fetchrow(stats_query)

        sync_query = """
        SELECT
            COUNT(*) as total_syncs,
            COUNT(CASE WHEN success THEN 1 END) as successful_syncs,
            SUM(records_fetched) as total_records_fetched,
            AVG(duration_ms) as avg_duration_ms
        FROM gateway_sync_history
        WHERE started_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
        """
        sync_stats = await pool.fetchrow(sync_query)

        return {
            "connections": {
                "total": stats['total_connections'] or 0,
                "active": stats['active_connections'] or 0,
                "errors": stats['error_connections'] or 0,
                "total_error_count": stats['total_errors'] or 0
            },
            "syncs_24h": {
                "total": sync_stats['total_syncs'] or 0,
                "successful": sync_stats['successful_syncs'] or 0,
                "records_fetched": sync_stats['total_records_fetched'] or 0,
                "avg_duration_ms": float(sync_stats['avg_duration_ms']) if sync_stats['avg_duration_ms'] else 0
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


# ============================================================================
# Helper Functions
# ============================================================================

def _create_connector(config: ConnectionConfig, pool: asyncpg.Pool):
    """Create appropriate connector based on type"""
    if config.type == 'rest':
        return RESTConnector(config, pool)
    elif config.type == 'json':
        return JSONConnector(config, pool)
    # Add more connector types here
    else:
        raise ValueError(f"Unsupported connector type: {config.type}")


async def _load_connector(connection_id: str, pool: asyncpg.Pool):
    """Load a connector from database"""
    query = "SELECT * FROM gateway_connections WHERE id = $1"
    row = await pool.fetchrow(query, connection_id)

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection {connection_id} not found"
        )

    config = ConnectionConfig(
        id=str(row['id']),
        name=row['name'],
        type=row['type'],
        description=row['description'],
        config=json.loads(row['config']) if row['config'] else {},
        credentials={},
        status=ConnectionStatus(row['status']),
        auto_sync=row['auto_sync'],
        sync_frequency=row['sync_frequency']
    )

    connector = _create_connector(config, pool)

    # Decrypt credentials if present
    if row['credentials_encrypted']:
        config.credentials = connector._decrypt_credentials(row['credentials_encrypted'])

    return connector
