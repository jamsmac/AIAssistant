"""
Communication Hub Module
Provides connectors for messaging platforms (Telegram, Gmail, WhatsApp, etc.)
"""

from .base_messenger import (
    BaseMessenger,
    ChannelConfig,
    MessageData,
    ConversationData,
    ChannelStatus
)
from .telegram_connector import TelegramConnector
from .gmail_connector import GmailConnector
from .whatsapp_connector import WhatsAppConnector

__all__ = [
    'BaseMessenger',
    'ChannelConfig',
    'MessageData',
    'ConversationData',
    'ChannelStatus',
    'TelegramConnector',
    'GmailConnector',
    'WhatsAppConnector',
]
