"""
Tests for Telegram Connector

Tests the Telegram Bot API integration.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncpg

from api.communications.telegram_connector import TelegramConnector
from api.communications.base_messenger import ChannelConfig, ChannelStatus


@pytest.fixture
async def mock_db_pool():
    """Create a mock database pool"""
    pool = AsyncMock(spec=asyncpg.Pool)
    conn = AsyncMock()
    conn.execute = AsyncMock()
    conn.fetchrow = AsyncMock()
    conn.fetch = AsyncMock()
    pool.acquire = AsyncMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.return_value.__aexit__ = AsyncMock()
    return pool


@pytest.fixture
def telegram_config():
    """Create test Telegram configuration"""
    return ChannelConfig(
        id="telegram-channel-123",
        type="telegram",
        name="Test Telegram Bot",
        config={"bot_username": "test_bot", "bot_id": 123456789},
        credentials={"bot_token": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"},
        status=ChannelStatus.ACTIVE
    )


@pytest.fixture
async def telegram_connector(telegram_config, mock_db_pool):
    """Create a Telegram connector instance"""
    return TelegramConnector(telegram_config, mock_db_pool)


class TestTelegramConnectorInitialization:
    """Test Telegram connector initialization"""

    def test_initialization_with_valid_token(self, telegram_connector):
        """Test initializing with valid bot token"""
        assert telegram_connector.bot_token == "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
        assert telegram_connector.connected == False

    def test_initialization_without_token(self, mock_db_pool):
        """Test initializing without bot token raises error"""
        config = ChannelConfig(
            type="telegram",
            name="Test Bot",
            config={},
            credentials={}
        )

        with pytest.raises(ValueError, match="bot token is required"):
            TelegramConnector(config, mock_db_pool)


class TestTelegramConnection:
    """Test Telegram connection methods"""

    @pytest.mark.asyncio
    @patch('api.communications.telegram_connector.Bot')
    async def test_connect_success(self, mock_bot_class, telegram_connector, mock_db_pool):
        """Test successful connection to Telegram"""
        # Mock the Bot instance
        mock_bot = AsyncMock()
        mock_bot.get_me = AsyncMock(return_value=MagicMock(
            username="test_bot",
            id=123456789,
            first_name="Test Bot"
        ))
        mock_bot_class.return_value = mock_bot

        # Mock database operations
        conn = await mock_db_pool.acquire().__aenter__()
        conn.execute = AsyncMock()

        result = await telegram_connector.connect()

        assert result == True
        assert telegram_connector.connected == True
        assert telegram_connector.config.config["bot_username"] == "test_bot"

    @pytest.mark.asyncio
    @patch('api.communications.telegram_connector.Bot')
    async def test_connect_failure(self, mock_bot_class, telegram_connector, mock_db_pool):
        """Test failed connection to Telegram"""
        from telegram.error import TelegramError

        mock_bot = AsyncMock()
        mock_bot.get_me = AsyncMock(side_effect=TelegramError("Invalid token"))
        mock_bot_class.return_value = mock_bot

        conn = await mock_db_pool.acquire().__aenter__()
        conn.execute = AsyncMock()

        result = await telegram_connector.connect()

        assert result == False
        assert telegram_connector.connected == False

    @pytest.mark.asyncio
    async def test_disconnect(self, telegram_connector):
        """Test disconnecting from Telegram"""
        telegram_connector.bot = AsyncMock()
        telegram_connector.application = AsyncMock()
        telegram_connector.application.shutdown = AsyncMock()
        telegram_connector.connected = True

        result = await telegram_connector.disconnect()

        assert result == True
        assert telegram_connector.connected == False
        assert telegram_connector.bot is None


class TestTelegramSendMessage:
    """Test sending messages via Telegram"""

    @pytest.mark.asyncio
    @patch('api.communications.telegram_connector.Bot')
    async def test_send_text_message(self, mock_bot_class, telegram_connector, mock_db_pool):
        """Test sending a text message"""
        # Setup mocks
        mock_bot = AsyncMock()
        mock_message = MagicMock(message_id=12345)
        mock_bot.send_message = AsyncMock(return_value=mock_message)
        telegram_connector.bot = mock_bot

        # Mock database
        conn = await mock_db_pool.acquire().__aenter__()
        conn.fetchrow.return_value = {
            "platform_conversation_id": "123456",
            "participant_id": "user123"
        }
        conn.fetchrow.side_effect = [
            {"platform_conversation_id": "123456", "participant_id": "user123"},  # conversation
            {"id": "msg-123"}  # save message result
        ]
        conn.execute = AsyncMock()

        # Send message
        message = await telegram_connector.send_message(
            conversation_id="conv-123",
            content="Hello, world!",
            message_type="text"
        )

        assert message.content == "Hello, world!"
        assert message.direction == "outbound"
        assert message.platform_message_id == "12345"
        mock_bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    @patch('api.communications.telegram_connector.Bot')
    async def test_send_message_without_bot(self, mock_bot_class, telegram_connector):
        """Test sending message when not connected"""
        telegram_connector.bot = None

        with pytest.raises(RuntimeError, match="Not connected"):
            await telegram_connector.send_message("conv-123", "Hello")

    @pytest.mark.asyncio
    async def test_send_image_message(self, telegram_connector, mock_db_pool):
        """Test sending an image message"""
        mock_bot = AsyncMock()
        mock_message = MagicMock(message_id=12346)
        mock_bot.send_photo = AsyncMock(return_value=mock_message)
        telegram_connector.bot = mock_bot

        conn = await mock_db_pool.acquire().__aenter__()
        conn.fetchrow.side_effect = [
            {"platform_conversation_id": "123456", "participant_id": "user123"},
            {"id": "msg-124"}
        ]
        conn.execute = AsyncMock()

        message = await telegram_connector.send_message(
            conversation_id="conv-123",
            content="Check this out!",
            message_type="image",
            attachments=[{"url": "https://example.com/image.jpg"}]
        )

        assert message.message_type == "image"
        mock_bot.send_photo.assert_called_once()


class TestTelegramReceiveMessages:
    """Test receiving messages from Telegram"""

    @pytest.mark.asyncio
    async def test_receive_messages_without_bot(self, telegram_connector):
        """Test receiving messages when not connected"""
        telegram_connector.bot = None

        with pytest.raises(RuntimeError, match="Not connected"):
            await telegram_connector.receive_messages()

    @pytest.mark.asyncio
    async def test_receive_messages_empty(self, telegram_connector):
        """Test receiving messages when there are none"""
        mock_bot = AsyncMock()
        mock_bot.get_updates = AsyncMock(return_value=[])
        telegram_connector.bot = mock_bot

        messages = await telegram_connector.receive_messages()

        assert messages == []


class TestTelegramWebhook:
    """Test Telegram webhook functionality"""

    @pytest.mark.asyncio
    async def test_setup_webhook_success(self, telegram_connector):
        """Test setting up webhook"""
        mock_bot = AsyncMock()
        mock_bot.set_webhook = AsyncMock()
        telegram_connector.bot = mock_bot
        telegram_connector.connected = True

        result = await telegram_connector.setup_webhook("https://example.com/webhook")

        assert result == True
        assert telegram_connector.webhook_url == "https://example.com/webhook"
        mock_bot.set_webhook.assert_called_once_with(url="https://example.com/webhook")

    @pytest.mark.asyncio
    async def test_setup_webhook_without_bot(self, telegram_connector):
        """Test setting up webhook when not connected"""
        telegram_connector.bot = None

        with pytest.raises(RuntimeError, match="Not connected"):
            await telegram_connector.setup_webhook("https://example.com/webhook")

    @pytest.mark.asyncio
    @patch('api.communications.telegram_connector.Update')
    async def test_handle_webhook_event(self, mock_update_class, telegram_connector, mock_db_pool):
        """Test handling webhook event"""
        # Create mock update with message
        mock_message = MagicMock()
        mock_message.chat.id = 123456
        mock_message.from_user.id = 789
        mock_message.from_user.full_name = "Test User"
        mock_message.text = "Hello!"
        mock_message.message_id = 999
        mock_message.date = datetime.now()

        mock_update = MagicMock()
        mock_update.message = mock_message
        mock_update_class.de_json.return_value = mock_update

        telegram_connector.bot = AsyncMock()

        # Mock database operations
        conn = await mock_db_pool.acquire().__aenter__()
        conn.fetchrow.side_effect = [
            None,  # No existing conversation
            {"id": "conv-123"},  # Created conversation
            {"id": "msg-456"}  # Created message
        ]
        conn.execute = AsyncMock()

        # Process webhook
        event_data = {"update_id": 1, "message": {}}
        message = await telegram_connector.handle_webhook_event(event_data)

        # Verify message was processed
        # Note: This test may need adjustment based on actual implementation details


class TestTelegramConversations:
    """Test Telegram conversation management"""

    @pytest.mark.asyncio
    async def test_get_conversations(self, telegram_connector, mock_db_pool):
        """Test retrieving conversations"""
        conn = await mock_db_pool.acquire().__aenter__()
        conn.fetch.return_value = [
            {
                "id": "conv-1",
                "channel_id": "channel-123",
                "platform_conversation_id": "123456",
                "participant_id": "user1",
                "participant_name": "User One",
                "status": "active",
                "unread_count": 3,
                "last_message_at": datetime.now(),
                "last_message_preview": "Hello!",
                "assigned_agent_id": None,
                "metadata": {},
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        ]

        conversations = await telegram_connector.get_conversations(status="active", limit=10)

        assert len(conversations) == 1
        assert conversations[0].participant_name == "User One"
        assert conversations[0].unread_count == 3


class TestTelegramMessageProcessing:
    """Test Telegram message processing"""

    @pytest.mark.asyncio
    async def test_process_text_message(self, telegram_connector, mock_db_pool):
        """Test processing a text message"""
        # Create mock Telegram message
        mock_message = MagicMock()
        mock_message.chat.id = 123456
        mock_message.chat.type = "private"
        mock_message.from_user.id = 789
        mock_message.from_user.full_name = "Test User"
        mock_message.from_user.username = "testuser"
        mock_message.text = "Hello, bot!"
        mock_message.message_id = 999
        mock_message.date = datetime.now()
        mock_message.photo = None
        mock_message.document = None
        mock_message.voice = None
        mock_message.video = None

        # Mock database
        conn = await mock_db_pool.acquire().__aenter__()
        conn.fetchrow.side_effect = [
            None,  # No existing conversation
            {"id": "conv-123"},  # Created conversation
            {"id": "msg-456"}  # Created message
        ]
        conn.execute = AsyncMock()

        # Mock auto-response check
        conn.fetch.return_value = []  # No auto-response rules

        telegram_connector.config.auto_response_enabled = False

        message = await telegram_connector._process_telegram_message(mock_message)

        assert message is not None
        assert message.content == "Hello, bot!"
        assert message.message_type == "text"
        assert message.direction == "inbound"


class TestTelegramErrorHandling:
    """Test error handling in Telegram connector"""

    @pytest.mark.asyncio
    @patch('api.communications.telegram_connector.Bot')
    async def test_send_message_telegram_error(self, mock_bot_class, telegram_connector, mock_db_pool):
        """Test handling Telegram API errors when sending"""
        from telegram.error import TelegramError

        mock_bot = AsyncMock()
        mock_bot.send_message = AsyncMock(side_effect=TelegramError("API Error"))
        telegram_connector.bot = mock_bot

        conn = await mock_db_pool.acquire().__aenter__()
        conn.fetchrow.return_value = {
            "platform_conversation_id": "123456",
            "participant_id": "user123"
        }

        with pytest.raises(TelegramError):
            await telegram_connector.send_message("conv-123", "Hello")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
