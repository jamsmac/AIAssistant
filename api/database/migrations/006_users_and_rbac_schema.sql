-- =====================================================
-- Users and RBAC Schema Migration
-- Version: 006
-- Description: Multi-user authentication and role-based access control
-- =====================================================

-- Organizations/Workspaces
-- Multi-tenant support
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    logo_url TEXT,
    plan VARCHAR(50) DEFAULT 'free', -- 'free', 'starter', 'professional', 'enterprise'
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'suspended', 'cancelled'
    max_users INTEGER DEFAULT 5,
    max_agents INTEGER DEFAULT 10,
    max_api_calls_per_month INTEGER DEFAULT 10000,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_plan CHECK (plan IN ('free', 'starter', 'professional', 'enterprise')),
    CONSTRAINT valid_org_status CHECK (status IN ('active', 'suspended', 'cancelled'))
);

CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_status ON organizations(status);

-- Users
-- User accounts with authentication
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255), -- bcrypt hash
    full_name VARCHAR(255),
    avatar_url TEXT,
    phone VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'inactive', 'suspended', 'pending'
    email_verified BOOLEAN DEFAULT false,
    phone_verified BOOLEAN DEFAULT false,
    two_factor_enabled BOOLEAN DEFAULT false,
    two_factor_secret VARCHAR(255),
    last_login_at TIMESTAMP,
    last_login_ip VARCHAR(50),
    login_count INTEGER DEFAULT 0,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    password_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    settings JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_user_status CHECK (status IN ('active', 'inactive', 'suspended', 'pending'))
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_organization ON users(organization_id);
CREATE INDEX idx_users_status ON users(status);

-- Roles
-- Define roles with permissions
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,
    is_system_role BOOLEAN DEFAULT false, -- System roles can't be deleted
    permissions JSONB DEFAULT '[]', -- Array of permission strings
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, slug)
);

CREATE INDEX idx_roles_organization ON roles(organization_id);
CREATE INDEX idx_roles_slug ON roles(slug);

-- User Roles (many-to-many)
CREATE TABLE IF NOT EXISTS user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    granted_by UUID REFERENCES users(id),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    UNIQUE(user_id, role_id)
);

CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_user_roles_role ON user_roles(role_id);

-- API Keys
-- For programmatic access
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    key_prefix VARCHAR(20) NOT NULL, -- e.g., 'sk_live_', 'sk_test_'
    key_hash VARCHAR(255) NOT NULL, -- Hashed key
    key_hint VARCHAR(20), -- Last 4 characters for display
    permissions JSONB DEFAULT '[]', -- Scoped permissions
    rate_limit_per_minute INTEGER DEFAULT 60,
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_keys_user ON api_keys(user_id);
CREATE INDEX idx_api_keys_organization ON api_keys(organization_id);
CREATE INDEX idx_api_keys_prefix ON api_keys(key_prefix);
CREATE INDEX idx_api_keys_active ON api_keys(is_active);

-- Sessions
-- User login sessions
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    device_info JSONB, -- Browser, OS, device type
    ip_address VARCHAR(50),
    user_agent TEXT,
    is_active BOOLEAN DEFAULT true,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_sessions_token ON user_sessions(token_hash);
CREATE INDEX idx_sessions_active ON user_sessions(is_active);
CREATE INDEX idx_sessions_expires ON user_sessions(expires_at);

-- Audit Log
-- Track all important actions
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL, -- 'user.created', 'agent.deleted', 'data.exported', etc.
    resource_type VARCHAR(100), -- 'user', 'agent', 'connection', etc.
    resource_id UUID,
    details JSONB, -- Action details
    ip_address VARCHAR(50),
    user_agent TEXT,
    status VARCHAR(20) DEFAULT 'success', -- 'success', 'failure', 'error'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_audit_status CHECK (status IN ('success', 'failure', 'error'))
);

CREATE INDEX idx_audit_organization ON audit_logs(organization_id);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_created ON audit_logs(created_at DESC);

