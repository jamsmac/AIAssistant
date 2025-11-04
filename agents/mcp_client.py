#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Client for External Integrations

Provides unified interface for Gmail, Google Drive, and Telegram integrations.
For MVP: Uses direct API calls. Future: Full MCP protocol implementation.
"""

import logging
import time
import base64
from typing import Dict, List, Optional, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Google API imports (optional, graceful degradation)
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    logging.warning("Google API libraries not installed. Gmail/Drive features disabled.")

# Telegram imports (optional, graceful degradation)
try:
    import telegram
    from telegram import Bot
    from telegram.error import TelegramError, TimedOut, NetworkError
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logging.warning("python-telegram-bot not installed. Telegram features disabled.")


# Custom Exceptions
class MCPError(Exception):
    """Base exception for MCP client errors"""
    pass


class InvalidTokenError(MCPError):
    """Token is expired or invalid"""
    pass


class RateLimitError(MCPError):
    """Rate limit exceeded"""
    pass


class ServiceUnavailableError(MCPError):
    """External service is unavailable"""
    pass


class PermissionError(MCPError):
    """Insufficient permissions for operation"""
    pass


class MCPClient:
    """
    MCP Client for external service integrations.

    Supports:
    - Gmail: Send and list emails
    - Google Drive: List and upload files
    - Telegram: Send messages

    Example:
        client = MCPClient()
        client.connect('gmail', {'access_token': '...', 'refresh_token': '...'})
        client.gmail_send('user@example.com', 'Hello', 'Test message')
        client.disconnect()
    """

    SUPPORTED_SERVICES = ['gmail', 'google_drive', 'telegram']
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds

    def __init__(self):
        """Initialize MCP client"""
        self.logger = logging.getLogger(__name__)
        self.connections: Dict[str, Any] = {}
        self.tokens: Dict[str, Dict] = {}

    def connect(self, service: str, token: Dict) -> bool:
        """
        Connect to MCP service.

        Args:
            service: Service name ('gmail', 'google_drive', 'telegram')
            token: Access token dictionary
                For Google services: {'access_token': str, 'refresh_token': str,
                                     'token_uri': str, 'client_id': str, 'client_secret': str}
                For Telegram: {'bot_token': str}

        Returns:
            True if connected successfully

        Raises:
            ValueError: If service not supported
            InvalidTokenError: If token is invalid
            ServiceUnavailableError: If service cannot be reached
        """
        if service not in self.SUPPORTED_SERVICES:
            raise ValueError(f"Service '{service}' not supported. Must be one of: {self.SUPPORTED_SERVICES}")

        self.logger.info(f"Connecting to {service}...")

        try:
            if service in ['gmail', 'google_drive']:
                return self._connect_google(service, token)
            elif service == 'telegram':
                return self._connect_telegram(token)
        except Exception as e:
            self.logger.error(f"Failed to connect to {service}: {e}")
            raise ServiceUnavailableError(f"Cannot connect to {service}: {e}")

    def _connect_google(self, service: str, token: Dict) -> bool:
        """Connect to Google service (Gmail or Drive)"""
        if not GOOGLE_AVAILABLE:
            raise ServiceUnavailableError("Google API libraries not installed")

        try:
            # Build credentials from token dict
            creds = Credentials(
                token=token.get('access_token'),
                refresh_token=token.get('refresh_token'),
                token_uri=token.get('token_uri', 'https://oauth2.googleapis.com/token'),
                client_id=token.get('client_id'),
                client_secret=token.get('client_secret'),
                scopes=token.get('scopes', [
                    'https://www.googleapis.com/auth/gmail.send',
                    'https://www.googleapis.com/auth/gmail.readonly',
                    'https://www.googleapis.com/auth/drive.file'
                ])
            )

            # Refresh token if expired
            if creds.expired and creds.refresh_token:
                self.logger.info(f"Refreshing {service} token...")
                creds.refresh(Request())
                # Update stored token
                token['access_token'] = creds.token

            # Build service
            if service == 'gmail':
                api_service = build('gmail', 'v1', credentials=creds)
            elif service == 'google_drive':
                api_service = build('drive', 'v3', credentials=creds)

            self.connections[service] = api_service
            self.tokens[service] = token

            self.logger.info(f"Successfully connected to {service}")
            return True

        except Exception as e:
            self.logger.error(f"Google auth error: {e}")
            raise InvalidTokenError(f"Invalid or expired token: {e}")

    def _connect_telegram(self, token: Dict) -> bool:
        """Connect to Telegram"""
        if not TELEGRAM_AVAILABLE:
            raise ServiceUnavailableError("Telegram library not installed")

        try:
            bot_token = token.get('bot_token')
            if not bot_token:
                raise InvalidTokenError("bot_token required for Telegram")

            bot = Bot(token=bot_token)

            # Test connection by getting bot info
            bot.get_me()

            self.connections['telegram'] = bot
            self.tokens['telegram'] = token

            self.logger.info("Successfully connected to Telegram")
            return True

        except Exception as e:
            self.logger.error(f"Telegram auth error: {e}")
            raise InvalidTokenError(f"Invalid Telegram bot token: {e}")

    def _retry_on_rate_limit(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry on rate limits"""
        for attempt in range(self.MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except HttpError as e:
                if e.resp.status == 429:  # Rate limit
                    if attempt < self.MAX_RETRIES - 1:
                        delay = self.RETRY_DELAY * (2 ** attempt)
                        self.logger.warning(f"Rate limited. Retrying in {delay}s...")
                        time.sleep(delay)
                        continue
                    else:
                        raise RateLimitError("Rate limit exceeded after retries")
                else:
                    raise
            except (TimedOut, NetworkError) as e:
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (2 ** attempt)
                    self.logger.warning(f"Network error. Retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                else:
                    raise ServiceUnavailableError(f"Service unavailable after retries: {e}")

    def gmail_send(self, to: str, subject: str, body: str, from_email: Optional[str] = None) -> Dict:
        """
        Send email via Gmail API.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            from_email: Sender email (optional, defaults to authenticated user)

        Returns:
            Dict with message ID and status

        Raises:
            ServiceUnavailableError: If not connected to Gmail
            PermissionError: If insufficient permissions
        """
        if 'gmail' not in self.connections:
            raise ServiceUnavailableError("Not connected to Gmail. Call connect() first.")

        try:
            # Create message
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            if from_email:
                message['from'] = from_email

            # Attach body
            message.attach(MIMEText(body, 'plain'))

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            # Send via API
            def _send():
                return self.connections['gmail'].users().messages().send(
                    userId='me',
                    body={'raw': raw_message}
                ).execute()

            result = self._retry_on_rate_limit(_send)

            self.logger.info(f"Email sent successfully to {to}. Message ID: {result['id']}")

            return {
                'success': True,
                'message_id': result['id'],
                'thread_id': result.get('threadId'),
                'to': to,
                'subject': subject
            }

        except HttpError as e:
            if e.resp.status == 403:
                raise PermissionError(f"Insufficient permissions to send email: {e}")
            self.logger.error(f"Gmail send error: {e}")
            raise ServiceUnavailableError(f"Failed to send email: {e}")

    def gmail_list(self, query: str = '', max_results: int = 10) -> List[Dict]:
        """
        List emails matching query.

        Args:
            query: Gmail search query (e.g., 'from:user@example.com is:unread')
            max_results: Maximum number of messages to return

        Returns:
            List of email dictionaries with id, subject, from, date, snippet

        Raises:
            ServiceUnavailableError: If not connected to Gmail
        """
        if 'gmail' not in self.connections:
            raise ServiceUnavailableError("Not connected to Gmail. Call connect() first.")

        try:
            # List messages
            def _list():
                return self.connections['gmail'].users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=max_results
                ).execute()

            results = self._retry_on_rate_limit(_list)
            messages = results.get('messages', [])

            if not messages:
                return []

            # Get full message details
            email_list = []
            for msg in messages:
                def _get():
                    return self.connections['gmail'].users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='metadata',
                        metadataHeaders=['From', 'Subject', 'Date']
                    ).execute()

                msg_data = self._retry_on_rate_limit(_get)

                # Extract headers
                headers = {h['name']: h['value'] for h in msg_data.get('payload', {}).get('headers', [])}

                email_list.append({
                    'id': msg_data['id'],
                    'thread_id': msg_data['threadId'],
                    'from': headers.get('From', ''),
                    'subject': headers.get('Subject', ''),
                    'date': headers.get('Date', ''),
                    'snippet': msg_data.get('snippet', '')
                })

            self.logger.info(f"Retrieved {len(email_list)} emails")
            return email_list

        except HttpError as e:
            self.logger.error(f"Gmail list error: {e}")
            raise ServiceUnavailableError(f"Failed to list emails: {e}")

    def drive_list(self, folder_id: str = 'root', max_results: int = 100) -> List[Dict]:
        """
        List files in Google Drive folder.

        Args:
            folder_id: Folder ID (default: 'root' for root folder)
            max_results: Maximum number of files to return

        Returns:
            List of file dictionaries with id, name, mimeType, size, modifiedTime

        Raises:
            ServiceUnavailableError: If not connected to Google Drive
        """
        if 'google_drive' not in self.connections:
            raise ServiceUnavailableError("Not connected to Google Drive. Call connect() first.")

        try:
            # Build query
            query = f"'{folder_id}' in parents and trashed=false"

            # List files
            def _list():
                return self.connections['google_drive'].files().list(
                    q=query,
                    pageSize=max_results,
                    fields='files(id, name, mimeType, size, modifiedTime, webViewLink)'
                ).execute()

            results = self._retry_on_rate_limit(_list)
            files = results.get('files', [])

            self.logger.info(f"Retrieved {len(files)} files from Drive")

            return files

        except HttpError as e:
            self.logger.error(f"Drive list error: {e}")
            raise ServiceUnavailableError(f"Failed to list files: {e}")

    def drive_upload(self, file_path: str, folder_id: str = 'root',
                     mime_type: Optional[str] = None) -> Dict:
        """
        Upload file to Google Drive.

        Args:
            file_path: Local file path to upload
            folder_id: Destination folder ID (default: 'root')
            mime_type: MIME type (auto-detected if None)

        Returns:
            Dict with file id, name, webViewLink

        Raises:
            ServiceUnavailableError: If not connected to Google Drive
            FileNotFoundError: If file doesn't exist
        """
        if 'google_drive' not in self.connections:
            raise ServiceUnavailableError("Not connected to Google Drive. Call connect() first.")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            file_name = os.path.basename(file_path)

            # File metadata
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }

            # Create media upload
            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)

            # Upload file
            def _upload():
                return self.connections['google_drive'].files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, name, webViewLink'
                ).execute()

            result = self._retry_on_rate_limit(_upload)

            self.logger.info(f"Uploaded file: {file_name} (ID: {result['id']})")

            return {
                'success': True,
                'file_id': result['id'],
                'name': result['name'],
                'web_view_link': result.get('webViewLink', '')
            }

        except HttpError as e:
            if e.resp.status == 403:
                raise PermissionError(f"Insufficient permissions to upload file: {e}")
            self.logger.error(f"Drive upload error: {e}")
            raise ServiceUnavailableError(f"Failed to upload file: {e}")

    def telegram_send(self, chat_id: str, text: str, parse_mode: str = 'HTML') -> Dict:
        """
        Send message via Telegram.

        Args:
            chat_id: Telegram chat ID or username (@channel)
            text: Message text
            parse_mode: Text parsing mode ('HTML', 'Markdown', or None)

        Returns:
            Dict with message_id and status

        Raises:
            ServiceUnavailableError: If not connected to Telegram
        """
        if 'telegram' not in self.connections:
            raise ServiceUnavailableError("Not connected to Telegram. Call connect() first.")

        try:
            def _send():
                return self.connections['telegram'].send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=parse_mode
                )

            message = self._retry_on_rate_limit(_send)

            self.logger.info(f"Telegram message sent to {chat_id}. Message ID: {message.message_id}")

            return {
                'success': True,
                'message_id': message.message_id,
                'chat_id': chat_id,
                'date': message.date.isoformat() if message.date else None
            }

        except TelegramError as e:
            self.logger.error(f"Telegram send error: {e}")
            raise ServiceUnavailableError(f"Failed to send Telegram message: {e}")

    def disconnect(self, service: Optional[str] = None) -> bool:
        """
        Close connection and cleanup.

        Args:
            service: Service to disconnect (None = disconnect all)

        Returns:
            True if disconnected successfully
        """
        if service:
            if service in self.connections:
                del self.connections[service]
                del self.tokens[service]
                self.logger.info(f"Disconnected from {service}")
            return True
        else:
            # Disconnect all
            self.connections.clear()
            self.tokens.clear()
            self.logger.info("Disconnected from all services")
            return True

    def is_connected(self, service: str) -> bool:
        """Check if service is connected"""
        return service in self.connections

    def get_connected_services(self) -> List[str]:
        """Get list of connected services"""
        return list(self.connections.keys())


# Helper function for testing
def test_mcp_client():
    """Test MCP client (requires valid tokens)"""
    client = MCPClient()

    print("MCP Client initialized")
    print(f"Supported services: {client.SUPPORTED_SERVICES}")
    print(f"Google API available: {GOOGLE_AVAILABLE}")
    print(f"Telegram API available: {TELEGRAM_AVAILABLE}")

    # Note: Actual testing requires valid OAuth tokens
    # This is a placeholder for integration tests

    return client


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run test
    test_mcp_client()
