-- =====================================================
-- API Gateway Schema Migration
-- Version: 004
-- Description: Tables for API Gateway and data source connections
-- =====================================================

-- Gateway Connections
-- Stores configuration for external data source connections
CREATE TABLE IF NOT EXISTS gateway_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'rest', 'json', 'sql', 'graphql', 'csv', 'webhook'
    description TEXT,
    config JSONB NOT NULL, -- Connection configuration (URL, headers, params, etc.)
    credentials_encrypted TEXT, -- Encrypted API keys, passwords, tokens
    status VARCHAR(20) DEFAULT 'inactive', -- 'active', 'inactive', 'error', 'testing'
    last_sync TIMESTAMP,
    sync_frequency VARCHAR(50), -- 'manual', 'hourly', 'daily', 'weekly', 'realtime'
    auto_sync BOOLEAN DEFAULT false,
    error_count INTEGER DEFAULT 0,
    last_error TEXT,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_type CHECK (type IN ('rest', 'json', 'sql', 'graphql', 'csv', 'webhook', 'rss', 'soap')),
    CONSTRAINT valid_status CHECK (status IN ('active', 'inactive', 'error', 'testing'))
);

CREATE INDEX idx_gateway_connections_type ON gateway_connections(type);
CREATE INDEX idx_gateway_connections_status ON gateway_connections(status);
CREATE INDEX idx_gateway_connections_created_at ON gateway_connections(created_at);

-- Gateway Data Mappings
-- Defines how external data maps to internal schema
CREATE TABLE IF NOT EXISTS gateway_data_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id UUID REFERENCES gateway_connections(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    source_schema JSONB NOT NULL, -- Schema of external data
    target_table VARCHAR(100), -- Internal table name (if applicable)
    target_schema JSONB NOT NULL, -- Schema of internal data
    transformation_rules JSONB, -- JSONata or custom transformation logic
    filter_rules JSONB, -- Conditions for filtering data
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_gateway_mappings_connection ON gateway_data_mappings(connection_id);
CREATE INDEX idx_gateway_mappings_active ON gateway_data_mappings(is_active);

-- Gateway Sync History
-- Tracks all synchronization attempts and results
CREATE TABLE IF NOT EXISTS gateway_sync_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id UUID REFERENCES gateway_connections(id) ON DELETE CASCADE,
    mapping_id UUID REFERENCES gateway_data_mappings(id),
    sync_type VARCHAR(50) DEFAULT 'full', -- 'full', 'incremental', 'manual'
    records_fetched INTEGER DEFAULT 0,
    records_processed INTEGER DEFAULT 0,
    records_success INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    success BOOLEAN DEFAULT false,
    error_message TEXT,
    error_details JSONB,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    triggered_by VARCHAR(100), -- 'scheduler', 'manual', 'webhook', 'agent'
    CONSTRAINT positive_records CHECK (
        records_fetched >= 0 AND
        records_processed >= 0 AND
        records_success >= 0 AND
        records_failed >= 0
    )
);

CREATE INDEX idx_gateway_sync_connection ON gateway_sync_history(connection_id);
CREATE INDEX idx_gateway_sync_started ON gateway_sync_history(started_at);
CREATE INDEX idx_gateway_sync_success ON gateway_sync_history(success);

-- Gateway Webhooks
-- Stores webhook endpoints for receiving external data
CREATE TABLE IF NOT EXISTS gateway_webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id UUID REFERENCES gateway_connections(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    endpoint_path VARCHAR(255) UNIQUE NOT NULL, -- e.g., '/webhook/stripe-events'
    secret_token VARCHAR(255), -- For webhook verification
    http_method VARCHAR(10) DEFAULT 'POST', -- 'POST', 'GET', 'PUT'
    expected_headers JSONB, -- Headers to validate
    payload_schema JSONB, -- Expected payload structure
    is_active BOOLEAN DEFAULT true,
    last_received TIMESTAMP,
    total_received INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_http_method CHECK (http_method IN ('GET', 'POST', 'PUT', 'PATCH', 'DELETE'))
);

CREATE INDEX idx_gateway_webhooks_endpoint ON gateway_webhooks(endpoint_path);
CREATE INDEX idx_gateway_webhooks_active ON gateway_webhooks(is_active);
CREATE INDEX idx_gateway_webhooks_connection ON gateway_webhooks(connection_id);

