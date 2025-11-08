-- =====================================================
-- Documentation Analyzer Schema Migration
-- Version: 007
-- Description: Tables for Documentation Analysis & Auto-Schema Generation
-- =====================================================

-- Document Sources
-- Stores uploaded/linked documentation for analysis
CREATE TABLE IF NOT EXISTS doc_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'openapi', 'swagger', 'pdf', 'google_sheets', 'json_schema'
    source_type VARCHAR(50) NOT NULL DEFAULT 'url', -- 'url', 'upload', 'text'
    source_url TEXT,
    file_path TEXT,
    file_content TEXT,
    metadata JSONB,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    error_message TEXT,
    processing_started_at TIMESTAMP,
    processing_completed_at TIMESTAMP,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_doc_type CHECK (type IN ('openapi', 'swagger', 'pdf', 'google_sheets', 'json_schema', 'markdown')),
    CONSTRAINT valid_source_type CHECK (source_type IN ('url', 'upload', 'text')),
    CONSTRAINT valid_doc_status CHECK (status IN ('pending', 'processing', 'completed', 'failed'))
);

CREATE INDEX idx_doc_sources_type ON doc_sources(type);
CREATE INDEX idx_doc_sources_status ON doc_sources(status);
CREATE INDEX idx_doc_sources_created_at ON doc_sources(created_at DESC);

-- Analysis Results
-- Stores AI-powered analysis results for each document
CREATE TABLE IF NOT EXISTS doc_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_source_id UUID REFERENCES doc_sources(id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL, -- 'structure', 'endpoints', 'schemas', 'summary'
    results JSONB NOT NULL,
    ai_summary TEXT,
    ai_model VARCHAR(50), -- 'claude-3-5-sonnet', 'gpt-4', etc.
    confidence_score DECIMAL(3,2),
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_analysis_type CHECK (analysis_type IN ('structure', 'endpoints', 'schemas', 'summary', 'full'))
);

CREATE INDEX idx_doc_analyses_source ON doc_analyses(doc_source_id);
CREATE INDEX idx_doc_analyses_type ON doc_analyses(analysis_type);
CREATE INDEX idx_doc_analyses_created_at ON doc_analyses(created_at DESC);

-- Endpoints (extracted from OpenAPI/Swagger specs)
-- Stores individual API endpoints found in documentation
CREATE TABLE IF NOT EXISTS doc_endpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_source_id UUID REFERENCES doc_sources(id) ON DELETE CASCADE,
    method VARCHAR(10) NOT NULL, -- 'GET', 'POST', 'PUT', 'DELETE', 'PATCH'
    path TEXT NOT NULL,
    summary TEXT,
    description TEXT,
    ai_explanation TEXT, -- Simple explanation in user's language
    parameters JSONB,
    request_body JSONB,
    responses JSONB,
    tags TEXT[],
    security JSONB,
    deprecated BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_http_method CHECK (method IN ('GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'))
);

CREATE INDEX idx_doc_endpoints_source ON doc_endpoints(doc_source_id);
CREATE INDEX idx_doc_endpoints_method ON doc_endpoints(method);
CREATE INDEX idx_doc_endpoints_path ON doc_endpoints USING gin(to_tsvector('english', path));
CREATE INDEX idx_doc_endpoints_tags ON doc_endpoints USING gin(tags);

-- Schemas (extracted from OpenAPI components)
-- Stores data models/schemas found in documentation
CREATE TABLE IF NOT EXISTS doc_schemas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_source_id UUID REFERENCES doc_sources(id) ON DELETE CASCADE,
    schema_name VARCHAR(255) NOT NULL,
    schema_type VARCHAR(50) DEFAULT 'object', -- 'object', 'array', 'string', etc.
    properties JSONB NOT NULL,
    required_fields TEXT[],
    description TEXT,
    ai_explanation TEXT, -- Simple explanation of what this data represents
    generated_sql TEXT, -- Auto-generated CREATE TABLE statement
    sql_table_name VARCHAR(255), -- Sanitized table name
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(doc_source_id, schema_name)
);

CREATE INDEX idx_doc_schemas_source ON doc_schemas(doc_source_id);
CREATE INDEX idx_doc_schemas_name ON doc_schemas(schema_name);
CREATE INDEX idx_doc_schemas_table_name ON doc_schemas(sql_table_name);