-- OAuth Connections
-- For OAuth provider integration (Google, GitHub, etc.)
CREATE TABLE IF NOT EXISTS oauth_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL, -- 'google', 'github', 'microsoft', etc.
    provider_user_id VARCHAR(255) NOT NULL,
    provider_email VARCHAR(255),
    access_token_encrypted TEXT,
    refresh_token_encrypted TEXT,
    token_expires_at TIMESTAMP,
    scope TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider, provider_user_id)
);

CREATE INDEX idx_oauth_user ON oauth_connections(user_id);
CREATE INDEX idx_oauth_provider ON oauth_connections(provider);

-- Email Verification Tokens
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_email_verification_user ON email_verification_tokens(user_id);
CREATE INDEX idx_email_verification_token ON email_verification_tokens(token);

-- Password Reset Tokens
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_password_reset_user ON password_reset_tokens(user_id);
CREATE INDEX idx_password_reset_token ON password_reset_tokens(token);

-- =====================================================
-- Default Roles and Permissions
-- =====================================================

-- Insert system roles (will be created for each organization)
-- These are templates, actual roles created when organization is created

-- Permission categories:
-- users.*       - User management
-- agents.*      - Agent management
-- blog.*        - Blog management
-- gateway.*     - API Gateway management
-- comm.*        - Communications management
-- settings.*    - Organization settings
-- audit.*       - Audit log access
-- billing.*     - Billing management

-- =====================================================
-- Views for RBAC
-- =====================================================

-- User Permissions View
CREATE OR REPLACE VIEW user_permissions AS
SELECT
    u.id as user_id,
    u.email,
    u.organization_id,
    r.id as role_id,
    r.name as role_name,
    r.slug as role_slug,
    r.permissions
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
WHERE u.status = 'active'
AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP);

-- Active Sessions View
CREATE OR REPLACE VIEW active_user_sessions AS
SELECT
    s.id as session_id,
    s.user_id,
    u.email,
    u.full_name,
    s.ip_address,
    s.device_info,
    s.last_activity_at,
    s.expires_at,
    EXTRACT(EPOCH FROM (s.expires_at - CURRENT_TIMESTAMP))/3600 as hours_until_expiry
FROM user_sessions s
JOIN users u ON s.user_id = u.id
WHERE s.is_active = true
AND s.expires_at > CURRENT_TIMESTAMP;

-- Organization Stats View
CREATE OR REPLACE VIEW organization_stats AS
SELECT
    o.id,
    o.name,
    o.plan,
    o.status,
    COUNT(DISTINCT u.id) as user_count,
    COUNT(DISTINCT CASE WHEN u.status = 'active' THEN u.id END) as active_user_count,
    COUNT(DISTINCT ak.id) as api_key_count,
    SUM(ak.usage_count) as total_api_calls,
    MAX(u.last_login_at) as last_user_login,
    o.created_at
FROM organizations o
LEFT JOIN users u ON o.id = u.organization_id
LEFT JOIN api_keys ak ON o.id = ak.organization_id
GROUP BY o.id, o.name, o.plan, o.status, o.created_at;

-- =====================================================
-- Functions for User Management
-- =====================================================

-- Function to check if user has permission
CREATE OR REPLACE FUNCTION user_has_permission(
    p_user_id UUID,
    p_permission VARCHAR
)
RETURNS BOOLEAN AS $$
DECLARE
    has_perm BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1
        FROM user_permissions
        WHERE user_id = p_user_id
        AND (
            permissions @> to_jsonb(ARRAY[p_permission])
            OR permissions @> to_jsonb(ARRAY['*'])
        )
    ) INTO has_perm;

    RETURN has_perm;
END;
$$ LANGUAGE plpgsql;

-- Function to create organization with default roles
CREATE OR REPLACE FUNCTION create_organization_with_defaults(
    p_name VARCHAR,
    p_slug VARCHAR,
    p_owner_email VARCHAR,
    p_owner_password_hash VARCHAR
)
RETURNS UUID AS $$
DECLARE
    v_org_id UUID;
    v_user_id UUID;
    v_admin_role_id UUID;