-- Gateway Webhook Events
-- Logs all incoming webhook requests
CREATE TABLE IF NOT EXISTS gateway_webhook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    webhook_id UUID REFERENCES gateway_webhooks(id) ON DELETE CASCADE,
    payload JSONB NOT NULL,
    headers JSONB,
    source_ip VARCHAR(50),
    processed BOOLEAN DEFAULT false,
    processing_error TEXT,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

CREATE INDEX idx_webhook_events_webhook ON gateway_webhook_events(webhook_id);
CREATE INDEX idx_webhook_events_received ON gateway_webhook_events(received_at);
CREATE INDEX idx_webhook_events_processed ON gateway_webhook_events(processed);

-- Gateway Rate Limits
-- Manages rate limiting for external API calls
CREATE TABLE IF NOT EXISTS gateway_rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id UUID REFERENCES gateway_connections(id) ON DELETE CASCADE,
    limit_type VARCHAR(50) NOT NULL, -- 'per_second', 'per_minute', 'per_hour', 'per_day'
    max_requests INTEGER NOT NULL,
    current_count INTEGER DEFAULT 0,
    window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    window_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT positive_limits CHECK (max_requests > 0 AND current_count >= 0)
);

CREATE INDEX idx_rate_limits_connection ON gateway_rate_limits(connection_id);
CREATE INDEX idx_rate_limits_window ON gateway_rate_limits(window_start, window_end);

-- Gateway Data Cache
-- Caches frequently accessed external data
CREATE TABLE IF NOT EXISTS gateway_data_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id UUID REFERENCES gateway_connections(id) ON DELETE CASCADE,
    cache_key VARCHAR(255) NOT NULL,
    data JSONB NOT NULL,
    metadata JSONB,
    ttl_seconds INTEGER DEFAULT 3600,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(connection_id, cache_key)
);

CREATE INDEX idx_cache_connection_key ON gateway_data_cache(connection_id, cache_key);
CREATE INDEX idx_cache_expires ON gateway_data_cache(expires_at);

-- Gateway API Keys
-- Manages API keys for external service authentication
CREATE TABLE IF NOT EXISTS gateway_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id UUID REFERENCES gateway_connections(id) ON DELETE CASCADE,
    key_name VARCHAR(255) NOT NULL,
    key_value_encrypted TEXT NOT NULL,
    key_type VARCHAR(50), -- 'api_key', 'bearer_token', 'oauth2', 'basic_auth'
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_keys_connection ON gateway_api_keys(connection_id);
CREATE INDEX idx_api_keys_active ON gateway_api_keys(is_active);

-- Gateway Connection Tags
-- Tagging system for organizing connections
CREATE TABLE IF NOT EXISTS gateway_connection_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id UUID REFERENCES gateway_connections(id) ON DELETE CASCADE,
    tag VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(connection_id, tag)
);

CREATE INDEX idx_connection_tags_tag ON gateway_connection_tags(tag);
CREATE INDEX idx_connection_tags_connection ON gateway_connection_tags(connection_id);

-- =====================================================
-- Views for Gateway Analytics
-- =====================================================

-- Connection Health View
CREATE OR REPLACE VIEW gateway_connection_health AS
SELECT
    gc.id,
    gc.name,
    gc.type,
    gc.status,
    gc.last_sync,
    gc.error_count,
    COUNT(gsh.id) as total_syncs,
    SUM(CASE WHEN gsh.success THEN 1 ELSE 0 END) as successful_syncs,
    AVG(gsh.duration_ms) as avg_duration_ms,
    MAX(gsh.started_at) as last_sync_attempt
FROM gateway_connections gc
LEFT JOIN gateway_sync_history gsh ON gc.id = gsh.connection_id
GROUP BY gc.id, gc.name, gc.type, gc.status, gc.last_sync, gc.error_count;

-- Webhook Activity View
CREATE OR REPLACE VIEW gateway_webhook_activity AS
SELECT
    gw.id,
    gw.name,
    gw.endpoint_path,
    gw.is_active,
    COUNT(gwe.id) as total_events,
    SUM(CASE WHEN gwe.processed THEN 1 ELSE 0 END) as processed_events,
    SUM(CASE WHEN NOT gwe.processed THEN 1 ELSE 0 END) as pending_events,
    MAX(gwe.received_at) as last_event_at
