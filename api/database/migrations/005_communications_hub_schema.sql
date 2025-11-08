-- =====================================================
-- Communication Hub Schema Migration
-- Version: 005
-- Description: Tables for Communication Hub (Telegram, Gmail, WhatsApp, etc.)
-- =====================================================

-- Communication Channels
-- Stores configuration for messaging platforms
CREATE TABLE IF NOT EXISTS comm_channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(50) NOT NULL, -- 'telegram', 'gmail', 'whatsapp', 'instagram', 'slack', 'discord'
    name VARCHAR(255) NOT NULL,
    description TEXT,
    config JSONB NOT NULL, -- Channel-specific configuration
    credentials_encrypted TEXT, -- Encrypted tokens, passwords, etc.
    status VARCHAR(20) DEFAULT 'inactive', -- 'active', 'inactive', 'error', 'testing'
    is_active BOOLEAN DEFAULT true,
    auto_respond BOOLEAN DEFAULT false,
    assigned_agent_id UUID, -- Default agent for this channel
    last_message_at TIMESTAMP,
    total_messages_received INTEGER DEFAULT 0,
    total_messages_sent INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    last_error TEXT,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_channel_type CHECK (type IN (
        'telegram', 'gmail', 'whatsapp', 'instagram', 'slack', 'discord', 'sms', 'messenger'
    )),
    CONSTRAINT valid_channel_status CHECK (status IN ('active', 'inactive', 'error', 'testing'))
);

CREATE INDEX idx_comm_channels_type ON comm_channels(type);
CREATE INDEX idx_comm_channels_status ON comm_channels(status);
CREATE INDEX idx_comm_channels_active ON comm_channels(is_active);
CREATE INDEX idx_comm_channels_agent ON comm_channels(assigned_agent_id);

-- Conversations
-- Represents individual conversations or threads
CREATE TABLE IF NOT EXISTS comm_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id UUID REFERENCES comm_channels(id) ON DELETE CASCADE,
    external_id VARCHAR(255), -- ID from external platform (chat_id, thread_id, etc.)
    participant_name VARCHAR(255),
    participant_id VARCHAR(255), -- External user ID
    participant_email VARCHAR(255),
    participant_phone VARCHAR(50),
    assigned_agent_id UUID, -- Can reference fractal_agents(id) if that table exists
    status VARCHAR(20) DEFAULT 'open', -- 'open', 'closed', 'archived', 'pending'
    priority VARCHAR(20) DEFAULT 'normal', -- 'low', 'normal', 'high', 'urgent'
    tags JSONB, -- Array of tags for organization
    metadata JSONB, -- Additional conversation data
    message_count INTEGER DEFAULT 0,
    unread_count INTEGER DEFAULT 0,
    last_message_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    CONSTRAINT valid_conversation_status CHECK (status IN ('open', 'closed', 'archived', 'pending')),
    CONSTRAINT valid_priority CHECK (priority IN ('low', 'normal', 'high', 'urgent'))
);

CREATE INDEX idx_comm_conversations_channel ON comm_conversations(channel_id);
CREATE INDEX idx_comm_conversations_external ON comm_conversations(external_id);
CREATE INDEX idx_comm_conversations_status ON comm_conversations(status);
CREATE INDEX idx_comm_conversations_priority ON comm_conversations(priority);
CREATE INDEX idx_comm_conversations_agent ON comm_conversations(assigned_agent_id);
CREATE INDEX idx_comm_conversations_last_message ON comm_conversations(last_message_at);
CREATE UNIQUE INDEX idx_comm_conversations_channel_external ON comm_conversations(channel_id, external_id);

-- Messages
-- Individual messages within conversations
CREATE TABLE IF NOT EXISTS comm_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES comm_conversations(id) ON DELETE CASCADE,
    external_id VARCHAR(255), -- Message ID from external platform
    direction VARCHAR(10) NOT NULL, -- 'inbound', 'outbound'
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'text', -- 'text', 'image', 'file', 'audio', 'video'
    attachments JSONB, -- Array of attachment objects
    metadata JSONB, -- Platform-specific metadata
    sender_name VARCHAR(255),
    sender_id VARCHAR(255),
    is_read BOOLEAN DEFAULT false,
    is_ai_generated BOOLEAN DEFAULT false,
    ai_confidence DECIMAL(3,2), -- 0.00 to 1.00
    processing_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processed', 'failed'
    processing_error TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP,
    processed_at TIMESTAMP,
    CONSTRAINT valid_direction CHECK (direction IN ('inbound', 'outbound')),
    CONSTRAINT valid_content_type CHECK (content_type IN (
        'text', 'image', 'file', 'audio', 'video', 'location', 'contact', 'sticker'
    )),
    CONSTRAINT valid_processing_status CHECK (processing_status IN ('pending', 'processed', 'failed'))
);

