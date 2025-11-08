-- FractalAgents System Schema
-- Version: 1.0.0
-- Description: Self-organizing AI agent network with collective memory

-- ============================================
-- 1. FRACTAL AGENTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS fractal_agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id VARCHAR(255) DEFAULT 'default' NOT NULL,
    name VARCHAR(255) NOT NULL,
    agent_type VARCHAR(50) NOT NULL, -- root, specialist, coordinator, worker
    description TEXT,
    skills TEXT[], -- Array of skill tags
    system_prompt TEXT,
    parent_agent_id UUID REFERENCES fractal_agents(id) ON DELETE SET NULL,

    -- Performance metrics
    total_tasks_processed INTEGER DEFAULT 0 NOT NULL,
    successful_tasks INTEGER DEFAULT 0 NOT NULL,
    failed_tasks INTEGER DEFAULT 0 NOT NULL,
    avg_response_time_ms FLOAT DEFAULT 0,
    avg_confidence_score FLOAT DEFAULT 0,

    -- Configuration
    temperature FLOAT DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 4096,
    model VARCHAR(100) DEFAULT 'claude-3-5-sonnet-20241022',
    provider VARCHAR(50) DEFAULT 'anthropic',
    trust_level FLOAT DEFAULT 0.5 CHECK (trust_level >= 0 AND trust_level <= 1),

    -- Status
    is_active BOOLEAN DEFAULT true NOT NULL,
    last_active_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    metadata JSONB DEFAULT '{}' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    UNIQUE(organization_id, name)
);

CREATE INDEX idx_fractal_agents_org ON fractal_agents(organization_id);
CREATE INDEX idx_fractal_agents_type ON fractal_agents(agent_type);
CREATE INDEX idx_fractal_agents_parent ON fractal_agents(parent_agent_id);
CREATE INDEX idx_fractal_agents_active ON fractal_agents(is_active) WHERE is_active = true;
CREATE INDEX idx_fractal_agents_skills ON fractal_agents USING GIN(skills);

-- ============================================
-- 2. AGENT CONNECTORS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS agent_connectors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_agent_id UUID REFERENCES fractal_agents(id) ON DELETE CASCADE NOT NULL,
    to_agent_id UUID REFERENCES fractal_agents(id) ON DELETE CASCADE NOT NULL,

    connector_type VARCHAR(50) NOT NULL, -- parent_child, peer, specialist, fallback
    strength FLOAT DEFAULT 0.5 CHECK (strength >= 0 AND strength <= 1),
    trust FLOAT DEFAULT 0.5 CHECK (trust >= 0 AND trust <= 1),

    -- Usage stats
    times_used INTEGER DEFAULT 0 NOT NULL,
    successful_routes INTEGER DEFAULT 0 NOT NULL,
    failed_routes INTEGER DEFAULT 0 NOT NULL,
    avg_satisfaction_score FLOAT DEFAULT 0,

    -- Routing rules
    routing_rules JSONB DEFAULT '{}', -- Conditions for when to use this connector
    priority INTEGER DEFAULT 0, -- Higher priority connectors are tried first

    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    UNIQUE(from_agent_id, to_agent_id, connector_type)
);

CREATE INDEX idx_agent_connectors_from ON agent_connectors(from_agent_id);
CREATE INDEX idx_agent_connectors_to ON agent_connectors(to_agent_id);
CREATE INDEX idx_agent_connectors_type ON agent_connectors(connector_type);
CREATE INDEX idx_agent_connectors_active ON agent_connectors(is_active) WHERE is_active = true;
CREATE INDEX idx_agent_connectors_priority ON agent_connectors(priority DESC);

