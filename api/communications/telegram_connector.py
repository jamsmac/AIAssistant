"""
Telegram Bot Connector

Integrates with Telegram Bot API for sending and receiving messages.
Supports both polling and webhook modes.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio
import logging

from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters
from telegram.error import TelegramError

from .base_messenger import (
    BaseMessenger,
    ChannelConfig,
    MessageData,
    ConversationData,
    ChannelStatus
)

logger = logging.getLogger(__name__)


class TelegramConnector(BaseMessenger):
    """
    Telegram Bot API Connector

    Handles sending and receiving messages via Telegram Bot API.
    Supports text, images, files, and other media types.
    """

    def __init__(self, config: ChannelConfig, db_pool):
        """
        Initialize Telegram connector

        Args:
            config: Channel configuration with Telegram bot token
            db_pool: Database connection pool
        """
        super().__init__(config, db_pool)

        # Extract bot token from credentials
        if not config.credentials or 'bot_token' not in config.credentials:
            raise ValueError("Telegram bot token is required in credentials")

        self.bot_token = config.credentials['bot_token']
        self.bot: Optional[Bot] = None
        self.application: Optional[Application] = None
        self.webhook_url: Optional[str] = None

    async def connect(self) -> bool:
        """
        Connect to Telegram Bot API

        Returns:
            bool: True if connection successful
        """
        try:
            self.logger.info(f"Connecting to Telegram with bot token: {self.bot_token[:10]}...")

            # Create bot instance
            self.bot = Bot(token=self.bot_token)

            # Test connection by getting bot info
            bot_info = await self.bot.get_me()
            self.logger.info(f"Connected to Telegram bot: @{bot_info.username}")

            # Update channel config with bot info
            self.config.config['bot_username'] = bot_info.username
            self.config.config['bot_id'] = bot_info.id
            self.config.config['bot_name'] = bot_info.first_name

            self.connected = True
            await self.update_channel_status(ChannelStatus.ACTIVE)

            return True

        except TelegramError as e:
            self.logger.error(f"Failed to connect to Telegram: {e}")
            await self.update_channel_status(ChannelStatus.ERROR, str(e))
            return False

    async def disconnect(self) -> bool:
        """
        Disconnect from Telegram

        Returns:
            bool: True if disconnection successful
        """
        try:
            if self.application:
                await self.application.shutdown()
                self.application = None

            self.bot = None
            self.connected = False

            await self.update_channel_status(ChannelStatus.INACTIVE)
            return True

        except Exception as e:
            self.logger.error(f"Error disconnecting from Telegram: {e}")
            return False

    async def send_message(
        self,
        conversation_id: str,
        content: str,
        message_type: str = "text",
        attachments: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MessageData:
        """
        Send message via Telegram

        Args:
            conversation_id: Database conversation ID
            content: Message text
            message_type: Type of message (text, image, file, etc.)
            attachments: Optional attachments
            metadata: Optional metadata

        Returns:
            MessageData: Sent message data
        """
        if not self.bot:
            raise RuntimeError("Not connected to Telegram")

        # Get conversation to find chat_id
        async with self.db_pool.acquire() as conn:
            conv = await conn.fetchrow("""
                SELECT platform_conversation_id, participant_id
                FROM comm_conversations
                WHERE id = $1
            """, conversation_id)

            if not conv:
                raise ValueError(f"Conversation {conversation_id} not found")

        chat_id = conv['platform_conversation_id']

        try:
            # Send based on message type
            telegram_message = None

            if message_type == "text":
                telegram_message = await self.bot.send_message(
                    chat_id=chat_id,
                    text=content,
                    parse_mode='HTML' if metadata and metadata.get('parse_mode') == 'html' else None
                )

            elif message_type == "image" and attachments:
                # Send photo
                photo_url = attachments[0].get('url')
                telegram_message = await self.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_url,
                    caption=content
                )

            elif message_type == "file" and attachments:
                # Send document
                file_url = attachments[0].get('url')
                telegram_message = await self.bot.send_document(
                    chat_id=chat_id,
                    document=file_url,
                    caption=content
                )

            # Create message data
            message = MessageData(
                conversation_id=conversation_id,
                direction="outbound",
                sender_id=str(self.bot.id),
                sender_name=self.config.config.get('bot_name', 'Bot'),
                content=content,
                message_type=message_type,
                attachments=attachments or [],
                metadata=metadata or {},
                platform_message_id=str(telegram_message.message_id),
                delivered_at=datetime.now()
            )

            # Save to database
            await self.save_message(message)

            # Record analytics
            await self.record_analytics('message_sent', {
                'message_type': message_type,
                'chat_id': chat_id
            })

            self.logger.info(f"Sent message to chat {chat_id}")
            return message

        except TelegramError as e:
            self.logger.error(f"Failed to send message: {e}")
            raise

    async def receive_messages(
        self,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[MessageData]:
        """
        Poll for new messages (using getUpdates)

        Args:
            since: Only fetch messages after this timestamp
            limit: Maximum number of messages to fetch

        Returns:
            List[MessageData]: New messages
        """
        if not self.bot:
            raise RuntimeError("Not connected to Telegram")

        messages = []

        try:
            # Get updates
            updates = await self.bot.get_updates(limit=limit)

            for update in updates:
                if update.message:
                    message_data = await self._process_telegram_message(update.message)
                    if message_data:
                        messages.append(message_data)

            return messages

        except TelegramError as e:
            self.logger.error(f"Failed to receive messages: {e}")
            return []

    async def get_conversations(
        self,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[ConversationData]:
        """
        Get conversations for this channel

        Args:
            status: Filter by status
            limit: Maximum conversations to return

        Returns:
            List[ConversationData]: Conversations
        """
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT * FROM comm_conversations
                WHERE channel_id = $1
            """
            params = [self.config.id]

            if status:
                query += " AND status = $2"
                params.append(status)

            query += " ORDER BY last_message_at DESC LIMIT $" + str(len(params) + 1)
            params.append(limit)

            rows = await conn.fetch(query, *params)

            conversations = []
            for row in rows:
                conversations.append(ConversationData(
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
                    metadata=row['metadata'] or {},
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                ))

            return conversations

    async def setup_webhook(self, webhook_url: str) -> bool:
        """
        Setup webhook for real-time message delivery

        Args:
            webhook_url: URL to receive webhook events

        Returns:
            bool: True if webhook setup successful
        """
        if not self.bot:
            raise RuntimeError("Not connected to Telegram")

        try:
            # Set webhook
            await self.bot.set_webhook(url=webhook_url)
            self.webhook_url = webhook_url

            self.logger.info(f"Webhook set to: {webhook_url}")

            # Update channel config
            self.config.config['webhook_url'] = webhook_url
            await self.save_channel()

            return True

        except TelegramError as e:
            self.logger.error(f"Failed to setup webhook: {e}")
            return False

    async def handle_webhook_event(self, event_data: Dict[str, Any]) -> Optional[MessageData]:
        """
        Process webhook event from Telegram

        Args:
            event_data: Telegram Update object as dict

        Returns:
            MessageData or None
        """
        try:
            # Parse update
            update = Update.de_json(event_data, self.bot)

            if update.message:
                return await self._process_telegram_message(update.message)

            return None

        except Exception as e:
            self.logger.error(f"Failed to process webhook event: {e}")
            return None

    async def _process_telegram_message(self, telegram_message) -> Optional[MessageData]:
        """
        Process a Telegram message object into MessageData

        Args:
            telegram_message: Telegram Message object

        Returns:
            MessageData or None
        """
        try:
            # Get or create conversation
            chat = telegram_message.chat
            platform_conversation_id = str(chat.id)

            conversation = await self.get_conversation_by_platform_id(platform_conversation_id)

            if not conversation:
                # Create new conversation
                conversation = ConversationData(
                    channel_id=self.config.id,
                    platform_conversation_id=platform_conversation_id,
                    participant_id=str(telegram_message.from_user.id),
                    participant_name=telegram_message.from_user.full_name or telegram_message.from_user.username or "Unknown",
                    status="active",
                    last_message_at=datetime.now(),
                    last_message_preview=telegram_message.text[:100] if telegram_message.text else "[Media]"
                )
                await self.save_conversation(conversation)

            # Determine message type and content
            message_type = "text"
            content = telegram_message.text or ""
            attachments = []

            if telegram_message.photo:
                message_type = "image"
                photo = telegram_message.photo[-1]  # Largest size
                attachments.append({
                    'type': 'image',
                    'file_id': photo.file_id,
                    'file_size': photo.file_size,
                    'width': photo.width,
                    'height': photo.height
                })
                content = telegram_message.caption or ""

            elif telegram_message.document:
                message_type = "file"
                doc = telegram_message.document
                attachments.append({
                    'type': 'file',
                    'file_id': doc.file_id,
                    'file_name': doc.file_name,
                    'file_size': doc.file_size,
                    'mime_type': doc.mime_type
                })
                content = telegram_message.caption or ""

            elif telegram_message.voice:
                message_type = "audio"
                voice = telegram_message.voice
                attachments.append({
                    'type': 'voice',
                    'file_id': voice.file_id,
                    'duration': voice.duration,
                    'file_size': voice.file_size
                })

            elif telegram_message.video:
                message_type = "video"
                video = telegram_message.video
                attachments.append({
                    'type': 'video',
                    'file_id': video.file_id,
                    'duration': video.duration,
                    'file_size': video.file_size,
                    'width': video.width,
                    'height': video.height
                })
                content = telegram_message.caption or ""

            # Create message data
            message = MessageData(
                conversation_id=conversation.id,
                direction="inbound",
                sender_id=str(telegram_message.from_user.id),
                sender_name=telegram_message.from_user.full_name or telegram_message.from_user.username or "Unknown",
                content=content,
                message_type=message_type,
                attachments=attachments,
                metadata={
                    'chat_id': chat.id,
                    'chat_type': chat.type,
                    'date': telegram_message.date.isoformat() if telegram_message.date else None
                },
                platform_message_id=str(telegram_message.message_id),
                delivered_at=datetime.now()
            )

            # Save to database
            await self.save_message(message)

            # Update conversation
            conversation.last_message_at = datetime.now()
            conversation.last_message_preview = content[:100] if content else f"[{message_type}]"
            conversation.unread_count += 1
            await self.save_conversation(conversation)

            # Check auto-response rules
            if self.config.auto_response_enabled:
                response_content = await self.check_auto_response_rules(message)
                if response_content:
                    await self.send_message(
                        conversation_id=conversation.id,
                        content=response_content,
                        metadata={'auto_response': True}
                    )

            # Record analytics
            await self.record_analytics('message_received', {
                'message_type': message_type,
                'chat_id': chat.id,
                'from_user': telegram_message.from_user.id
            })

            self.logger.info(f"Processed message from chat {chat.id}")
            return message

        except Exception as e:
            self.logger.error(f"Error processing Telegram message: {e}")
            return None

    async def start_polling(self):
        """
        Start polling for messages (alternative to webhook)
        Useful for development/testing
        """
        if not self.bot:
            raise RuntimeError("Not connected to Telegram")

        try:
            # Create application
            self.application = Application.builder().token(self.bot_token).build()

            # Add message handler
            async def message_handler(update: Update, context):
                await self._process_telegram_message(update.message)

            self.application.add_handler(MessageHandler(filters.ALL, message_handler))

            # Start polling
            self.logger.info("Starting Telegram polling...")
            await self.application.run_polling()

        except Exception as e:
            self.logger.error(f"Error in polling: {e}")
            raise