CREATE INDEX idx_comm_messages_conversation ON comm_messages(conversation_id);
CREATE INDEX idx_comm_messages_direction ON comm_messages(direction);
CREATE INDEX idx_comm_messages_sent_at ON comm_messages(sent_at DESC);
CREATE INDEX idx_comm_messages_processing ON comm_messages(processing_status);
CREATE INDEX idx_comm_messages_unread ON comm_messages(is_read) WHERE is_read = false;

-- Message Templates
-- Pre-defined message templates for quick responses
CREATE TABLE IF NOT EXISTS comm_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100), -- 'greeting', 'support', 'sales', 'custom'
    content TEXT NOT NULL,
    variables JSONB, -- Variables that can be replaced in template
    channel_type VARCHAR(50), -- Specific to a channel type, or NULL for all
    is_active BOOLEAN DEFAULT true,
    usage_count INTEGER DEFAULT 0,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_comm_templates_category ON comm_templates(category);
CREATE INDEX idx_comm_templates_channel ON comm_templates(channel_type);
CREATE INDEX idx_comm_templates_active ON comm_templates(is_active);

-- Auto-Response Rules
-- Rules for automated message responses
CREATE TABLE IF NOT EXISTS comm_auto_response_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    channel_id UUID REFERENCES comm_channels(id) ON DELETE CASCADE,
    trigger_type VARCHAR(50) NOT NULL, -- 'keyword', 'regex', 'time', 'first_message', 'all'
    trigger_value TEXT, -- Keyword, regex pattern, or time expression
    response_template_id UUID REFERENCES comm_templates(id),
    response_text TEXT, -- Direct response text (if not using template)
    assign_to_agent_id UUID, -- Assign conversation to specific agent
    priority VARCHAR(20) DEFAULT 'normal',
    is_active BOOLEAN DEFAULT true,
    execution_count INTEGER DEFAULT 0,
    last_executed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_trigger_type CHECK (trigger_type IN (
        'keyword', 'regex', 'time', 'first_message', 'all', 'sentiment'
    ))
);

CREATE INDEX idx_auto_response_channel ON comm_auto_response_rules(channel_id);
CREATE INDEX idx_auto_response_active ON comm_auto_response_rules(is_active);

-- Message Analytics
-- Aggregated statistics for messaging
CREATE TABLE IF NOT EXISTS comm_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id UUID REFERENCES comm_channels(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES comm_conversations(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    hour INTEGER, -- 0-23 for hourly stats
    messages_received INTEGER DEFAULT 0,
    messages_sent INTEGER DEFAULT 0,
    unique_participants INTEGER DEFAULT 0,
    avg_response_time_seconds INTEGER,
    ai_responses INTEGER DEFAULT 0,
    human_responses INTEGER DEFAULT 0,
    conversations_opened INTEGER DEFAULT 0,
    conversations_closed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(channel_id, date, hour)
);

CREATE INDEX idx_comm_analytics_channel ON comm_analytics(channel_id);
CREATE INDEX idx_comm_analytics_date ON comm_analytics(date);
CREATE INDEX idx_comm_analytics_channel_date ON comm_analytics(channel_id, date);

-- Bot Commands (for platforms that support them like Telegram)
CREATE TABLE IF NOT EXISTS comm_bot_commands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id UUID REFERENCES comm_channels(id) ON DELETE CASCADE,
    command VARCHAR(100) NOT NULL, -- e.g., '/start', '/help'
    description TEXT,
    handler_type VARCHAR(50) DEFAULT 'template', -- 'template', 'agent', 'function'
    handler_config JSONB, -- Configuration for handler
    is_active BOOLEAN DEFAULT true,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(channel_id, command)
);