BEGIN
    -- Create organization
    INSERT INTO organizations (name, slug)
    VALUES (p_name, p_slug)
    RETURNING id INTO v_org_id;

    -- Create admin role
    INSERT INTO roles (organization_id, name, slug, is_system_role, permissions)
    VALUES (
        v_org_id,
        'Administrator',
        'admin',
        true,
        '["*"]'::jsonb
    )
    RETURNING id INTO v_admin_role_id;

    -- Create developer role
    INSERT INTO roles (organization_id, name, slug, is_system_role, permissions)
    VALUES (
        v_org_id,
        'Developer',
        'developer',
        true,
        '["agents.*", "blog.*", "gateway.*", "comm.*"]'::jsonb
    );

    -- Create viewer role
    INSERT INTO roles (organization_id, name, slug, is_system_role, permissions)
    VALUES (
        v_org_id,
        'Viewer',
        'viewer',
        true,
        '["agents.view", "blog.view", "gateway.view", "comm.view"]'::jsonb
    );

    -- Create owner user
    INSERT INTO users (organization_id, email, password_hash, status, email_verified)
    VALUES (v_org_id, p_owner_email, p_owner_password_hash, 'active', true)
    RETURNING id INTO v_user_id;

    -- Assign admin role to owner
    INSERT INTO user_roles (user_id, role_id)
    VALUES (v_user_id, v_admin_role_id);

    -- Log the action
    INSERT INTO audit_logs (organization_id, user_id, action, resource_type, resource_id, status)
    VALUES (v_org_id, v_user_id, 'organization.created', 'organization', v_org_id, 'success');

    RETURN v_org_id;
END;
$$ LANGUAGE plpgsql;

-- Function to update last login
CREATE OR REPLACE FUNCTION update_user_login(
    p_user_id UUID,
    p_ip_address VARCHAR
)
RETURNS VOID AS $$
BEGIN
    UPDATE users
    SET last_login_at = CURRENT_TIMESTAMP,
        last_login_ip = p_ip_address,
        login_count = login_count + 1,
        failed_login_attempts = 0
    WHERE id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Function to log failed login
CREATE OR REPLACE FUNCTION log_failed_login(
    p_email VARCHAR
)
RETURNS VOID AS $$
BEGIN
    UPDATE users
    SET failed_login_attempts = failed_login_attempts + 1,
        locked_until = CASE
            WHEN failed_login_attempts >= 4
            THEN CURRENT_TIMESTAMP + INTERVAL '15 minutes'
            ELSE locked_until
        END
    WHERE email = p_email;
END;
$$ LANGUAGE plpgsql;

-- Function to clean expired sessions
CREATE OR REPLACE FUNCTION clean_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    UPDATE user_sessions
    SET is_active = false
    WHERE expires_at < CURRENT_TIMESTAMP
    AND is_active = true;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Sample Data
-- =====================================================

-- Create default organization
DO $$
DECLARE
    v_org_id UUID;
BEGIN
    -- Only create if doesn't exist
    IF NOT EXISTS (SELECT 1 FROM organizations WHERE slug = 'default') THEN
        SELECT create_organization_with_defaults(
            'Default Organization',
            'default',
            'admin@example.com',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeVu6XN6sJ/0ocWX2' -- password: 'admin123'
        ) INTO v_org_id;
    END IF;
END $$;

-- =====================================================
-- Triggers
-- =====================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_roles_updated_at BEFORE UPDATE ON roles
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Comments
-- =====================================================

COMMENT ON TABLE organizations IS 'Multi-tenant organizations/workspaces';
COMMENT ON TABLE users IS 'User accounts with authentication';
COMMENT ON TABLE roles IS 'Roles with defined permissions';
COMMENT ON TABLE user_roles IS 'User to role assignments';
COMMENT ON TABLE api_keys IS 'API keys for programmatic access';
COMMENT ON TABLE user_sessions IS 'Active user login sessions';
COMMENT ON TABLE audit_logs IS 'Audit trail of all important actions';
COMMENT ON TABLE oauth_connections IS 'OAuth provider connections';

-- =====================================================
-- Migration Complete
-- =====================================================