-- Generated Tables
-- Tracks tables that were auto-created from schemas
CREATE TABLE IF NOT EXISTS doc_generated_tables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_schema_id UUID REFERENCES doc_schemas(id) ON DELETE CASCADE,
    table_name VARCHAR(255) NOT NULL,
    sql_statement TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'created', 'failed'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP,
    CONSTRAINT valid_generated_table_status CHECK (status IN ('pending', 'created', 'failed')),
    UNIQUE(table_name)
);

CREATE INDEX idx_doc_generated_tables_schema ON doc_generated_tables(doc_schema_id);
CREATE INDEX idx_doc_generated_tables_status ON doc_generated_tables(status);

-- Export History
-- Tracks data exports to external systems (Google Sheets, Telegram, etc.)
CREATE TABLE IF NOT EXISTS doc_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_source_id UUID REFERENCES doc_sources(id) ON DELETE CASCADE,
    export_type VARCHAR(50) NOT NULL, -- 'google_sheets', 'telegram', 'supabase', 'vendhub'
    destination TEXT NOT NULL, -- URL, chat_id, etc.
    data_exported JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    CONSTRAINT valid_export_type CHECK (export_type IN ('google_sheets', 'telegram', 'supabase', 'vendhub', 'webhook')),
    CONSTRAINT valid_export_status CHECK (status IN ('pending', 'in_progress', 'completed', 'failed'))
);

CREATE INDEX idx_doc_exports_source ON doc_exports(doc_source_id);
CREATE INDEX idx_doc_exports_type ON doc_exports(export_type);
CREATE INDEX idx_doc_exports_status ON doc_exports(status);

-- =====================================================
-- Helper Functions
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_doc_sources_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
DROP TRIGGER IF EXISTS trigger_update_doc_sources_updated_at ON doc_sources;
CREATE TRIGGER trigger_update_doc_sources_updated_at
    BEFORE UPDATE ON doc_sources
    FOR EACH ROW
    EXECUTE FUNCTION update_doc_sources_updated_at();

-- Function to sanitize table names (convert to valid SQL identifiers)
CREATE OR REPLACE FUNCTION sanitize_table_name(input_name TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN lower(
        regexp_replace(
            regexp_replace(input_name, '[^a-zA-Z0-9_]', '_', 'g'),
            '_+', '_', 'g'
        )
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =====================================================
-- Sample Data (for development/testing)
-- =====================================================

-- Sample OpenAPI documentation source
INSERT INTO doc_sources (name, type, source_type, source_url, status, metadata)
VALUES (
    'Sample API Documentation',
    'openapi',
    'url',
    'https://petstore.swagger.io/v2/swagger.json',
    'pending',
    '{"version": "3.0.0", "info": {"title": "Sample API"}}'::jsonb
) ON CONFLICT DO NOTHING;

-- =====================================================
-- Views for Reporting
-- =====================================================

-- View: Document Analysis Summary
CREATE OR REPLACE VIEW doc_analysis_summary AS
SELECT
    ds.id,
    ds.name,
    ds.type,
    ds.status,
    ds.created_at,
    COUNT(DISTINCT de.id) as endpoint_count,
    COUNT(DISTINCT dsch.id) as schema_count,
    COUNT(DISTINCT da.id) as analysis_count,
    MAX(ds.processing_completed_at) as last_processed
FROM doc_sources ds
LEFT JOIN doc_endpoints de ON ds.id = de.doc_source_id
LEFT JOIN doc_schemas dsch ON ds.id = dsch.doc_source_id
LEFT JOIN doc_analyses da ON ds.id = da.doc_source_id
GROUP BY ds.id, ds.name, ds.type, ds.status, ds.created_at;

-- View: Recent Exports
CREATE OR REPLACE VIEW doc_recent_exports AS
SELECT
    dex.id,
    ds.name as source_name,
    dex.export_type,
    dex.destination,
    dex.status,
    dex.created_at,
    dex.completed_at,
    (dex.completed_at - dex.created_at) as duration
FROM doc_exports dex
JOIN doc_sources ds ON dex.doc_source_id = ds.id
ORDER BY dex.created_at DESC
LIMIT 100;

-- =====================================================
-- Grants (if using role-based access)
-- =====================================================

-- Grant access to tables (adjust role as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_role;
-- GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app_role;

-- =====================================================
-- Migration Complete
-- =====================================================