CREATE INDEX idx_bot_commands_channel ON comm_bot_commands(channel_id);
CREATE INDEX idx_bot_commands_active ON comm_bot_commands(is_active);

-- =====================================================
-- Views for Communication Hub Analytics
-- =====================================================

-- Channel Activity View
CREATE OR REPLACE VIEW comm_channel_activity AS
SELECT
    cc.id,
    cc.name,
    cc.type,
    cc.status,
    cc.total_messages_received,
    cc.total_messages_sent,
    COUNT(DISTINCT conv.id) as total_conversations,
    COUNT(DISTINCT CASE WHEN conv.status = 'open' THEN conv.id END) as open_conversations,
    AVG(CASE WHEN conv.status = 'closed'
        THEN EXTRACT(EPOCH FROM (conv.closed_at - conv.created_at))/3600
        END) as avg_conversation_duration_hours,
    MAX(cc.last_message_at) as last_activity
FROM comm_channels cc
LEFT JOIN comm_conversations conv ON cc.id = conv.channel_id
GROUP BY cc.id, cc.name, cc.type, cc.status, cc.total_messages_received, cc.total_messages_sent;

-- Conversation Overview View
CREATE OR REPLACE VIEW comm_conversation_overview AS
SELECT
    conv.id,
    conv.status,
    conv.priority,
    ch.name as channel_name,
    ch.type as channel_type,
    conv.participant_name,
    conv.message_count,
    conv.unread_count,
    conv.last_message_at,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - conv.last_message_at))/3600 as hours_since_last_message,
    conv.created_at,
    CASE WHEN conv.status = 'open'
        THEN EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - conv.created_at))/3600
        ELSE EXTRACT(EPOCH FROM (conv.closed_at - conv.created_at))/3600
    END as conversation_age_hours
FROM comm_conversations conv
JOIN comm_channels ch ON conv.channel_id = ch.id;

-- Inbox View (Unified Inbox)
CREATE OR REPLACE VIEW comm_unified_inbox AS
SELECT
    msg.id as message_id,
    msg.conversation_id,
    conv.participant_name,
    conv.status as conversation_status,
    conv.priority,
    ch.name as channel_name,
    ch.type as channel_type,
    msg.direction,
    msg.content,
    msg.content_type,
    msg.is_read,
    msg.sent_at,
    conv.unread_count,
    ROW_NUMBER() OVER (PARTITION BY msg.conversation_id ORDER BY msg.sent_at DESC) as message_rank
FROM comm_messages msg
JOIN comm_conversations conv ON msg.conversation_id = conv.id
JOIN comm_channels ch ON conv.channel_id = ch.id
WHERE conv.status IN ('open', 'pending');

-- =====================================================
-- Functions for Communication Hub Operations
-- =====================================================

-- Function to update conversation counters
CREATE OR REPLACE FUNCTION update_conversation_counters()
RETURNS TRIGGER AS $$
BEGIN
    -- Update message count
    UPDATE comm_conversations
    SET message_count = message_count + 1,
        last_message_at = NEW.sent_at,
        updated_at = CURRENT_TIMESTAMP,
        unread_count = CASE
            WHEN NEW.direction = 'inbound' AND NOT NEW.is_read
            THEN unread_count + 1
            ELSE unread_count
        END
    WHERE id = NEW.conversation_id;

    -- Update channel counters
    UPDATE comm_channels
    SET total_messages_received = CASE
            WHEN NEW.direction = 'inbound' THEN total_messages_received + 1
            ELSE total_messages_received
        END,
        total_messages_sent = CASE
            WHEN NEW.direction = 'outbound' THEN total_messages_sent + 1
            ELSE total_messages_sent
        END,
        last_message_at = NEW.sent_at,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = (SELECT channel_id FROM comm_conversations WHERE id = NEW.conversation_id);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for message counter updates
CREATE TRIGGER trigger_update_conversation_counters
AFTER INSERT ON comm_messages
FOR EACH ROW
EXECUTE FUNCTION update_conversation_counters();

