-- ============================================
-- GDPR COMPLIANCE AND DATA ENCRYPTION
-- Critical Security Fix - Phase 2
-- Date: 2025-01-04
-- ============================================

-- This migration adds GDPR compliance features and encryption
-- for sensitive data like API keys and personal information.

-- ============================================
-- 1. ENABLE REQUIRED EXTENSIONS
-- ============================================

-- Enable pgcrypto for encryption
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================
-- 2. USER DATA DELETION (GDPR Right to be Forgotten)
-- ============================================

-- Function to anonymize user data (GDPR compliant)
CREATE OR REPLACE FUNCTION anonymize_user_data(user_email VARCHAR)
RETURNS BOOLEAN AS $$
DECLARE
    user_author_id UUID;
    anonymized_email VARCHAR := 'deleted-' || gen_random_uuid() || '@deleted.local';
    anonymized_name VARCHAR := 'Deleted User';
BEGIN
    -- Find author record
    SELECT id INTO user_author_id
    FROM blog_authors
    WHERE email = user_email;

    -- Anonymize blog_authors
    IF user_author_id IS NOT NULL THEN
        UPDATE blog_authors
        SET
            email = anonymized_email,
            name = anonymized_name,
            bio = '[User data deleted]',
            avatar_url = NULL,
            twitter = NULL,
            linkedin = NULL,
            github = NULL,
            website = NULL,
            is_active = FALSE
        WHERE id = user_author_id;
    END IF;

    -- Anonymize blog_comments
    UPDATE blog_comments
    SET
        author_name = anonymized_name,
        author_email = anonymized_email,
        author_avatar = NULL,
        ip_address = NULL,
        user_agent = NULL
    WHERE author_email = user_email OR user_id = user_email;

    -- Anonymize blog_subscriptions
    UPDATE blog_subscriptions
    SET
        email = anonymized_email,
        name = anonymized_name,
        status = 'unsubscribed'
    WHERE email = user_email;

    -- Anonymize blog_analytics
    UPDATE blog_analytics
    SET
        user_id = NULL,
        ip_address = NULL,
        user_agent = NULL
    WHERE user_id = user_email;

    -- Anonymize blog_social_shares
    UPDATE blog_social_shares
    SET
        user_id = NULL,
        ip_address = NULL,
        user_agent = NULL
    WHERE user_id = user_email;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- 3. DATA RETENTION POLICIES
-- ============================================

-- Function to delete old analytics data (keep last 2 years)
CREATE OR REPLACE FUNCTION cleanup_old_analytics()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM blog_analytics
    WHERE timestamp < NOW() - INTERVAL '2 years';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup old social shares (keep last 1 year)
CREATE OR REPLACE FUNCTION cleanup_old_social_shares()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM blog_social_shares
    WHERE created_at < NOW() - INTERVAL '1 year';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 4. SENSITIVE DATA ENCRYPTION TABLE
-- ============================================

-- Table to store encrypted API keys and secrets
CREATE TABLE IF NOT EXISTS encrypted_secrets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id VARCHAR(255),
    user_id VARCHAR(255),

    -- Secret identification
    secret_key VARCHAR(100) NOT NULL,  -- e.g., 'anthropic_api_key', 'openai_api_key'
    secret_type VARCHAR(50) NOT NULL,  -- 'api_key', 'password', 'token', 'certificate'

    -- Encrypted value (using pgcrypto)
    encrypted_value BYTEA NOT NULL,  -- AES-256 encrypted

    -- Metadata
    description TEXT,
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    rotation_required BOOLEAN DEFAULT FALSE,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255),

    -- Constraints
    CONSTRAINT unique_org_secret UNIQUE(organization_id, secret_key)
);

-- Enable RLS
ALTER TABLE encrypted_secrets ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Only owner and admin can access
CREATE POLICY "encrypted_secrets_owner_access" ON encrypted_secrets
    FOR ALL
    USING (
        organization_id = auth.jwt() ->> 'organization_id' OR
        user_id = auth.jwt() ->> 'sub' OR
        auth.jwt() ->> 'role' = 'admin'
    );

-- Indexes
CREATE INDEX IF NOT EXISTS idx_secrets_org ON encrypted_secrets(organization_id);
CREATE INDEX IF NOT EXISTS idx_secrets_user ON encrypted_secrets(user_id);
CREATE INDEX IF NOT EXISTS idx_secrets_type ON encrypted_secrets(secret_type);
CREATE INDEX IF NOT EXISTS idx_secrets_expires ON encrypted_secrets(expires_at);