-- ============================================
-- 3. AGENT COLLECTIVE MEMORY TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS agent_collective_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id VARCHAR(255) DEFAULT 'default' NOT NULL,

    -- Task information
    task_description TEXT NOT NULL,
    task_type VARCHAR(100),
    required_skills TEXT[],
    complexity_score INTEGER DEFAULT 5 CHECK (complexity_score >= 1 AND complexity_score <= 10),

    -- Agent that handled it
    agent_id UUID REFERENCES fractal_agents(id) ON DELETE SET NULL,
    agent_name VARCHAR(255),

    -- Execution details
    success BOOLEAN NOT NULL,
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    execution_time_ms INTEGER,
    tokens_used INTEGER,
    cost DECIMAL(10, 6),

    -- Learning data
    result_summary TEXT,
    learnings JSONB, -- Key insights extracted from this execution
    errors_encountered TEXT[],
    improvements_suggested TEXT[],

    -- Context
    context JSONB DEFAULT '{}',
    input_hash VARCHAR(64), -- Hash of input for similarity matching

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    -- For finding similar tasks
    embedding VECTOR(1536) -- For semantic search (requires pgvector extension)
);

CREATE INDEX idx_collective_memory_org ON agent_collective_memory(organization_id);
CREATE INDEX idx_collective_memory_agent ON agent_collective_memory(agent_id);
CREATE INDEX idx_collective_memory_type ON agent_collective_memory(task_type);
CREATE INDEX idx_collective_memory_success ON agent_collective_memory(success);
CREATE INDEX idx_collective_memory_created ON agent_collective_memory(created_at DESC);
CREATE INDEX idx_collective_memory_skills ON agent_collective_memory USING GIN(required_skills);
CREATE INDEX idx_collective_memory_hash ON agent_collective_memory(input_hash);
-- Uncomment if pgvector is available:
-- CREATE INDEX idx_collective_memory_embedding ON agent_collective_memory USING ivfflat (embedding vector_cosine_ops);

-- ============================================
-- 4. AGENT SKILLS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS agent_skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    skill_name VARCHAR(255) UNIQUE NOT NULL,
    skill_category VARCHAR(100), -- technical, creative, analysis, communication, etc.
    description TEXT,

    -- Metrics
    total_uses INTEGER DEFAULT 0 NOT NULL,
    success_rate FLOAT DEFAULT 0,
    avg_confidence FLOAT DEFAULT 0,
    avg_execution_time_ms FLOAT DEFAULT 0,

    -- Agents with this skill
    agent_count INTEGER DEFAULT 0 NOT NULL,

    -- Requirements
    required_model_capabilities TEXT[],
    min_tokens INTEGER DEFAULT 1000,

    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_agent_skills_category ON agent_skills(skill_category);
CREATE INDEX idx_agent_skills_success ON agent_skills(success_rate DESC);
CREATE INDEX idx_agent_skills_usage ON agent_skills(total_uses DESC);

-- ============================================
-- 5. TASK ROUTING HISTORY TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS task_routing_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID DEFAULT uuid_generate_v4(),
    organization_id VARCHAR(255) DEFAULT 'default' NOT NULL,

    -- Task details
    task_description TEXT NOT NULL,
    task_type VARCHAR(100),
    required_skills TEXT[],
    complexity_score INTEGER,

    -- Routing decision
    router_agent_id UUID REFERENCES fractal_agents(id) ON DELETE SET NULL,
    assigned_to_agent_id UUID REFERENCES fractal_agents(id) ON DELETE SET NULL,
    routing_reason TEXT, -- Why this agent was chosen
    routing_confidence FLOAT,
    alternatives_considered JSONB, -- Other agents that were considered

    -- Execution
    execution_started_at TIMESTAMP WITH TIME ZONE,
    execution_completed_at TIMESTAMP WITH TIME ZONE,
    execution_time_ms INTEGER,

    -- Result
    success BOOLEAN,
    confidence_score FLOAT,
    result_quality_score FLOAT,
    tokens_used INTEGER,
    cost DECIMAL(10, 6),

    -- Learning
    was_correct_choice BOOLEAN, -- Did this agent perform well?
    user_feedback_score INTEGER CHECK (user_feedback_score >= 1 AND user_feedback_score <= 5),
    notes TEXT,

    -- Hierarchy tracking
    parent_task_id UUID, -- If this task was decomposed from a larger task
    subtask_count INTEGER DEFAULT 0,
    final_agent_id UUID REFERENCES fractal_agents(id) ON DELETE SET NULL, -- Agent that actually completed it

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_routing_history_org ON task_routing_history(organization_id);
CREATE INDEX idx_routing_history_task ON task_routing_history(task_id);
CREATE INDEX idx_routing_history_router ON task_routing_history(router_agent_id);
CREATE INDEX idx_routing_history_assigned ON task_routing_history(assigned_to_agent_id);
CREATE INDEX idx_routing_history_final ON task_routing_history(final_agent_id);
CREATE INDEX idx_routing_history_parent ON task_routing_history(parent_task_id);
CREATE INDEX idx_routing_history_created ON task_routing_history(created_at DESC);
CREATE INDEX idx_routing_history_success ON task_routing_history(success);
CREATE INDEX idx_routing_history_skills ON task_routing_history USING GIN(required_skills);

