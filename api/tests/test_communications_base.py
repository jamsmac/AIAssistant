"""
Tests for Base Messenger Connector

Tests the abstract base class and common functionality for all messaging connectors.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
import asyncpg

from api.communications.base_messenger import (
    BaseMessenger,
    ChannelConfig,
    MessageData,
    ConversationData,
    ChannelStatus
)


class TestMessenger(BaseMessenger):
    """Concrete implementation for testing"""

    async def connect(self) -> bool:
        self.connected = True
        return True

    async def disconnect(self) -> bool:
        self.connected = False
        return True

    async def send_message(self, conversation_id, content, message_type="text", attachments=None, metadata=None):
        return MessageData(
            conversation_id=conversation_id,
            direction="outbound",
            sender_id="test_bot",
            sender_name="Test Bot",
            content=content,
            message_type=message_type,
            platform_message_id="test_msg_123"
        )

    async def receive_messages(self, since=None, limit=100):
        return []

    async def get_conversations(self, status=None, limit=50):
        return []

    async def setup_webhook(self, webhook_url):
        return True

    async def handle_webhook_event(self, event_data):
        return None


@pytest.fixture
async def mock_db_pool():
    """Create a mock database pool"""
    pool = AsyncMock(spec=asyncpg.Pool)

    # Mock connection
    conn = AsyncMock()
    conn.execute = AsyncMock()
    conn.fetchrow = AsyncMock()
    conn.fetch = AsyncMock()

    pool.acquire = AsyncMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.return_value.__aexit__ = AsyncMock()

    return pool


@pytest.fixture
def channel_config():
    """Create a test channel configuration"""
    return ChannelConfig(
        id="test-channel-123",
        type="test",
        name="Test Channel",
        config={"api_url": "https://test.example.com"},
        credentials={"api_key": "test_key_123"},
        status=ChannelStatus.ACTIVE
    )


@pytest.fixture
async def messenger(channel_config, mock_db_pool):
    """Create a test messenger instance"""
    return TestMessenger(channel_config, mock_db_pool)


class TestChannelConfig:
    """Test ChannelConfig dataclass"""

    def test_channel_config_creation(self):
        """Test creating a channel config"""
        config = ChannelConfig(
            type="telegram",
            name="My Bot",
            config={"bot_id": 123},
            credentials={"token": "abc123"}
        )

        assert config.type == "telegram"
        assert config.name == "My Bot"
        assert config.config["bot_id"] == 123
        assert config.status == ChannelStatus.INACTIVE  # Default

    def test_channel_status_enum(self):
        """Test channel status enum values"""
        assert ChannelStatus.ACTIVE.value == "active"
        assert ChannelStatus.INACTIVE.value == "inactive"
        assert ChannelStatus.ERROR.value == "error"


class TestMessageData:
    """Test MessageData dataclass"""

    def test_message_creation(self):
        """Test creating a message"""
        msg = MessageData(
            conversation_id="conv-123",
            direction="inbound",
            sender_id="user-456",
            sender_name="John Doe",
            content="Hello!",
            message_type="text",
            platform_message_id="msg-789"
        )

        assert msg.conversation_id == "conv-123"
        assert msg.direction == "inbound"
        assert msg.content == "Hello!"
        assert msg.attachments == []  # Default


class TestConversationData:
    """Test ConversationData dataclass"""

    def test_conversation_creation(self):
        """Test creating a conversation"""
        conv = ConversationData(
            channel_id="channel-123",
            platform_conversation_id="platform-conv-456",
            participant_id="user-789",
            participant_name="Jane Smith",
            status="active"
        )

        assert conv.channel_id == "channel-123"
        assert conv.participant_name == "Jane Smith"
        assert conv.unread_count == 0  # Default


class TestBaseMessenger:
    """Test BaseMessenger abstract class implementation"""

    @pytest.mark.asyncio
    async def test_messenger_initialization(self, messenger, channel_config):
        """Test messenger initialization"""
        assert messenger.config == channel_config
        assert messenger.connected == False

    @pytest.mark.asyncio
    async def test_connect(self, messenger):
        """Test connecting to platform"""
        result = await messenger.connect()
        assert result == True
        assert messenger.connected == True

    @pytest.mark.asyncio
    async def test_disconnect(self, messenger):
        """Test disconnecting from platform"""
        await messenger.connect()
        result = await messenger.disconnect()
        assert result == True
        assert messenger.connected == False

    @pytest.mark.asyncio
    async def test_save_channel_new(self, messenger, mock_db_pool):
        """Test saving a new channel"""
        conn = await mock_db_pool.acquire().__aenter__()
        conn.fetchrow.return_value = {"id": "new-channel-id"}

        # Remove ID to simulate new channel
        messenger.config.id = None

        channel_id = await messenger.save_channel()

        assert conn.execute.called or conn.fetchrow.called
        assert messenger.config.id == "new-channel-id"

    @pytest.mark.asyncio
    async def test_save_channel_existing(self, messenger, mock_db_pool):
        """Test updating an existing channel"""
        conn = await mock_db_pool.acquire().__aenter__()

        channel_id = await messenger.save_channel()

        assert conn.execute.called
        assert channel_id == "test-channel-123"

    @pytest.mark.asyncio
    async def test_update_channel_status(self, messenger, mock_db_pool):
        """Test updating channel status"""
        await messenger.update_channel_status(ChannelStatus.ERROR, "Test error")

        conn = await mock_db_pool.acquire().__aenter__()
        assert conn.execute.called
        assert messenger.config.status == ChannelStatus.ERROR

    @pytest.mark.asyncio
    async def test_save_conversation_new(self, messenger, mock_db_pool):
        """Test saving a new conversation"""
        conn = await mock_db_pool.acquire().__aenter__()
        conn.fetchrow.return_value = {"id": "new-conv-id"}

        conversation = ConversationData(
            channel_id="test-channel-123",
            platform_conversation_id="platform-conv-789",
            participant_id="user-123",
            participant_name="Test User",
            status="active"
        )

        conv_id = await messenger.save_conversation(conversation)

        assert conn.fetchrow.called
        assert conversation.id == "new-conv-id"

    @pytest.mark.asyncio
    async def test_save_message(self, messenger, mock_db_pool):
        """Test saving a message"""
        conn = await mock_db_pool.acquire().__aenter__()
        conn.fetchrow.return_value = {"id": "new-msg-id"}

        message = MessageData(
            conversation_id="conv-123",
            direction="inbound",
            sender_id="user-456",
            sender_name="Test User",
            content="Hello!",
            message_type="text",
            platform_message_id="platform-msg-789"
        )

        msg_id = await messenger.save_message(message)

        assert conn.fetchrow.called
        assert message.id == "new-msg-id"

    @pytest.mark.asyncio
    async def test_get_conversation_by_platform_id(self, messenger, mock_db_pool):
        """Test retrieving conversation by platform ID"""
        conn = await mock_db_pool.acquire().__aenter__()
        conn.fetchrow.return_value = {
            "id": "conv-123",
            "channel_id": "channel-456",
            "platform_conversation_id": "platform-conv-789",
            "participant_id": "user-123",
            "participant_name": "Test User",
            "status": "active",
            "unread_count": 5,
            "last_message_at": datetime.now(),
            "last_message_preview": "Hello!",
            "assigned_agent_id": None,
            "metadata": "{}",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        conversation = await messenger.get_conversation_by_platform_id("platform-conv-789")

        assert conversation is not None
        assert conversation.participant_name == "Test User"
        assert conversation.unread_count == 5

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, messenger, mock_db_pool):
        """Test retrieving non-existent conversation"""
        conn = await mock_db_pool.acquire().__aenter__()
        conn.fetchrow.return_value = None

        conversation = await messenger.get_conversation_by_platform_id("nonexistent")

        assert conversation is None

    @pytest.mark.asyncio
    async def test_check_auto_response_rules_keyword(self, messenger, mock_db_pool):
        """Test auto-response with keyword trigger"""
        conn = await mock_db_pool.acquire().__aenter__()
        conn.fetch.return_value = [
            {
                "trigger_type": "keyword",
                "trigger_value": "hello",
                "response_template_id": None,
                "response_text": "Hi! How can I help?",
                "priority": 100
            }
        ]

        message = MessageData(
            conversation_id="conv-123",
            content="Hello there!",
            direction="inbound",
            sender_id="user-123",
            sender_name="Test User",
            message_type="text",
            platform_message_id="msg-123"
        )

        response = await messenger.check_auto_response_rules(message)

        assert response == "Hi! How can I help?"

    @pytest.mark.asyncio
    async def test_check_auto_response_rules_no_match(self, messenger, mock_db_pool):
        """Test auto-response with no matching rules"""
        conn = await mock_db_pool.acquire().__aenter__()
        conn.fetch.return_value = [
            {
                "trigger_type": "keyword",
                "trigger_value": "goodbye",
                "response_template_id": None,
                "response_text": "See you later!",
                "priority": 100
            }
        ]

        message = MessageData(
            conversation_id="conv-123",
            content="Hello there!",
            direction="inbound",
            sender_id="user-123",
            sender_name="Test User",
            message_type="text",
            platform_message_id="msg-123"
        )

        response = await messenger.check_auto_response_rules(message)

        assert response is None

    @pytest.mark.asyncio
    async def test_record_analytics(self, messenger, mock_db_pool):
        """Test recording analytics event"""
        await messenger.record_analytics("message_sent", {"count": 1})

        conn = await mock_db_pool.acquire().__aenter__()
        assert conn.execute.called


class TestMessengerErrorHandling:
    """Test error handling in messenger"""

    @pytest.mark.asyncio
    async def test_save_channel_database_error(self, messenger, mock_db_pool):
        """Test handling database errors when saving channel"""
        conn = await mock_db_pool.acquire().__aenter__()
        conn.execute.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            await messenger.save_channel()

    @pytest.mark.asyncio
    async def test_update_status_with_no_id(self, messenger, mock_db_pool):
        """Test updating status when channel has no ID"""
        messenger.config.id = None

        # Should not raise error, just return
        await messenger.update_channel_status(ChannelStatus.ERROR)

        conn = await mock_db_pool.acquire().__aenter__()
        # Should not have called execute
        conn.execute.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
