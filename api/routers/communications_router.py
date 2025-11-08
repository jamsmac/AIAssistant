"""
Communications Router

REST API endpoints for the Communication Hub.
Manages messaging channels, conversations, and messages.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncpg
import logging

from ..db_pool import get_db_pool
from ..communications import (
    ChannelConfig,
    ChannelStatus,
    TelegramConnector,
    GmailConnector,
    WhatsAppConnector
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/communications", tags=["communications"])


# Pydantic Models

class ChannelCreate(BaseModel):
    type: str  # 'telegram', 'gmail', 'whatsapp', etc.
    name: str
    config: Dict[str, Any] = {}
    credentials: Dict[str, Any]
    auto_response_enabled: bool = False
    assigned_agent_id: Optional[str] = None


class ChannelUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    credentials: Optional[Dict[str, Any]] = None
    auto_response_enabled: Optional[bool] = None
    assigned_agent_id: Optional[str] = None
    status: Optional[str] = None


class MessageSend(BaseModel):
    conversation_id: str
    content: str
    message_type: str = "text"
    attachments: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}


class ChannelResponse(BaseModel):
    id: str
    type: str
    name: str
    config: Dict[str, Any]
    status: str
    assigned_agent_id: Optional[str]
    total_messages_received: int
    total_messages_sent: int
    auto_response_enabled: bool
    created_at: datetime
    updated_at: datetime


class ConversationResponse(BaseModel):
    id: str
    channel_id: str
    channel_name: str
    channel_type: str
    participant_id: str
    participant_name: str
    status: str
    unread_count: int
    last_message_at: Optional[datetime]
    last_message_preview: str
    assigned_agent_id: Optional[str]
    created_at: datetime


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    direction: str
    sender_id: str
    sender_name: str
    content: str
    message_type: str
    attachments: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    read_at: Optional[datetime]
    created_at: datetime


class StatsResponse(BaseModel):
    total_channels: int
    active_channels: int
    total_conversations: int
    active_conversations: int
    total_messages: int
    messages_today: int
    unread_messages: int


# Helper functions

def _create_connector(config: ChannelConfig, db_pool: asyncpg.Pool):
    """Create appropriate connector instance based on type"""
    if config.type == 'telegram':
        return TelegramConnector(config, db_pool)
    elif config.type == 'gmail':
        return GmailConnector(config, db_pool)
    elif config.type == 'whatsapp':
        return WhatsAppConnector(config, db_pool)
    else:
        raise ValueError(f"Unsupported channel type: {config.type}")


# Endpoints

@router.post("/channels", response_model=ChannelResponse)
async def create_channel(
    channel_data: ChannelCreate,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Create a new messaging channel

    Creates and tests connection to a messaging platform.
    """
    try:
        # Create config
        config = ChannelConfig(
            type=channel_data.type,
            name=channel_data.name,
            config=channel_data.config,
            credentials=channel_data.credentials,
            auto_response_enabled=channel_data.auto_response_enabled,
            assigned_agent_id=channel_data.assigned_agent_id
        )

        # Create connector
        connector = _create_connector(config, pool)

        # Test connection
        connected = await connector.connect()
        if not connected:
            raise HTTPException(status_code=400, detail="Failed to connect to channel")

        # Save to database
        channel_id = await connector.save_channel()

        # Get created channel
        return await get_channel(channel_id, pool)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating channel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/channels", response_model=List[ChannelResponse])