-- ============================================
-- 5. ENCRYPTION HELPER FUNCTIONS
-- ============================================

-- Function to store encrypted secret
CREATE OR REPLACE FUNCTION store_encrypted_secret(
    p_org_id VARCHAR,
    p_secret_key VARCHAR,
    p_secret_value TEXT,
    p_secret_type VARCHAR,
    p_encryption_key TEXT,
    p_description TEXT DEFAULT NULL,
    p_expires_at TIMESTAMP DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_secret_id UUID;
BEGIN
    INSERT INTO encrypted_secrets (
        organization_id,
        secret_key,
        secret_type,
        encrypted_value,
        description,
        expires_at,
        created_by
    ) VALUES (
        p_org_id,
        p_secret_key,
        p_secret_type,
        pgp_sym_encrypt(p_secret_value, p_encryption_key),
        p_description,
        p_expires_at,
        auth.jwt() ->> 'sub'
    )
    ON CONFLICT (organization_id, secret_key)
    DO UPDATE SET
        encrypted_value = pgp_sym_encrypt(p_secret_value, p_encryption_key),
        updated_at = NOW()
    RETURNING id INTO v_secret_id;

    RETURN v_secret_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to retrieve decrypted secret
CREATE OR REPLACE FUNCTION get_decrypted_secret(
    p_org_id VARCHAR,
    p_secret_key VARCHAR,
    p_encryption_key TEXT
)
RETURNS TEXT AS $$
DECLARE
    v_encrypted_value BYTEA;
    v_decrypted_value TEXT;
BEGIN
    -- Get encrypted value
    SELECT encrypted_value INTO v_encrypted_value
    FROM encrypted_secrets
    WHERE organization_id = p_org_id
        AND secret_key = p_secret_key
        AND (expires_at IS NULL OR expires_at > NOW());

    IF v_encrypted_value IS NULL THEN
        RETURN NULL;
    END IF;

    -- Decrypt and return
    v_decrypted_value := pgp_sym_decrypt(v_encrypted_value, p_encryption_key);

    -- Update last_used_at
    UPDATE encrypted_secrets
    SET last_used_at = NOW()
    WHERE organization_id = p_org_id AND secret_key = p_secret_key;

    RETURN v_decrypted_value;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- 6. AUDIT LOGGING TABLE
-- ============================================

-- Table to log sensitive operations for compliance
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id VARCHAR(255),

    -- Event details
    event_type VARCHAR(100) NOT NULL,
    -- Types: 'user_login', 'data_access', 'data_export', 'secret_access', 'user_deletion'
    event_action VARCHAR(50) NOT NULL,  -- 'create', 'read', 'update', 'delete'

    -- Who performed the action
    user_id VARCHAR(255),
    user_email VARCHAR(255),
    user_role VARCHAR(50),

    -- What was affected
    resource_type VARCHAR(100),  -- 'blog_post', 'agent', 'secret', 'user_data'
    resource_id VARCHAR(255),

    -- Details
    description TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Context
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255),

    -- Success/failure
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,

    -- Timestamp
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Admin read only
CREATE POLICY "audit_logs_admin_read" ON audit_logs
    FOR SELECT
    USING (
        auth.jwt() ->> 'role' = 'admin' OR
        auth.jwt() ->> 'role' = 'service_role'
    );

-- RLS Policy: System can insert
CREATE POLICY "audit_logs_system_insert" ON audit_logs
    FOR INSERT
    WITH CHECK (
        auth.jwt() ->> 'role' = 'service_role' OR
        user_id = auth.jwt() ->> 'sub'
    );

-- Indexes
CREATE INDEX IF NOT EXISTS idx_audit_org ON audit_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_type ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(event_action);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp DESC);

-- Partitioning for audit_logs (optional, for high volume)
-- Can partition by month for better performance

-- ============================================
-- 7. AUDIT HELPER FUNCTION
-- ============================================

-- Function to log audit event
CREATE OR REPLACE FUNCTION log_audit_event(
    p_event_type VARCHAR,
    p_event_action VARCHAR,
    p_resource_type VARCHAR DEFAULT NULL,
    p_resource_id VARCHAR DEFAULT NULL,
    p_description TEXT DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}'::jsonb
)
RETURNS UUID AS $$
DECLARE
    v_audit_id UUID;
