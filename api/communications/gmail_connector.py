"""
Gmail API Connector

Integrates with Gmail API for sending and receiving emails.
Uses OAuth2 authentication for secure access.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .base_messenger import (
    BaseMessenger,
    ChannelConfig,
    MessageData,
    ConversationData,
    ChannelStatus
)

logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]


class GmailConnector(BaseMessenger):
    """
    Gmail API Connector

    Handles sending and receiving emails via Gmail API.
    Requires OAuth2 authentication.
    """

    def __init__(self, config: ChannelConfig, db_pool):
        """
        Initialize Gmail connector

        Args:
            config: Channel configuration with OAuth credentials
            db_pool: Database connection pool
        """
        super().__init__(config, db_pool)

        self.service = None
        self.credentials: Optional[Credentials] = None
        self.user_email: Optional[str] = None

    async def connect(self) -> bool:
        """
        Connect to Gmail API using OAuth2

        Returns:
            bool: True if connection successful
        """
        try:
            self.logger.info("Connecting to Gmail API...")

            # Load credentials from config
            if self.config.credentials and 'oauth_token' in self.config.credentials:
                # Load existing OAuth token
                token_data = self.config.credentials['oauth_token']
                self.credentials = Credentials.from_authorized_user_info(token_data, SCOPES)

            # Refresh token if needed
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
                # Save refreshed token
                self.config.credentials['oauth_token'] = {
                    'token': self.credentials.token,
                    'refresh_token': self.credentials.refresh_token,
                    'token_uri': self.credentials.token_uri,
                    'client_id': self.credentials.client_id,
                    'client_secret': self.credentials.client_secret,
                    'scopes': self.credentials.scopes
                }
                await self.save_channel()

            if not self.credentials or not self.credentials.valid:
                raise ValueError("Invalid or missing OAuth credentials. Please authenticate first.")

            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=self.credentials)

            # Get user profile to verify connection
            profile = self.service.users().getProfile(userId='me').execute()
            self.user_email = profile['emailAddress']

            self.logger.info(f"Connected to Gmail: {self.user_email}")

            # Update channel config
            self.config.config['user_email'] = self.user_email
            self.config.config['total_messages'] = profile.get('messagesTotal', 0)

            self.connected = True
            await self.update_channel_status(ChannelStatus.ACTIVE)

            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to Gmail: {e}")
            await self.update_channel_status(ChannelStatus.ERROR, str(e))
            return False

    async def disconnect(self) -> bool:
        """
        Disconnect from Gmail

        Returns:
            bool: True if disconnection successful
        """
        try:
            self.service = None
            self.credentials = None
            self.connected = False

            await self.update_channel_status(ChannelStatus.INACTIVE)
            return True

        except Exception as e:
            self.logger.error(f"Error disconnecting from Gmail: {e}")
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
        Send email via Gmail

        Args:
            conversation_id: Database conversation ID
            content: Email body (HTML or plain text)
            message_type: Type of message (text, html)
            attachments: Optional file attachments
            metadata: Optional metadata (subject, cc, bcc, etc.)

        Returns:
            MessageData: Sent message data
        """
        if not self.service:
            raise RuntimeError("Not connected to Gmail")

        # Get conversation to find recipient
        async with self.db_pool.acquire() as conn:
            conv = await conn.fetchrow("""
                SELECT participant_id, metadata
                FROM comm_conversations
                WHERE id = $1
            """, conversation_id)

            if not conv:
                raise ValueError(f"Conversation {conversation_id} not found")

        recipient_email = conv['participant_id']
        conv_metadata = conv['metadata'] or {}

        try:
            # Create email message
            if message_type == "html" or (metadata and metadata.get('html')):
                message = MIMEMultipart('alternative')
                part = MIMEText(content, 'html')
                message.attach(part)
            else:
                message = MIMEText(content, 'plain')

            # Set headers
            message['To'] = recipient_email
            message['From'] = self.user_email
            message['Subject'] = metadata.get('subject', 'Re: ' + conv_metadata.get('subject', 'No Subject')) if metadata else 'Re: ' + conv_metadata.get('subject', 'No Subject')

            # Add thread ID for threading
            if conv_metadata.get('thread_id'):
                message['References'] = conv_metadata.get('message_id', '')
                message['In-Reply-To'] = conv_metadata.get('message_id', '')

            # Add CC and BCC if provided
            if metadata and metadata.get('cc'):
                message['Cc'] = metadata['cc']
            if metadata and metadata.get('bcc'):
                message['Bcc'] = metadata['bcc']

            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    # In real implementation, would read file from URL or path
                    # part.set_payload(file_data)
                    # encoders.encode_base64(part)
                    # part.add_header('Content-Disposition', f'attachment; filename={attachment["filename"]}')
                    # message.attach(part)
                    pass

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            # Send email
            send_params = {'userId': 'me', 'body': {'raw': raw_message}}
            if conv_metadata.get('thread_id'):
                send_params['body']['threadId'] = conv_metadata['thread_id']

            sent_message = self.service.users().messages().send(**send_params).execute()

            # Create message data
            message_data = MessageData(
                conversation_id=conversation_id,
                direction="outbound",
                sender_id=self.user_email,
                sender_name=self.config.config.get('user_name', self.user_email),
                content=content,
                message_type=message_type,
                attachments=attachments or [],
                metadata={
                    'subject': message['Subject'],
                    'thread_id': sent_message.get('threadId'),
                    'label_ids': sent_message.get('labelIds', [])
                },
                platform_message_id=sent_message['id'],
                delivered_at=datetime.now()
            )

            # Save to database
            await self.save_message(message_data)

            # Record analytics
            await self.record_analytics('message_sent', {
                'message_type': message_type,
                'recipient': recipient_email,
                'has_attachments': bool(attachments)
            })

            self.logger.info(f"Sent email to {recipient_email}")
            return message_data

        except HttpError as e:
            self.logger.error(f"Failed to send email: {e}")
            raise

    async def receive_messages(
        self,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[MessageData]:
        """
        Poll for new emails

        Args:
            since: Only fetch messages after this timestamp
            limit: Maximum number of messages to fetch

        Returns:
            List[MessageData]: New messages
        """
        if not self.service:
            raise RuntimeError("Not connected to Gmail")

        messages = []

        try:
            # Build query
            query = 'in:inbox is:unread'
            if since:
                # Gmail uses internal date format
                query += f' after:{since.strftime("%Y/%m/%d")}'

            # Get message IDs
            result = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=limit
            ).execute()

            message_ids = result.get('messages', [])

            # Fetch full message details
            for msg_id_obj in message_ids:
                msg_id = msg_id_obj['id']
                message = self.service.users().messages().get(
                    userId='me',
                    id=msg_id,
                    format='full'
                ).execute()

                message_data = await self._process_gmail_message(message)
                if message_data:
                    messages.append(message_data)

            return messages

        except HttpError as e:
            self.logger.error(f"Failed to receive messages: {e}")
            return []

    async def get_conversations(
        self,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[ConversationData]:
        """
        Get email conversations (threads) for this channel

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
        Setup Gmail push notifications (watch)

        Args:
            webhook_url: URL to receive push notifications

        Returns:
            bool: True if webhook setup successful
        """
        if not self.service:
            raise RuntimeError("Not connected to Gmail")

        try:
            # Set up Gmail push notifications
            # Note: Requires Cloud Pub/Sub topic setup
            request = {
                'labelIds': ['INBOX'],
                'topicName': self.config.config.get('pubsub_topic')
            }

            if not request['topicName']:
                self.logger.warning("No Pub/Sub topic configured for Gmail push notifications")
                return False

            watch_response = self.service.users().watch(userId='me', body=request).execute()

            self.logger.info(f"Gmail watch setup: {watch_response}")

            # Update channel config
            self.config.config['watch_expiration'] = watch_response.get('expiration')
            self.config.config['history_id'] = watch_response.get('historyId')
            await self.save_channel()

            return True

        except HttpError as e:
            self.logger.error(f"Failed to setup Gmail watch: {e}")
            return False

    async def handle_webhook_event(self, event_data: Dict[str, Any]) -> Optional[MessageData]:
        """
        Process Gmail push notification

        Args:
            event_data: Pub/Sub message data

        Returns:
            MessageData or None
        """
        try:
            # Decode Pub/Sub message
            if 'message' in event_data and 'data' in event_data['message']:
                import json
                decoded_data = base64.b64decode(event_data['message']['data']).decode('utf-8')
                notification = json.loads(decoded_data)

                # Get history
                history_id = self.config.config.get('history_id')
                if history_id:
                    history = self.service.users().history().list(
                        userId='me',
                        startHistoryId=history_id,
                        historyTypes=['messageAdded']
                    ).execute()

                    # Process new messages
                    for change in history.get('history', []):
                        if 'messagesAdded' in change:
                            for msg_added in change['messagesAdded']:
                                message = msg_added['message']
                                full_message = self.service.users().messages().get(
                                    userId='me',
                                    id=message['id'],
                                    format='full'
                                ).execute()

                                return await self._process_gmail_message(full_message)

            return None

        except Exception as e:
            self.logger.error(f"Failed to process Gmail webhook: {e}")
            return None

    async def _process_gmail_message(self, gmail_message: Dict[str, Any]) -> Optional[MessageData]:
        """
        Process a Gmail message object into MessageData

        Args:
            gmail_message: Gmail message object

        Returns:
            MessageData or None
        """
        try:
            # Extract headers
            headers = {h['name']: h['value'] for h in gmail_message['payload']['headers']}

            from_email = headers.get('From', '')
            subject = headers.get('Subject', 'No Subject')
            thread_id = gmail_message.get('threadId')
            message_id = headers.get('Message-ID', gmail_message['id'])

            # Extract sender email
            import re
            email_match = re.search(r'<(.+?)>', from_email)
            sender_email = email_match.group(1) if email_match else from_email

            # Get or create conversation
            platform_conversation_id = thread_id or gmail_message['id']
            conversation = await self.get_conversation_by_platform_id(platform_conversation_id)

            if not conversation:
                # Create new conversation
                conversation = ConversationData(
                    channel_id=self.config.id,
                    platform_conversation_id=platform_conversation_id,
                    participant_id=sender_email,
                    participant_name=from_email.split('<')[0].strip() if '<' in from_email else sender_email,
                    status="active",
                    last_message_at=datetime.now(),
                    last_message_preview=subject[:100],
                    metadata={
                        'subject': subject,
                        'thread_id': thread_id,
                        'message_id': message_id
                    }
                )
                await self.save_conversation(conversation)

            # Extract message body
            content = ""
            message_type = "text"

            if 'parts' in gmail_message['payload']:
                for part in gmail_message['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        content = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
                    elif part['mimeType'] == 'text/html':
                        content = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        message_type = "html"
            elif 'body' in gmail_message['payload'] and gmail_message['payload']['body'].get('data'):
                content = base64.urlsafe_b64decode(gmail_message['payload']['body']['data']).decode('utf-8')

            # Extract attachments
            attachments = []
            if 'parts' in gmail_message['payload']:
                for part in gmail_message['payload']['parts']:
                    if part.get('filename'):
                        attachments.append({
                            'filename': part['filename'],
                            'mime_type': part['mimeType'],
                            'size': part['body'].get('size', 0),
                            'attachment_id': part['body'].get('attachmentId')
                        })

            # Create message data
            message = MessageData(
                conversation_id=conversation.id,
                direction="inbound",
                sender_id=sender_email,
                sender_name=from_email.split('<')[0].strip() if '<' in from_email else sender_email,
                content=content,
                message_type=message_type,
                attachments=attachments,
                metadata={
                    'subject': subject,
                    'thread_id': thread_id,
                    'message_id': message_id,
                    'label_ids': gmail_message.get('labelIds', [])
                },
                platform_message_id=gmail_message['id'],
                delivered_at=datetime.fromtimestamp(int(gmail_message['internalDate']) / 1000)
            )

            # Save to database
            await self.save_message(message)

            # Update conversation
            conversation.last_message_at = datetime.now()
            conversation.last_message_preview = content[:100] if content else subject[:100]
            conversation.unread_count += 1
            await self.save_conversation(conversation)

            # Check auto-response rules
            if self.config.auto_response_enabled:
                response_content = await self.check_auto_response_rules(message)
                if response_content:
                    await self.send_message(
                        conversation_id=conversation.id,
                        content=response_content,
                        metadata={
                            'auto_response': True,
                            'subject': f"Re: {subject}"
                        }
                    )

            # Record analytics
            await self.record_analytics('message_received', {
                'message_type': message_type,
                'from': sender_email,
                'has_attachments': bool(attachments)
            })

            self.logger.info(f"Processed email from {sender_email}")
            return message

        except Exception as e:
            self.logger.error(f"Error processing Gmail message: {e}")
            return None