async def list_channels(
    type: Optional[str] = None,
    status: Optional[str] = None,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    List all messaging channels

    Optional filters by type and status.
    """
    try:
        query = "SELECT * FROM comm_channels WHERE 1=1"
        params = []

        if type:
            params.append(type)
            query += f" AND type = ${len(params)}"

        if status:
            params.append(status)
            query += f" AND status = ${len(params)}"

        query += " ORDER BY created_at DESC"

        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

            channels = []
            for row in rows:
                import json
                channels.append(ChannelResponse(
                    id=str(row['id']),
                    type=row['type'],
                    name=row['name'],
                    config=json.loads(row['config']) if row['config'] else {},
                    status=row['status'],
                    assigned_agent_id=str(row['assigned_agent_id']) if row['assigned_agent_id'] else None,
                    total_messages_received=row['total_messages_received'],
                    total_messages_sent=row['total_messages_sent'],
                    auto_response_enabled=row.get('auto_response_enabled', False),
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                ))

            return channels

    except Exception as e:
        logger.error(f"Error listing channels: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/channels/{channel_id}", response_model=ChannelResponse)
async def get_channel(channel_id: str, pool: asyncpg.Pool = Depends(get_db_pool)):
    """Get a specific channel by ID"""
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM comm_channels WHERE id = $1", channel_id)

            if not row:
                raise HTTPException(status_code=404, detail="Channel not found")

            import json
            return ChannelResponse(
                id=str(row['id']),
                type=row['type'],
                name=row['name'],
                config=json.loads(row['config']) if row['config'] else {},
                status=row['status'],
                assigned_agent_id=str(row['assigned_agent_id']) if row['assigned_agent_id'] else None,
                total_messages_received=row['total_messages_received'],
                total_messages_sent=row['total_messages_sent'],
                auto_response_enabled=row.get('auto_response_enabled', False),
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting channel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/channels/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    channel_id: str,
    channel_data: ChannelUpdate,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Update a channel"""
    try:
        updates = []
        params = []
        param_count = 1

        if channel_data.name is not None:
            params.append(channel_data.name)
            updates.append(f"name = ${param_count}")
            param_count += 1

        if channel_data.config is not None:
            import json
            params.append(json.dumps(channel_data.config))
            updates.append(f"config = ${param_count}")
            param_count += 1

        if channel_data.status is not None:
            params.append(channel_data.status)
            updates.append(f"status = ${param_count}")
            param_count += 1

        if channel_data.auto_response_enabled is not None:
            params.append(channel_data.auto_response_enabled)
            updates.append(f"auto_response_enabled = ${param_count}")
            param_count += 1

        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(channel_id)

        query = f"UPDATE comm_channels SET {', '.join(updates)} WHERE id = ${param_count}"

        async with pool.acquire() as conn:
            await conn.execute(query, *params)

        return await get_channel(channel_id, pool)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating channel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/channels/{channel_id}")
async def delete_channel(channel_id: str, pool: asyncpg.Pool = Depends(get_db_pool)):
    """Delete a channel"""
    try:
        async with pool.acquire() as conn:
            result = await conn.execute("DELETE FROM comm_channels WHERE id = $1", channel_id)

            if result == "DELETE 0":
                raise HTTPException(status_code=404, detail="Channel not found")

            return {"success": True, "message": "Channel deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting channel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/channels/{channel_id}/test")
async def test_channel(channel_id: str, pool: asyncpg.Pool = Depends(get_db_pool)):
    """Test connection to a channel"""
    try:
        # Get channel
        channel = await get_channel(channel_id, pool)

        # Create config
        import json
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM comm_channels WHERE id = $1", channel_id)
            credentials = json.loads(row['credentials_encrypted']) if row['credentials_encrypted'] else None

        config = ChannelConfig(
            id=channel_id,
            type=channel.type,
            name=channel.name,
            config=channel.config,
            credentials=credentials,
            status=ChannelStatus(channel.status)
        )

        # Create connector and test
        connector = _create_connector(config, pool)
        connected = await connector.connect()

        return {
            "success": connected,
            "status": "active" if connected else "error"
        }

    except Exception as e:
        logger.error(f"Error testing channel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    channel_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    List conversations (unified inbox)

    Shows all conversations across all channels or filtered by channel.
    """
    try:
        query = """
            SELECT c.*, ch.name as channel_name, ch.type as channel_type
            FROM comm_conversations c
            JOIN comm_channels ch ON c.channel_id = ch.id
            WHERE 1=1
        """
        params = []

        if channel_id:
            params.append(channel_id)
            query += f" AND c.channel_id = ${len(params)}"

        if status:
            params.append(status)
            query += f" AND c.status = ${len(params)}"

        query += f" ORDER BY c.last_message_at DESC LIMIT ${len(params) + 1}"
        params.append(limit)

        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

            conversations = []
            for row in rows:
                conversations.append(ConversationResponse(
                    id=str(row['id']),
                    channel_id=str(row['channel_id']),
                    channel_name=row['channel_name'],
                    channel_type=row['channel_type'],
                    participant_id=row['participant_id'],
                    participant_name=row['participant_name'],
                    status=row['status'],
                    unread_count=row['unread_count'],
                    last_message_at=row['last_message_at'],
                    last_message_preview=row['last_message_preview'],
                    assigned_agent_id=str(row['assigned_agent_id']) if row['assigned_agent_id'] else None,
                    created_at=row['created_at']
                ))

            return conversations

    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 100,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Get messages for a specific conversation"""
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM comm_messages
                WHERE conversation_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """, conversation_id, limit)

            messages = []
            import json
            for row in rows:
                messages.append(MessageResponse(
                    id=str(row['id']),
                    conversation_id=str(row['conversation_id']),
                    direction=row['direction'],
                    sender_id=row['sender_id'],
                    sender_name=row['sender_name'],
                    content=row['content'],
                    message_type=row['message_type'],
                    attachments=json.loads(row['attachments']) if row['attachments'] else [],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {},
                    read_at=row['read_at'],
                    created_at=row['created_at']
                ))

            # Reverse to show oldest first
            return list(reversed(messages))

    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/messages/send", response_model=MessageResponse)
async def send_message(
    message_data: MessageSend,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Send a message via a channel"""
    try:
        # Get conversation and channel
        async with pool.acquire() as conn:
            conv = await conn.fetchrow("""
                SELECT c.*, ch.type, ch.name, ch.config, ch.credentials_encrypted
                FROM comm_conversations c
                JOIN comm_channels ch ON c.channel_id = ch.id
                WHERE c.id = $1
            """, message_data.conversation_id)

            if not conv:
                raise HTTPException(status_code=404, detail="Conversation not found")

        # Create channel config
        import json
        config = ChannelConfig(
            id=str(conv['channel_id']),
            type=conv['type'],
            name=conv['name'],
            config=json.loads(conv['config']) if conv['config'] else {},
            credentials=json.loads(conv['credentials_encrypted']) if conv['credentials_encrypted'] else None,
            status=ChannelStatus.ACTIVE
        )

        # Create connector
        connector = _create_connector(config, pool)
        await connector.connect()

        # Send message
        sent_message = await connector.send_message(
            conversation_id=message_data.conversation_id,
            content=message_data.content,
            message_type=message_data.message_type,
            attachments=message_data.attachments,
            metadata=message_data.metadata
        )

        return MessageResponse(
            id=sent_message.id,
            conversation_id=sent_message.conversation_id,
            direction=sent_message.direction,
            sender_id=sent_message.sender_id,
            sender_name=sent_message.sender_name,
            content=sent_message.content,
            message_type=sent_message.message_type,
            attachments=sent_message.attachments,
            metadata=sent_message.metadata,
            read_at=sent_message.read_at,
            created_at=sent_message.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhooks/{channel_id}")
async def handle_webhook(
    channel_id: str,
    request: Request,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Handle webhook events from messaging platforms

    Each platform sends webhooks in different formats.
    """
    try:
        # Get channel
        channel = await get_channel(channel_id, pool)

        # Get request body
        event_data = await request.json()

        # Create connector
        import json
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM comm_channels WHERE id = $1", channel_id)
            credentials = json.loads(row['credentials_encrypted']) if row['credentials_encrypted'] else None

        config = ChannelConfig(
            id=channel_id,
            type=channel.type,
            name=channel.name,
            config=channel.config,
            credentials=credentials,
            status=ChannelStatus(channel.status)
        )

        connector = _create_connector(config, pool)
        await connector.connect()

        # Process webhook
        message = await connector.handle_webhook_event(event_data)

        if message:
            return {
                "success": True,
                "message_id": message.id,
                "conversation_id": message.conversation_id
            }
        else:
            return {"success": True, "message": "Event processed but no message created"}

    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        # Don't raise exception - return 200 to acknowledge receipt
        return {"success": False, "error": str(e)}


@router.get("/stats", response_model=StatsResponse)
async def get_stats(pool: asyncpg.Pool = Depends(get_db_pool)):
    """Get communication hub statistics"""
    try:
        async with pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT
                    (SELECT COUNT(*) FROM comm_channels) as total_channels,
                    (SELECT COUNT(*) FROM comm_channels WHERE status = 'active') as active_channels,
                    (SELECT COUNT(*) FROM comm_conversations) as total_conversations,
                    (SELECT COUNT(*) FROM comm_conversations WHERE status = 'active') as active_conversations,
                    (SELECT COUNT(*) FROM comm_messages) as total_messages,
                    (SELECT COUNT(*) FROM comm_messages WHERE created_at >= CURRENT_DATE) as messages_today,
                    (SELECT SUM(unread_count) FROM comm_conversations) as unread_messages
            """)

            return StatsResponse(
                total_channels=stats['total_channels'],
                active_channels=stats['active_channels'],
                total_conversations=stats['total_conversations'],
                active_conversations=stats['active_conversations'],
                total_messages=stats['total_messages'],
                messages_today=stats['messages_today'],
                unread_messages=stats['unread_messages'] or 0
            )

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/{conversation_id}/mark-read")
async def mark_conversation_read(
    conversation_id: str,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Mark all messages in a conversation as read"""
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                SELECT mark_conversation_as_read($1)
            """, conversation_id)

            return {"success": True}

    except Exception as e:
        logger.error(f"Error marking conversation as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/{conversation_id}/close")
async def close_conversation(
    conversation_id: str,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Close a conversation"""
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                SELECT close_conversation($1)
            """, conversation_id)

            return {"success": True}

    except Exception as e:
        logger.error(f"Error closing conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