BEGIN
    INSERT INTO audit_logs (
        organization_id,
        event_type,
        event_action,
        user_id,
        user_email,
        user_role,
        resource_type,
        resource_id,
        description,
        metadata
    ) VALUES (
        auth.jwt() ->> 'organization_id',
        p_event_type,
        p_event_action,
        auth.jwt() ->> 'sub',
        auth.jwt() ->> 'email',
        auth.jwt() ->> 'role',
        p_resource_type,
        p_resource_id,
        p_description,
        p_metadata
    )
    RETURNING id INTO v_audit_id;

    RETURN v_audit_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- 8. AUTOMATIC AUDIT TRIGGERS
-- ============================================

-- Trigger function to log blog post changes
CREATE OR REPLACE FUNCTION audit_blog_post_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        PERFORM log_audit_event(
            'blog_post',
            'delete',
            'blog_post',
            OLD.id::text,
            'Blog post deleted: ' || OLD.title
        );
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        IF OLD.status != NEW.status THEN
            PERFORM log_audit_event(
                'blog_post',
                'update',
                'blog_post',
                NEW.id::text,
                'Status changed from ' || OLD.status || ' to ' || NEW.status
            );
        END IF;
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        PERFORM log_audit_event(
            'blog_post',
            'create',
            'blog_post',
            NEW.id::text,
            'Blog post created: ' || NEW.title
        );
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Apply audit trigger to blog_posts
DROP TRIGGER IF EXISTS trigger_audit_blog_posts ON blog_posts;
CREATE TRIGGER trigger_audit_blog_posts
    AFTER INSERT OR UPDATE OR DELETE ON blog_posts
    FOR EACH ROW
    EXECUTE FUNCTION audit_blog_post_changes();

-- ============================================
-- 9. DATA EXPORT FOR GDPR
-- ============================================

-- Function to export all user data (GDPR data portability)
CREATE OR REPLACE FUNCTION export_user_data(p_user_email VARCHAR)
RETURNS JSONB AS $$
DECLARE
    v_author_id UUID;
    v_result JSONB;
BEGIN
    -- Get author ID
    SELECT id INTO v_author_id
    FROM blog_authors
    WHERE email = p_user_email;

    -- Build comprehensive data export
    v_result := jsonb_build_object(
        'user_email', p_user_email,
        'export_date', NOW(),
        'author_profile', (
            SELECT jsonb_build_object(
                'name', name,
                'bio', bio,
                'email', email,
                'twitter', twitter,
                'linkedin', linkedin,
                'github', github,
                'website', website,
                'post_count', post_count,
                'total_views', total_views,
                'created_at', created_at
            )
            FROM blog_authors
            WHERE email = p_user_email
        ),
        'blog_posts', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'title', title,
                    'slug', slug,
                    'content', content,
                    'status', status,
                    'published_at', published_at,
                    'view_count', view_count,
                    'like_count', like_count
                )
            )
            FROM blog_posts
            WHERE author_id = v_author_id
        ),
        'comments', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'content', content,
                    'post_id', post_id,
                    'created_at', created_at,
                    'status', status
                )
            )
            FROM blog_comments
            WHERE author_email = p_user_email
        ),
        'subscriptions', (
            SELECT jsonb_build_object(
                'status', status,
                'frequency', frequency,
                'subscribed_at', subscribed_at
            )
            FROM blog_subscriptions
            WHERE email = p_user_email
        )
    );

    -- Log the export
    PERFORM log_audit_event(
        'data_export',
        'read',
        'user_data',
        p_user_email,
        'User data exported for GDPR compliance'
    );

    RETURN v_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- COMMENTS
-- ============================================

COMMENT ON FUNCTION anonymize_user_data IS
    'GDPR compliant user data anonymization (Right to be Forgotten)';

COMMENT ON FUNCTION export_user_data IS
    'GDPR compliant user data export (Data Portability)';

COMMENT ON TABLE encrypted_secrets IS
    'Stores API keys and sensitive data with AES-256 encryption';

COMMENT ON TABLE audit_logs IS
    'Compliance audit trail for sensitive operations';

-- ============================================
-- MIGRATION COMPLETE
-- ============================================