-- ============================================
-- TRIGGERS
-- ============================================

-- Auto-update updated_at on fractal_agents
CREATE TRIGGER update_fractal_agents_updated_at
    BEFORE UPDATE ON fractal_agents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Auto-update updated_at on agent_connectors
CREATE TRIGGER update_agent_connectors_updated_at
    BEFORE UPDATE ON agent_connectors
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Auto-update updated_at on agent_skills
CREATE TRIGGER update_agent_skills_updated_at
    BEFORE UPDATE ON agent_skills
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- HELPER FUNCTIONS
-- ============================================

-- Function to update agent metrics after task completion
CREATE OR REPLACE FUNCTION update_agent_metrics(
    p_agent_id UUID,
    p_success BOOLEAN,
    p_response_time_ms INTEGER,
    p_confidence_score FLOAT
)
RETURNS VOID AS $$
BEGIN
    UPDATE fractal_agents
    SET
        total_tasks_processed = total_tasks_processed + 1,
        successful_tasks = successful_tasks + CASE WHEN p_success THEN 1 ELSE 0 END,
        failed_tasks = failed_tasks + CASE WHEN NOT p_success THEN 1 ELSE 0 END,
        avg_response_time_ms = (
            (avg_response_time_ms * total_tasks_processed + p_response_time_ms) /
            (total_tasks_processed + 1)
        ),
        avg_confidence_score = (
            (avg_confidence_score * total_tasks_processed + COALESCE(p_confidence_score, 0)) /
            (total_tasks_processed + 1)
        ),
        last_active_at = NOW(),
        updated_at = NOW()
    WHERE id = p_agent_id;
END;
$$ LANGUAGE plpgsql;