-- Function to mark messages as read
CREATE OR REPLACE FUNCTION mark_conversation_as_read(conv_id UUID)
RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER;
BEGIN
    UPDATE comm_messages
    SET is_read = true,
        read_at = CURRENT_TIMESTAMP
    WHERE conversation_id = conv_id
    AND is_read = false
    AND direction = 'inbound';

    GET DIAGNOSTICS updated_count = ROW_COUNT;

    -- Reset unread counter
    UPDATE comm_conversations
    SET unread_count = 0,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = conv_id;

    RETURN updated_count;
END;
$$ LANGUAGE plpgsql;

-- Function to close conversation
CREATE OR REPLACE FUNCTION close_conversation(conv_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE comm_conversations
    SET status = 'closed',
        closed_at = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = conv_id
    AND status != 'closed';

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Function to aggregate analytics
CREATE OR REPLACE FUNCTION aggregate_comm_analytics(target_date DATE)
RETURNS INTEGER AS $$
DECLARE
    processed_count INTEGER := 0;
BEGIN
    -- Insert or update daily analytics
    INSERT INTO comm_analytics (
        channel_id,
        date,
        messages_received,
        messages_sent,
        unique_participants,
        conversations_opened,
        conversations_closed
    )
    SELECT
        ch.id as channel_id,
        target_date,
        COUNT(CASE WHEN msg.direction = 'inbound' THEN 1 END) as messages_received,
        COUNT(CASE WHEN msg.direction = 'outbound' THEN 1 END) as messages_sent,
        COUNT(DISTINCT conv.participant_id) as unique_participants,
        COUNT(DISTINCT CASE WHEN DATE(conv.created_at) = target_date THEN conv.id END) as conversations_opened,
        COUNT(DISTINCT CASE WHEN DATE(conv.closed_at) = target_date THEN conv.id END) as conversations_closed
    FROM comm_channels ch
    LEFT JOIN comm_conversations conv ON ch.id = conv.channel_id
    LEFT JOIN comm_messages msg ON conv.id = msg.conversation_id
        AND DATE(msg.sent_at) = target_date
    GROUP BY ch.id
    ON CONFLICT (channel_id, date, hour) DO UPDATE
    SET messages_received = EXCLUDED.messages_received,
        messages_sent = EXCLUDED.messages_sent,
        unique_participants = EXCLUDED.unique_participants,
        conversations_opened = EXCLUDED.conversations_opened,
        conversations_closed = EXCLUDED.conversations_closed;

    GET DIAGNOSTICS processed_count = ROW_COUNT;
    RETURN processed_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Sample Data for Testing
-- =====================================================

-- Sample Telegram channel
INSERT INTO comm_channels (name, type, description, config, status)
VALUES (
    'Main Telegram Bot',
    'telegram',
    'Primary customer support bot',
    '{"bot_token": "PLACEHOLDER", "webhook_url": "https://example.com/webhook/telegram"}',
    'inactive'
) ON CONFLICT DO NOTHING;

-- Sample Gmail channel
INSERT INTO comm_channels (name, type, description, config, status)
VALUES (
    'Support Email',
    'gmail',
    'support@example.com inbox',
    '{"email": "support@example.com", "check_interval": 60}',
    'inactive'
) ON CONFLICT DO NOTHING;

-- Sample templates
INSERT INTO comm_templates (name, category, content, variables)
VALUES
    ('Welcome Message', 'greeting', 'Hello {{name}}! Welcome to our service. How can I help you today?', '["name"]'),
    ('Thank You', 'support', 'Thank you for contacting us! We will get back to you shortly.', '[]'),
    ('Working Hours', 'support', 'Our working hours are Monday-Friday, 9 AM - 6 PM. We will respond to your message during business hours.', '[]')
ON CONFLICT DO NOTHING;

-- =====================================================
-- Comments and Documentation
-- =====================================================

COMMENT ON TABLE comm_channels IS 'Configuration for messaging platform integrations';
COMMENT ON TABLE comm_conversations IS 'Individual conversations or message threads';
COMMENT ON TABLE comm_messages IS 'Individual messages within conversations';
COMMENT ON TABLE comm_templates IS 'Pre-defined message templates for quick responses';
COMMENT ON TABLE comm_auto_response_rules IS 'Rules for automated message handling';
COMMENT ON TABLE comm_analytics IS 'Aggregated messaging statistics';
COMMENT ON TABLE comm_bot_commands IS 'Bot commands for platforms like Telegram';

-- =====================================================
-- Migration Complete
-- =====================================================