FROM gateway_webhooks gw
LEFT JOIN gateway_webhook_events gwe ON gw.id = gwe.webhook_id
GROUP BY gw.id, gw.name, gw.endpoint_path, gw.is_active;

-- =====================================================
-- Functions for Gateway Operations
-- =====================================================

-- Function to clean expired cache entries
CREATE OR REPLACE FUNCTION clean_expired_gateway_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM gateway_data_cache
    WHERE expires_at < CURRENT_TIMESTAMP;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to reset rate limit windows
CREATE OR REPLACE FUNCTION reset_expired_rate_limits()
RETURNS INTEGER AS $$
DECLARE
    reset_count INTEGER;
BEGIN
    UPDATE gateway_rate_limits
    SET current_count = 0,
        window_start = CURRENT_TIMESTAMP,
        window_end = CURRENT_TIMESTAMP + INTERVAL '1 hour'
    WHERE window_end < CURRENT_TIMESTAMP;

    GET DIAGNOSTICS reset_count = ROW_COUNT;
    RETURN reset_count;
END;
$$ LANGUAGE plpgsql;

-- Function to update connection status based on sync history
CREATE OR REPLACE FUNCTION update_gateway_connection_status()
RETURNS TRIGGER AS $$
BEGIN
    -- If sync failed, increment error count
    IF NOT NEW.success THEN
        UPDATE gateway_connections
        SET error_count = error_count + 1,
            last_error = NEW.error_message,
            status = CASE
                WHEN error_count >= 5 THEN 'error'
                ELSE status
            END
        WHERE id = NEW.connection_id;
    ELSE
        -- If sync succeeded, reset error count
        UPDATE gateway_connections
        SET error_count = 0,
            last_error = NULL,
            last_sync = NEW.completed_at,
            status = 'active'
        WHERE id = NEW.connection_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update connection status
CREATE TRIGGER trigger_update_connection_status
AFTER INSERT ON gateway_sync_history
FOR EACH ROW
EXECUTE FUNCTION update_gateway_connection_status();

-- Function to increment webhook event counter
CREATE OR REPLACE FUNCTION increment_webhook_counter()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE gateway_webhooks
    SET total_received = total_received + 1,
        last_received = NEW.received_at
    WHERE id = NEW.webhook_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for webhook counter
CREATE TRIGGER trigger_increment_webhook_counter
AFTER INSERT ON gateway_webhook_events
FOR EACH ROW
EXECUTE FUNCTION increment_webhook_counter();

-- =====================================================
-- Sample Data for Testing
-- =====================================================

-- Sample REST API connection
INSERT INTO gateway_connections (name, type, description, config, status)
VALUES (
    'JSONPlaceholder API',
    'rest',
    'Public REST API for testing',
    '{"base_url": "https://jsonplaceholder.typicode.com", "timeout": 30, "retry_count": 3}',
    'active'
);

-- Sample webhook
INSERT INTO gateway_webhooks (name, endpoint_path, secret_token, is_active)
VALUES (
    'GitHub Events',
    '/webhook/github',
    'github_secret_token_123',
    true
);

-- =====================================================
-- Comments and Documentation
-- =====================================================

COMMENT ON TABLE gateway_connections IS 'Stores configuration for all external data source connections';
COMMENT ON TABLE gateway_data_mappings IS 'Defines transformation rules from external to internal data schemas';
COMMENT ON TABLE gateway_sync_history IS 'Audit trail of all data synchronization operations';
COMMENT ON TABLE gateway_webhooks IS 'Webhook endpoints for receiving external data pushes';
COMMENT ON TABLE gateway_webhook_events IS 'Log of all incoming webhook events';
COMMENT ON TABLE gateway_rate_limits IS 'Rate limiting configuration and state for external APIs';
COMMENT ON TABLE gateway_data_cache IS 'Temporary cache for frequently accessed external data';

-- =====================================================
-- Grants (adjust as needed for your security model)
-- =====================================================

-- Grant permissions to application user (adjust username as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- =====================================================
-- Migration Complete
-- =====================================================