-- Function to update connector metrics after use
CREATE OR REPLACE FUNCTION update_connector_metrics(
    p_connector_id UUID,
    p_success BOOLEAN,
    p_satisfaction_score FLOAT DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    UPDATE agent_connectors
    SET
        times_used = times_used + 1,
        successful_routes = successful_routes + CASE WHEN p_success THEN 1 ELSE 0 END,
        failed_routes = failed_routes + CASE WHEN NOT p_success THEN 1 ELSE 0 END,
        avg_satisfaction_score = (
            (avg_satisfaction_score * times_used + COALESCE(p_satisfaction_score, 0)) /
            (times_used + 1)
        ),
        updated_at = NOW()
    WHERE id = p_connector_id;
END;
$$ LANGUAGE plpgsql;

-- Function to find similar tasks in collective memory
CREATE OR REPLACE FUNCTION find_similar_tasks(
    p_task_description TEXT,
    p_required_skills TEXT[],
    p_limit INTEGER DEFAULT 5
)
RETURNS TABLE (
    memory_id UUID,
    task_description TEXT,
    agent_name VARCHAR,
    success BOOLEAN,
    confidence_score FLOAT,
    similarity_score FLOAT
) AS $$
BEGIN
    -- Simple similarity based on skill overlap and text matching
    -- For production, use pgvector for semantic search
    RETURN QUERY
    SELECT
        m.id,
        m.task_description,
        m.agent_name,
        m.success,
        m.confidence_score,
        (
            -- Skill overlap score (0-1)
            COALESCE(
                array_length(
                    ARRAY(SELECT unnest(m.required_skills) INTERSECT SELECT unnest(p_required_skills)),
                    1
                )::FLOAT /
                GREATEST(array_length(m.required_skills, 1), array_length(p_required_skills, 1)),
                0
            ) * 0.7 +
            -- Text similarity score (0-1) - simplified
            CASE
                WHEN m.task_description ILIKE '%' || p_task_description || '%' THEN 0.3
                ELSE 0
            END
        ) AS similarity
    FROM agent_collective_memory m
    WHERE m.success = true
    ORDER BY similarity DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- VIEWS FOR COMMON QUERIES
-- ============================================

-- Agent performance summary
CREATE OR REPLACE VIEW agent_performance_summary AS
SELECT
    a.id,
    a.organization_id,
    a.name,
    a.agent_type,
    a.skills,
    a.total_tasks_processed,
    a.successful_tasks,
    a.failed_tasks,
    CASE
        WHEN a.total_tasks_processed > 0
        THEN (a.successful_tasks::FLOAT / a.total_tasks_processed * 100)::DECIMAL(5,2)
        ELSE 0
    END as success_rate_percent,
    a.avg_response_time_ms,
    a.avg_confidence_score,
    a.trust_level,
    a.is_active,
    a.last_active_at,
    (
        SELECT COUNT(*)
        FROM agent_connectors
        WHERE from_agent_id = a.id AND is_active = true
    ) as outgoing_connections,
    (
        SELECT COUNT(*)
        FROM agent_connectors
        WHERE to_agent_id = a.id AND is_active = true
    ) as incoming_connections
FROM fractal_agents a;

-- Task routing efficiency
CREATE OR REPLACE VIEW task_routing_efficiency AS
SELECT
    organization_id,
    DATE_TRUNC('hour', created_at) as time_bucket,
    COUNT(*) as total_tasks,
    COUNT(*) FILTER (WHERE success = true) as successful_tasks,
    AVG(execution_time_ms) as avg_execution_time_ms,
    AVG(confidence_score) as avg_confidence,
    AVG(routing_confidence) as avg_routing_confidence,
    COUNT(DISTINCT assigned_to_agent_id) as agents_used
FROM task_routing_history
GROUP BY organization_id, time_bucket
ORDER BY time_bucket DESC;

-- ============================================
-- SEED DATA - Default Root Agent
-- ============================================

INSERT INTO fractal_agents (
    organization_id,
    name,
    agent_type,
    description,
    skills,
    system_prompt,
    trust_level,
    is_active
) VALUES (
    'default',
    'RootOrchestrator',
    'root',
    'Main orchestrator agent that routes tasks to specialized agents',
    ARRAY['task_routing', 'task_decomposition', 'coordination', 'orchestration'],
    'You are the root orchestrator agent. Your role is to analyze incoming tasks, decompose them if needed, and route them to the most appropriate specialized agents. You maintain the health and efficiency of the entire agent network.',
    1.0,
    true
) ON CONFLICT (organization_id, name) DO NOTHING;

-- ============================================
-- COMMENTS
-- ============================================

COMMENT ON TABLE fractal_agents IS 'Self-organizing AI agents with skills and performance metrics';
COMMENT ON TABLE agent_connectors IS 'Connections between agents defining routing relationships';
COMMENT ON TABLE agent_collective_memory IS 'Shared memory of all tasks processed, enabling learning';
COMMENT ON TABLE agent_skills IS 'Registry of all skills available in the system';
COMMENT ON TABLE task_routing_history IS 'Complete history of task routing decisions and outcomes';

-- Migration complete
SELECT 'FractalAgents schema created successfully' AS status;
