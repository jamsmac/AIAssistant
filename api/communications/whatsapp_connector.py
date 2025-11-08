"""
WhatsApp Business API Connector

Integrates with WhatsApp Business API for sending and receiving messages.
Supports WhatsApp Cloud API (Meta).
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import httpx

from .base_messenger import (
    BaseMessenger,
    ChannelConfig,
    MessageData,
    ConversationData,
    ChannelStatus
)

logger = logging.getLogger(__name__)


class WhatsAppConnector(BaseMessenger):
    """
    WhatsApp Business API Connector

    Handles sending and receiving messages via WhatsApp Cloud API.
    Supports text, images, documents, and template messages.
    """

    def __init__(self, config: ChannelConfig, db_pool):
        """
        Initialize WhatsApp connector

        Args:
            config: Channel configuration with WhatsApp credentials
            db_pool: Database connection pool
        """
        super().__init__(config, db_pool)

        # Extract credentials
        if not config.credentials or 'access_token' not in config.credentials:
            raise ValueError("WhatsApp access token is required in credentials")

        if not config.config or 'phone_number_id' not in config.config:
            raise ValueError("WhatsApp phone number ID is required in config")

        self.access_token = config.credentials['access_token']
        self.phone_number_id = config.config['phone_number_id']
        self.business_account_id = config.config.get('business_account_id')

        # WhatsApp Cloud API base URL
        self.api_version = config.config.get('api_version', 'v18.0')
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

        # HTTP client
        self.client: Optional[httpx.AsyncClient] = None

    async def connect(self) -> bool:
        """
        Connect to WhatsApp Business API

        Returns:
            bool: True if connection successful
        """
        try:
            self.logger.info(f"Connecting to WhatsApp Business API...")

            # Create HTTP client
            self.client = httpx.AsyncClient(
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                },
                timeout=30.0
            )

            # Test connection by getting phone number details
            response = await self.client.get(
                f"{self.base_url}/{self.phone_number_id}"
            )

            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"Connected to WhatsApp: {data.get('display_phone_number')}")

                # Update channel config
                self.config.config['display_phone_number'] = data.get('display_phone_number')
                self.config.config['verified_name'] = data.get('verified_name')
                self.config.config['quality_rating'] = data.get('quality_rating')

                self.connected = True
                await self.update_channel_status(ChannelStatus.ACTIVE)
                return True
            else:
                self.logger.error(f"Failed to connect: {response.status_code} - {response.text}")
                await self.update_channel_status(ChannelStatus.ERROR, response.text)
                return False

        except Exception as e:
            self.logger.error(f"Failed to connect to WhatsApp: {e}")
            await self.update_channel_status(ChannelStatus.ERROR, str(e))
            return False

    async def disconnect(self) -> bool:
        """
        Disconnect from WhatsApp

        Returns:
            bool: True if disconnection successful
        """
        try:
            if self.client:
                await self.client.aclose()
                self.client = None

            self.connected = False
            await self.update_channel_status(ChannelStatus.INACTIVE)
            return True

        except Exception as e:
            self.logger.error(f"Error disconnecting from WhatsApp: {e}")
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
        Send message via WhatsApp

        Args:
            conversation_id: Database conversation ID
            content: Message text
            message_type: Type of message (text, image, document, template)
            attachments: Optional media attachments
            metadata: Optional metadata (template params, etc.)

        Returns:
            MessageData: Sent message data
        """
        if not self.client:
            raise RuntimeError("Not connected to WhatsApp")

        # Get conversation to find recipient phone number
        async with self.db_pool.acquire() as conn:
            conv = await conn.fetchrow("""
                SELECT participant_id, metadata
                FROM comm_conversations
                WHERE id = $1
            """, conversation_id)

            if not conv:
                raise ValueError(f"Conversation {conversation_id} not found")

        to_phone = conv['participant_id']

        try:
            # Build message payload
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to_phone
            }

            whatsapp_message_id = None

            if message_type == "text":
                # Text message
                payload["type"] = "text"
                payload["text"] = {"body": content}

            elif message_type == "image" and attachments:
                # Image message
                payload["type"] = "image"
                image_url = attachments[0].get('url')
                payload["image"] = {
                    "link": image_url
                }
                if content:
                    payload["image"]["caption"] = content

            elif message_type == "document" and attachments:
                # Document message
                payload["type"] = "document"
                doc_url = attachments[0].get('url')
                doc_filename = attachments[0].get('filename', 'document')
                payload["document"] = {
                    "link": doc_url,
                    "filename": doc_filename
                }
                if content:
                    payload["document"]["caption"] = content

            elif message_type == "template":
                # Template message (for initiating conversations)
                template_name = metadata.get('template_name') if metadata else None
                if not template_name:
                    raise ValueError("Template name required for template messages")

                payload["type"] = "template"
                payload["template"] = {
                    "name": template_name,
                    "language": {"code": metadata.get('language', 'en')}
                }

                # Add template parameters if provided
                if metadata.get('parameters'):
                    payload["template"]["components"] = [
                        {
                            "type": "body",
                            "parameters": metadata['parameters']
                        }
                    ]

            # Send message
            response = await self.client.post(
                f"{self.base_url}/{self.phone_number_id}/messages",
                json=payload
            )

            if response.status_code == 200:
                data = response.json()
                whatsapp_message_id = data['messages'][0]['id']
            else:
                self.logger.error(f"Failed to send message: {response.status_code} - {response.text}")
                raise Exception(f"WhatsApp API error: {response.text}")

            # Create message data
            message = MessageData(
                conversation_id=conversation_id,
                direction="outbound",
                sender_id=self.phone_number_id,
                sender_name=self.config.config.get('verified_name', 'WhatsApp Business'),
                content=content,
                message_type=message_type,
                attachments=attachments or [],
                metadata=metadata or {},
                platform_message_id=whatsapp_message_id,
                delivered_at=datetime.now()
            )

            # Save to database
            await self.save_message(message)

            # Record analytics
            await self.record_analytics('message_sent', {
                'message_type': message_type,
                'to': to_phone
            })

            self.logger.info(f"Sent WhatsApp message to {to_phone}")
            return message

        except Exception as e:
            self.logger.error(f"Failed to send WhatsApp message: {e}")
            raise

    async def receive_messages(
        self,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[MessageData]:
        """
        Poll for new messages (not recommended - use webhooks instead)

        WhatsApp Cloud API doesn't support polling. Use webhooks.

        Returns:
            List[MessageData]: Empty list (use webhooks instead)
        """
        self.logger.warning("WhatsApp doesn't support polling. Use webhooks instead.")
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

        Note: WhatsApp webhooks are configured in Meta Business Suite, not via API.
        This method stores the webhook URL for reference.

        Args:
            webhook_url: URL to receive webhook events

        Returns:
            bool: True if webhook URL stored successfully
        """
        try:
            self.webhook_url = webhook_url

            # Store webhook URL in config
            self.config.config['webhook_url'] = webhook_url
            await self.save_channel()

            self.logger.info(f"Webhook URL configured: {webhook_url}")
            self.logger.info("Remember to configure this URL in Meta Business Suite!")

            return True

        except Exception as e:
            self.logger.error(f"Failed to setup webhook: {e}")
            return False

    async def handle_webhook_event(self, event_data: Dict[str, Any]) -> Optional[MessageData]:
        """
        Process webhook event from WhatsApp

        Args:
            event_data: WhatsApp webhook payload

        Returns:
            MessageData or None
        """
        try:
            # WhatsApp webhook structure:
            # {
            #   "object": "whatsapp_business_account",
            #   "entry": [{
            #     "id": "BUSINESS_ACCOUNT_ID",
            #     "changes": [{
            #       "value": {
            #         "messaging_product": "whatsapp",
            #         "messages": [...]
            #       }
            #     }]
            #   }]
            # }

            if event_data.get('object') != 'whatsapp_business_account':
                return None

            for entry in event_data.get('entry', []):
                for change in entry.get('changes', []):
                    value = change.get('value', {})

                    # Process messages
                    messages = value.get('messages', [])
                    for whatsapp_message in messages:
                        message_data = await self._process_whatsapp_message(whatsapp_message, value)
                        if message_data:
                            return message_data

                    # Process status updates
                    statuses = value.get('statuses', [])
                    for status in statuses:
                        await self._process_message_status(status)

            return None

        except Exception as e:
            self.logger.error(f"Failed to process WhatsApp webhook: {e}")
            return None

    async def _process_whatsapp_message(
        self,
        whatsapp_message: Dict[str, Any],
        value: Dict[str, Any]
    ) -> Optional[MessageData]:
        """
        Process a WhatsApp message object into MessageData

        Args:
            whatsapp_message: WhatsApp message object
            value: WhatsApp webhook value object

        Returns:
            MessageData or None
        """
        try:
            # Extract message details
            message_id = whatsapp_message.get('id')
            from_phone = whatsapp_message.get('from')
            timestamp = whatsapp_message.get('timestamp')
            message_type = whatsapp_message.get('type')

            # Get or create conversation
            platform_conversation_id = from_phone
            conversation = await self.get_conversation_by_platform_id(platform_conversation_id)

            if not conversation:
                # Get contact name if available
                contacts = value.get('contacts', [])
                contact_name = from_phone  # Default to phone number
                for contact in contacts:
                    if contact.get('wa_id') == from_phone:
                        contact_name = contact.get('profile', {}).get('name', from_phone)
                        break

                # Create new conversation
                conversation = ConversationData(
                    channel_id=self.config.id,
                    platform_conversation_id=platform_conversation_id,
                    participant_id=from_phone,
                    participant_name=contact_name,
                    status="active",
                    last_message_at=datetime.now(),
                    last_message_preview=""
                )
                await self.save_conversation(conversation)

            # Extract message content based on type
            content = ""
            attachments = []

            if message_type == "text":
                content = whatsapp_message.get('text', {}).get('body', '')

            elif message_type == "image":
                image_data = whatsapp_message.get('image', {})
                attachments.append({
                    'type': 'image',
                    'id': image_data.get('id'),
                    'mime_type': image_data.get('mime_type'),
                    'sha256': image_data.get('sha256')
                })
                content = image_data.get('caption', '[Image]')

            elif message_type == "document":
                doc_data = whatsapp_message.get('document', {})
                attachments.append({
                    'type': 'document',
                    'id': doc_data.get('id'),
                    'filename': doc_data.get('filename'),
                    'mime_type': doc_data.get('mime_type'),
                    'sha256': doc_data.get('sha256')
                })
                content = doc_data.get('caption', f"[Document: {doc_data.get('filename')}]")

            elif message_type == "audio":
                audio_data = whatsapp_message.get('audio', {})
                attachments.append({
                    'type': 'audio',
                    'id': audio_data.get('id'),
                    'mime_type': audio_data.get('mime_type'),
                    'sha256': audio_data.get('sha256')
                })
                content = "[Voice Message]"

            elif message_type == "video":
                video_data = whatsapp_message.get('video', {})
                attachments.append({
                    'type': 'video',
                    'id': video_data.get('id'),
                    'mime_type': video_data.get('mime_type'),
                    'sha256': video_data.get('sha256')
                })
                content = video_data.get('caption', '[Video]')

            elif message_type == "location":
                location = whatsapp_message.get('location', {})
                content = f"[Location: {location.get('latitude')}, {location.get('longitude')}]"

            # Create message data
            message = MessageData(
                conversation_id=conversation.id,
                direction="inbound",
                sender_id=from_phone,
                sender_name=conversation.participant_name,
                content=content,
                message_type=message_type,
                attachments=attachments,
                metadata={
                    'timestamp': timestamp,
                    'whatsapp_message_id': message_id
                },
                platform_message_id=message_id,
                delivered_at=datetime.fromtimestamp(int(timestamp))
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
                'from': from_phone
            })

            self.logger.info(f"Processed WhatsApp message from {from_phone}")
            return message

        except Exception as e:
            self.logger.error(f"Error processing WhatsApp message: {e}")
            return None

    async def _process_message_status(self, status: Dict[str, Any]):
        """
        Process message status update (sent, delivered, read)

        Args:
            status: WhatsApp status object
        """
        try:
            message_id = status.get('id')
            status_type = status.get('status')  # sent, delivered, read

            # Update message in database
            if status_type in ['delivered', 'read']:
                async with self.db_pool.acquire() as conn:
                    if status_type == 'delivered':
                        await conn.execute("""
                            UPDATE comm_messages
                            SET delivered_at = CURRENT_TIMESTAMP
                            WHERE platform_message_id = $1
                        """, message_id)
                    elif status_type == 'read':
                        await conn.execute("""
                            UPDATE comm_messages
                            SET read_at = CURRENT_TIMESTAMP
                            WHERE platform_message_id = $1
                        """, message_id)

            self.logger.debug(f"Message {message_id} status: {status_type}")

        except Exception as e:
            self.logger.error(f"Error processing message status: {e}")

    async def mark_message_as_read(self, whatsapp_message_id: str) -> bool:
        """
        Mark a message as read on WhatsApp

        Args:
            whatsapp_message_id: WhatsApp message ID

        Returns:
            bool: True if successful
        """
        if not self.client:
            return False

        try:
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": whatsapp_message_id
            }

            response = await self.client.post(
                f"{self.base_url}/{self.phone_number_id}/messages",
                json=payload
            )

            return response.status_code == 200

        except Exception as e:
            self.logger.error(f"Failed to mark message as read: {e}")
            return False
