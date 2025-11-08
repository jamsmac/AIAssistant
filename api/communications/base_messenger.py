"""
Base Messenger Connector

Abstract base class for all messaging platform connectors (Telegram, Gmail, WhatsApp, etc.)
Provides common functionality for message handling, conversation management, and analytics.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import asyncpg
import json
import logging

logger = logging.getLogger(__name__)


class ChannelStatus(str, Enum):
    """Channel connection status"""
    INACTIVE = "inactive"
    ACTIVE = "active"
    ERROR = "error"
    CONNECTING = "connecting"


@dataclass
class ChannelConfig:
    """Configuration for a messaging channel"""
    id: Optional[str] = None
    type: str = ""  # 'telegram', 'gmail', 'whatsapp', etc.
    name: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    credentials: Optional[Dict[str, Any]] = None
    status: ChannelStatus = ChannelStatus.INACTIVE
    assigned_agent_id: Optional[str] = None
    auto_response_enabled: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class MessageData:
    """Represents a single message"""
    id: Optional[str] = None
    conversation_id: str = ""
    direction: str = "inbound"  # 'inbound' or 'outbound'
    sender_id: str = ""
    sender_name: str = ""
    content: str = ""
    message_type: str = "text"  # 'text', 'image', 'file', 'audio', 'video'
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    platform_message_id: str = ""
    read_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


@dataclass
class ConversationData:
    """Represents a conversation thread"""
    id: Optional[str] = None
    channel_id: str = ""
    platform_conversation_id: str = ""
    participant_id: str = ""
    participant_name: str = ""
    status: str = "active"  # 'active', 'archived', 'closed'
    unread_count: int = 0
    last_message_at: Optional[datetime] = None
    last_message_preview: str = ""
    assigned_agent_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class BaseMessenger(ABC):
    """
    Abstract base class for messaging platform connectors

    All messenger connectors must implement these methods:
    - connect(): Establish connection to platform
    - disconnect(): Close connection
    - send_message(): Send a message
    - receive_messages(): Poll for new messages
    - get_conversations(): List conversations
    - setup_webhook(): Configure webhook for real-time messages
    """

    def __init__(self, config: ChannelConfig, db_pool: asyncpg.Pool):
        """
        Initialize messenger connector

        Args:
            config: Channel configuration
            db_pool: Database connection pool
        """
        self.config = config
        self.db_pool = db_pool
        self.connected = False
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to messaging platform

        Returns:
            bool: True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Close connection to messaging platform

        Returns:
            bool: True if disconnection successful
        """
        pass

    @abstractmethod
    async def send_message(
        self,
        conversation_id: str,
        content: str,
        message_type: str = "text",
        attachments: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MessageData:
        """
        Send a message to a conversation

        Args:
            conversation_id: Database conversation ID
            content: Message text content
            message_type: Type of message (text, image, file, etc.)
            attachments: List of attachments
            metadata: Additional metadata

        Returns:
            MessageData: Sent message data
        """
        pass

    @abstractmethod
    async def receive_messages(
        self,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[MessageData]:
        """
        Poll for new messages

        Args:
            since: Only fetch messages after this timestamp
            limit: Maximum number of messages to fetch

        Returns:
            List[MessageData]: List of new messages
        """
        pass

    @abstractmethod
    async def get_conversations(
        self,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[ConversationData]:
        """
        Get list of conversations

        Args:
            status: Filter by status (active, archived, closed)
            limit: Maximum number of conversations to return

        Returns:
            List[ConversationData]: List of conversations
        """
        pass

    @abstractmethod
    async def setup_webhook(self, webhook_url: str) -> bool:
        """
        Configure webhook for real-time message delivery

        Args:
            webhook_url: URL to receive webhook events

        Returns:
            bool: True if webhook setup successful
        """
        pass

    @abstractmethod
    async def handle_webhook_event(self, event_data: Dict[str, Any]) -> Optional[MessageData]:
        """
        Process webhook event from platform

        Args:
            event_data: Raw webhook event data

        Returns:
            MessageData: Parsed message data, or None if not a message event
        """
        pass

    # Common database operations (implemented for all connectors)

    async def save_channel(self) -> str:
        """
        Save channel configuration to database

        Returns:
            str: Channel ID
        """
        async with self.db_pool.acquire() as conn:
            # Check if channel already exists
            if self.config.id:
                # Update existing
                await conn.execute("""
                    UPDATE comm_channels
                    SET name = $1,
                        config = $2,
                        credentials_encrypted = $3,
                        status = $4,
                        assigned_agent_id = $5,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $6
                """,
                    self.config.name,
                    json.dumps(self.config.config),
                    json.dumps(self.config.credentials) if self.config.credentials else None,
                    self.config.status.value,
                    self.config.assigned_agent_id,
                    self.config.id
                )
                return self.config.id
            else:
                # Insert new
                row = await conn.fetchrow("""
                    INSERT INTO comm_channels (type, name, config, credentials_encrypted, status, assigned_agent_id)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id
                """,
                    self.config.type,
                    self.config.name,
                    json.dumps(self.config.config),
                    json.dumps(self.config.credentials) if self.config.credentials else None,
                    self.config.status.value,
                    self.config.assigned_agent_id
                )
                self.config.id = str(row['id'])
                return self.config.id

    async def update_channel_status(self, status: ChannelStatus, error_message: Optional[str] = None):
        """
        Update channel status in database

        Args:
            status: New status
            error_message: Optional error message if status is ERROR
        """
        if not self.config.id:
            return

        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE comm_channels
                SET status = $1,
                    last_error = $2,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $3
            """, status.value, error_message, self.config.id)

        self.config.status = status

    async def save_conversation(self, conversation: ConversationData) -> str:
        """
        Save conversation to database

        Args:
            conversation: Conversation data

        Returns:
            str: Conversation ID
        """
        async with self.db_pool.acquire() as conn:
            if conversation.id:
                # Update existing
                await conn.execute("""
                    UPDATE comm_conversations
                    SET participant_name = $1,
                        status = $2,
                        last_message_at = $3,
                        last_message_preview = $4,
                        assigned_agent_id = $5,
                        metadata = $6,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $7
                """,
                    conversation.participant_name,
                    conversation.status,
                    conversation.last_message_at,
                    conversation.last_message_preview,
                    conversation.assigned_agent_id,
                    json.dumps(conversation.metadata),
                    conversation.id
                )
                return conversation.id
            else:
                # Insert new
                row = await conn.fetchrow("""
                    INSERT INTO comm_conversations (
                        channel_id, platform_conversation_id, participant_id,
                        participant_name, status, last_message_at, last_message_preview,
                        assigned_agent_id, metadata
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING id
                """,
                    self.config.id,
                    conversation.platform_conversation_id,
                    conversation.participant_id,
                    conversation.participant_name,
                    conversation.status,
                    conversation.last_message_at,
                    conversation.last_message_preview,
                    conversation.assigned_agent_id,
                    json.dumps(conversation.metadata)
                )
                conversation.id = str(row['id'])
                return conversation.id

    async def save_message(self, message: MessageData) -> str:
        """
        Save message to database

        Args:
            message: Message data

        Returns:
            str: Message ID
        """
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO comm_messages (
                    conversation_id, direction, sender_id, sender_name,
                    content, message_type, attachments, metadata,
                    platform_message_id, delivered_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id
            """,
                message.conversation_id,
                message.direction,
                message.sender_id,
                message.sender_name,
                message.content,
                message.message_type,
                json.dumps(message.attachments),
                json.dumps(message.metadata),
                message.platform_message_id,
                message.delivered_at
            )
            message.id = str(row['id'])
            return message.id

    async def get_conversation_by_platform_id(self, platform_conversation_id: str) -> Optional[ConversationData]:
        """
        Get conversation from database by platform ID

        Args:
            platform_conversation_id: Platform-specific conversation ID

        Returns:
            ConversationData or None
        """
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM comm_conversations
                WHERE channel_id = $1 AND platform_conversation_id = $2
            """, self.config.id, platform_conversation_id)

            if not row:
                return None

            return ConversationData(
                id=str(row['id']),
                channel_id=str(row['channel_id']),
                platform_conversation_id=row['platform_conversation_id'],
                participant_id=row['participant_id'],
                participant_name=row['participant_name'],
                status=row['status'],
                unread_count=row['unread_count'],
                last_message_at=row['last_message_at'],
                last_message_preview=row['last_message_preview'],
                assigned_agent_id=str(row['assigned_agent_id']) if row['assigned_agent_id'] else None,
                metadata=json.loads(row['metadata']) if row['metadata'] else {},
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )

    async def check_auto_response_rules(self, message: MessageData) -> Optional[str]:
        """
        Check if message matches any auto-response rules

        Args:
            message: Incoming message

        Returns:
            str: Response template content, or None
        """
        async with self.db_pool.acquire() as conn:
            # Get active auto-response rules for this channel
            rules = await conn.fetch("""
                SELECT * FROM comm_auto_response_rules
                WHERE channel_id = $1 AND is_active = true
                ORDER BY priority DESC
            """, self.config.id)

            for rule in rules:
                trigger_type = rule['trigger_type']
                trigger_value = rule['trigger_value']

                # Check if rule matches
                matched = False
                if trigger_type == 'keyword':
                    matched = trigger_value.lower() in message.content.lower()
                elif trigger_type == 'regex':
                    import re
                    matched = bool(re.search(trigger_value, message.content))
                elif trigger_type == 'all':
                    matched = True

                if matched:
                    # Get template
                    template_id = rule['response_template_id']
                    if template_id:
                        template = await conn.fetchrow("""
                            SELECT content FROM comm_templates
                            WHERE id = $1
                        """, template_id)
                        return template['content'] if template else rule['response_text']
                    else:
                        return rule['response_text']

            return None

    async def record_analytics(self, event_type: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Record analytics event

        Args:
            event_type: Type of event (message_sent, message_received, etc.)
            metadata: Additional event metadata
        """
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO comm_analytics (channel_id, event_type, metadata)
                VALUES ($1, $2, $3)
            """, self.config.id, event_type, json.dumps(metadata or {}))
