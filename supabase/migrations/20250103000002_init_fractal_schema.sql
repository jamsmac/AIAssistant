-- ============================================
-- FRACTAL AGENTS SCHEMA
-- AIAssistant v4.5 - Self-Organizing Agent System
-- ============================================

-- Enable UUID extension
-- UUID extension not needed, using gen_random_uuid()

-- ============================================
-- 1. FRACTAL AGENTS (main agents table)
-- ============================================
CREATE TABLE IF NOT EXISTS fractal_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id VARCHAR(255),  -- For multi-tenant support

    -- Identity
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL DEFAULT 'specialist',
    -- Types: 'root', 'specialist', 'bridge', 'helper'
    description TEXT,

    -- Competencies (what agent can do)
    skills JSONB DEFAULT '[]'::jsonb,
    -- Example: ["excel_parsing", "data_analysis", "report_generation"]

    -- Hierarchy (place in fractal)
    parent_agent_id UUID REFERENCES fractal_agents(id) ON DELETE SET NULL,
    level INTEGER DEFAULT 0,  -- 0 = root, 1 = first level, etc.
    path VARCHAR(1000),  -- Materialized path for tree queries: 'root.child1.child2'

    -- Configuration
    model VARCHAR(100) DEFAULT 'claude-sonnet-4-20250514',
    system_prompt TEXT,
    tools JSONB DEFAULT '[]'::jsonb,  -- Available tools
    max_tokens INTEGER DEFAULT 4096,
    temperature FLOAT DEFAULT 0.7,

    -- Performance metrics
    success_rate FLOAT DEFAULT 1.0,  -- 0.0 to 1.0
    avg_response_time INTEGER,  -- milliseconds
    total_tasks_completed INTEGER DEFAULT 0,
    total_tasks_failed INTEGER DEFAULT 0,

    -- Status & Trust
    enabled BOOLEAN DEFAULT TRUE,
    trust_level FLOAT DEFAULT 0.5,  -- 0.0 to 1.0
    last_active_at TIMESTAMP,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255),

    -- Constraints
    CONSTRAINT valid_trust_level CHECK (trust_level >= 0 AND trust_level <= 1),
    CONSTRAINT valid_success_rate CHECK (success_rate >= 0 AND success_rate <= 1),
    CONSTRAINT valid_level CHECK (level >= 0)
);

-- Indexes for fractal_agents
CREATE INDEX IF NOT EXISTS idx_fractal_agents_org ON fractal_agents(organization_id);
CREATE INDEX IF NOT EXISTS idx_fractal_agents_parent ON fractal_agents(parent_agent_id);
CREATE INDEX IF NOT EXISTS idx_fractal_agents_type ON fractal_agents(type);
CREATE INDEX IF NOT EXISTS idx_fractal_agents_enabled ON fractal_agents(enabled);
CREATE INDEX IF NOT EXISTS idx_fractal_agents_skills ON fractal_agents USING GIN(skills);
CREATE INDEX IF NOT EXISTS idx_fractal_agents_path ON fractal_agents(path);
CREATE INDEX IF NOT EXISTS idx_fractal_agents_level ON fractal_agents(level);

-- ============================================
-- 2. AGENT CONNECTORS (connections between agents)
-- ============================================
CREATE TABLE IF NOT EXISTS agent_connectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id VARCHAR(255),

    -- Connection
    from_agent_id UUID NOT NULL REFERENCES fractal_agents(id) ON DELETE CASCADE,
    to_agent_id UUID NOT NULL REFERENCES fractal_agents(id) ON DELETE CASCADE,

    -- Relationship type
    connector_type VARCHAR(50) DEFAULT 'peer',
    -- Types: 'parent-child', 'peer', 'bridge', 'fallback', 'delegation'

    -- Strength of connection
    strength FLOAT DEFAULT 0.5,  -- 0.0 to 1.0
    trust FLOAT DEFAULT 0.5,  -- 0.0 to 1.0
    weight FLOAT DEFAULT 1.0,  -- For routing priority

    -- Communication history
    total_interactions INTEGER DEFAULT 0,
    successful_handoffs INTEGER DEFAULT 0,
    failed_handoffs INTEGER DEFAULT 0,
    last_interaction_at TIMESTAMP,

    -- Routing rules
    routing_rules JSONB DEFAULT '{}'::jsonb,
    -- Example: {"when": "data_analysis", "min_confidence": 0.8}

    -- Status
    enabled BOOLEAN DEFAULT TRUE,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_connector_strength CHECK (strength >= 0 AND strength <= 1),
    CONSTRAINT valid_connector_trust CHECK (trust >= 0 AND trust <= 1),
    CONSTRAINT no_self_connection CHECK (from_agent_id != to_agent_id),
    CONSTRAINT unique_connector UNIQUE(from_agent_id, to_agent_id)
);

-- Indexes for agent_connectors
CREATE INDEX IF NOT EXISTS idx_connectors_from ON agent_connectors(from_agent_id);
CREATE INDEX IF NOT EXISTS idx_connectors_to ON agent_connectors(to_agent_id);
CREATE INDEX IF NOT EXISTS idx_connectors_type ON agent_connectors(connector_type);
CREATE INDEX IF NOT EXISTS idx_connectors_enabled ON agent_connectors(enabled);
CREATE INDEX IF NOT EXISTS idx_connectors_strength ON agent_connectors(strength);

-- ============================================
-- 3. AGENT COLLECTIVE MEMORY (shared learning)
-- ============================================
CREATE TABLE IF NOT EXISTS agent_collective_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id VARCHAR(255),

    -- Task context
    task_type VARCHAR(100) NOT NULL,
    task_category VARCHAR(50),  -- 'code', 'analysis', 'writing', etc.
    input_context TEXT NOT NULL,
    -- input_embedding VECTOR(1536),  -- For semantic search (requires pgvector extension)

    -- Solution
    solution_approach TEXT,
    solution_summary TEXT,
    participating_agents UUID[],  -- Array of agent IDs
    primary_agent_id UUID REFERENCES fractal_agents(id) ON DELETE SET NULL,

    -- Outcome
    success BOOLEAN DEFAULT TRUE,
    execution_time INTEGER,  -- milliseconds
    complexity_score FLOAT,  -- 0-10

    -- Learning
    learning_extracted TEXT,  -- What was learned from this task
    confidence_score FLOAT DEFAULT 0.5,  -- How confident in this solution
    reusability_score FLOAT DEFAULT 0.5,  -- How reusable is this solution

    -- References
    similar_tasks UUID[],  -- Links to similar past tasks
    related_memory_ids UUID[],  -- Related memory entries

    -- Usage tracking
    times_referenced INTEGER DEFAULT 0,
    last_referenced_at TIMESTAMP,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    tags TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_confidence CHECK (confidence_score >= 0 AND confidence_score <= 1),
    CONSTRAINT valid_reusability CHECK (reusability_score >= 0 AND reusability_score <= 1)
);

-- Indexes for agent_collective_memory
CREATE INDEX IF NOT EXISTS idx_memory_org ON agent_collective_memory(organization_id);
CREATE INDEX IF NOT EXISTS idx_memory_task_type ON agent_collective_memory(task_type);
CREATE INDEX IF NOT EXISTS idx_memory_category ON agent_collective_memory(task_category);
CREATE INDEX IF NOT EXISTS idx_memory_success ON agent_collective_memory(success);
CREATE INDEX IF NOT EXISTS idx_memory_confidence ON agent_collective_memory(confidence_score);
CREATE INDEX IF NOT EXISTS idx_memory_agents ON agent_collective_memory USING GIN(participating_agents);
CREATE INDEX IF NOT EXISTS idx_memory_tags ON agent_collective_memory USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_memory_created ON agent_collective_memory(created_at);

-- ============================================
-- 4. AGENT SKILLS REGISTRY (catalog of skills)
-- ============================================
CREATE TABLE IF NOT EXISTS agent_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Skill definition
    skill_name VARCHAR(100) UNIQUE NOT NULL,
    skill_category VARCHAR(50),  -- 'data', 'code', 'communication', 'analysis'
    description TEXT,

    -- Requirements
    required_tools JSONB DEFAULT '[]'::jsonb,
    required_models JSONB DEFAULT '[]'::jsonb,
    required_capabilities TEXT[],

    -- Difficulty & Performance
    difficulty_level INTEGER DEFAULT 5,  -- 1-10
    avg_execution_time INTEGER,  -- milliseconds

    -- Agents who have this skill
    agents_with_skill UUID[],  -- Array of agent IDs

    -- Performance stats across all agents
    avg_success_rate FLOAT DEFAULT 1.0,
    total_uses INTEGER DEFAULT 0,
    total_successes INTEGER DEFAULT 0,
    total_failures INTEGER DEFAULT 0,

    -- Documentation
    usage_examples TEXT[],
    best_practices TEXT,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_difficulty CHECK (difficulty_level >= 1 AND difficulty_level <= 10),
    CONSTRAINT valid_avg_success CHECK (avg_success_rate >= 0 AND avg_success_rate <= 1)
);

-- Indexes for agent_skills
CREATE INDEX IF NOT EXISTS idx_skills_name ON agent_skills(skill_name);
CREATE INDEX IF NOT EXISTS idx_skills_category ON agent_skills(skill_category);
CREATE INDEX IF NOT EXISTS idx_skills_agents ON agent_skills USING GIN(agents_with_skill);
CREATE INDEX IF NOT EXISTS idx_skills_difficulty ON agent_skills(difficulty_level);

-- ============================================
-- 5. TASK ROUTING HISTORY (routing decisions log)
-- ============================================
CREATE TABLE IF NOT EXISTS task_routing_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id VARCHAR(255),

    -- Task reference
    task_id VARCHAR(255),  -- External task ID
    task_description TEXT,
    task_type VARCHAR(100),
    required_skills TEXT[],

    -- Routing decision
    router_agent_id UUID REFERENCES fractal_agents(id) ON DELETE SET NULL,
    assigned_to_agent_id UUID REFERENCES fractal_agents(id) ON DELETE SET NULL,
    routing_reason TEXT,
    routing_confidence FLOAT,
    routing_algorithm VARCHAR(50) DEFAULT 'skill_match',

    -- Alternative options considered
    alternatives JSONB DEFAULT '[]'::jsonb,
    -- Example: [{"agent_id": "...", "score": 0.7, "reason": "..."}]

    -- Execution
    execution_started_at TIMESTAMP,
    execution_completed_at TIMESTAMP,
    execution_time INTEGER,  -- milliseconds

    -- Outcome
    was_successful BOOLEAN,
    was_rerouted BOOLEAN DEFAULT FALSE,
    rerouted_to_agent_id UUID REFERENCES fractal_agents(id) ON DELETE SET NULL,
    reroute_reason TEXT,
    final_agent_id UUID REFERENCES fractal_agents(id) ON DELETE SET NULL,

    -- Error handling
    error_occurred BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Learning
    feedback_score FLOAT,  -- User/system feedback
    learning_notes TEXT,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_routing_confidence CHECK (routing_confidence IS NULL OR (routing_confidence >= 0 AND routing_confidence <= 1)),
    CONSTRAINT valid_feedback CHECK (feedback_score IS NULL OR (feedback_score >= 0 AND feedback_score <= 1))
);

-- Indexes for task_routing_history
CREATE INDEX IF NOT EXISTS idx_routing_org ON task_routing_history(organization_id);
CREATE INDEX IF NOT EXISTS idx_routing_task ON task_routing_history(task_id);
CREATE INDEX IF NOT EXISTS idx_routing_router ON task_routing_history(router_agent_id);
CREATE INDEX IF NOT EXISTS idx_routing_assigned ON task_routing_history(assigned_to_agent_id);
CREATE INDEX IF NOT EXISTS idx_routing_success ON task_routing_history(was_successful);
CREATE INDEX IF NOT EXISTS idx_routing_rerouted ON task_routing_history(was_rerouted);
CREATE INDEX IF NOT EXISTS idx_routing_created ON task_routing_history(created_at);
CREATE INDEX IF NOT EXISTS idx_routing_type ON task_routing_history(task_type);

-- ============================================
-- 6. AGENT PERFORMANCE METRICS (time-series metrics)
-- ============================================
CREATE TABLE IF NOT EXISTS agent_performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES fractal_agents(id) ON DELETE CASCADE,

    -- Time period
    metric_date DATE NOT NULL,
    metric_hour INTEGER,  -- 0-23 for hourly metrics

    -- Performance metrics
    tasks_completed INTEGER DEFAULT 0,
    tasks_failed INTEGER DEFAULT 0,
    avg_response_time INTEGER,  -- milliseconds
    total_tokens_used INTEGER DEFAULT 0,
    total_cost FLOAT DEFAULT 0.0,

    -- Quality metrics
    avg_confidence FLOAT,
    avg_user_rating FLOAT,
    error_rate FLOAT,

    -- Collaboration metrics
    tasks_delegated INTEGER DEFAULT 0,
    tasks_received INTEGER DEFAULT 0,
    collaboration_score FLOAT,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_agent_metric UNIQUE(agent_id, metric_date, metric_hour)
);

-- Indexes for agent_performance_metrics
CREATE INDEX IF NOT EXISTS idx_metrics_agent ON agent_performance_metrics(agent_id);
CREATE INDEX IF NOT EXISTS idx_metrics_date ON agent_performance_metrics(metric_date);
CREATE INDEX IF NOT EXISTS idx_metrics_hour ON agent_performance_metrics(metric_hour);

-- ============================================
-- HELPER FUNCTIONS
-- ============================================

-- Function to update agent success rate
CREATE OR REPLACE FUNCTION update_agent_success_rate()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE fractal_agents
    SET
        total_tasks_completed = total_tasks_completed + CASE WHEN NEW.success THEN 1 ELSE 0 END,
        total_tasks_failed = total_tasks_failed + CASE WHEN NOT NEW.success THEN 1 ELSE 0 END,
        success_rate = (
            (total_tasks_completed + CASE WHEN NEW.success THEN 1 ELSE 0 END)::FLOAT /
            (total_tasks_completed + total_tasks_failed + 1)::FLOAT
        ),
        last_active_at = NOW(),
        updated_at = NOW()
    WHERE id = ANY(NEW.participating_agents);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update success rate
DROP TRIGGER IF EXISTS trigger_update_success_rate ON agent_collective_memory;
CREATE TRIGGER trigger_update_success_rate
    AFTER INSERT ON agent_collective_memory
    FOR EACH ROW
    EXECUTE FUNCTION update_agent_success_rate();

-- Function to update agent path when hierarchy changes
CREATE OR REPLACE FUNCTION update_agent_path()
RETURNS TRIGGER AS $$
DECLARE
    parent_path VARCHAR(1000);
BEGIN
    IF NEW.parent_agent_id IS NULL THEN
        NEW.path := NEW.name;
        NEW.level := 0;
    ELSE
        SELECT path, level INTO parent_path, NEW.level
        FROM fractal_agents
        WHERE id = NEW.parent_agent_id;

        NEW.path := parent_path || '.' || NEW.name;
        NEW.level := NEW.level + 1;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update path
DROP TRIGGER IF EXISTS trigger_update_agent_path ON fractal_agents;
CREATE TRIGGER trigger_update_agent_path
    BEFORE INSERT OR UPDATE OF parent_agent_id, name ON fractal_agents
    FOR EACH ROW
    EXECUTE FUNCTION update_agent_path();

-- ============================================
-- INITIAL DATA (Optional - for testing)
-- ============================================

-- Insert default root agent
INSERT INTO fractal_agents (
    id,
    name,
    type,
    description,
    skills,
    level,
    path,
    system_prompt,
    trust_level,
    organization_id
) VALUES (
    gen_random_uuid(),
    'RootOrchestrator',
    'root',
    'Main orchestrator that coordinates all other agents',
    '["task_routing", "planning", "coordination", "delegation"]'::jsonb,
    0,
    'RootOrchestrator',
    'You are the root orchestrator agent. Your role is to analyze incoming tasks and route them to the most appropriate specialist agents. You can break down complex tasks into subtasks and coordinate their execution.',
    1.0,
    'default'
) ON CONFLICT DO NOTHING;

-- Insert common skills
INSERT INTO agent_skills (skill_name, skill_category, description) VALUES
    ('data_analysis', 'data', 'Analyze and interpret data'),
    ('code_generation', 'code', 'Write and generate code'),
    ('code_review', 'code', 'Review and improve code quality'),
    ('writing', 'communication', 'Write articles, documentation, content'),
    ('seo_optimization', 'communication', 'Optimize content for SEO'),
    ('image_generation', 'creative', 'Generate images and graphics'),
    ('social_media', 'communication', 'Create social media content')
ON CONFLICT DO NOTHING;

-- ============================================
-- VIEWS FOR EASY QUERYING
-- ============================================

-- View: Agent hierarchy with full details
CREATE OR REPLACE VIEW v_agent_hierarchy AS
SELECT
    a.id,
    a.name,
    a.type,
    a.level,
    a.path,
    a.skills,
    a.success_rate,
    a.total_tasks_completed,
    a.enabled,
    p.name as parent_name,
    p.id as parent_id,
    (SELECT COUNT(*) FROM fractal_agents WHERE parent_agent_id = a.id) as child_count,
    (SELECT COUNT(*) FROM agent_connectors WHERE from_agent_id = a.id) as outgoing_connections,
    (SELECT COUNT(*) FROM agent_connectors WHERE to_agent_id = a.id) as incoming_connections
FROM fractal_agents a
LEFT JOIN fractal_agents p ON a.parent_agent_id = p.id
ORDER BY a.path;

-- View: Agent performance summary
CREATE OR REPLACE VIEW v_agent_performance AS
SELECT
    a.id,
    a.name,
    a.type,
    a.total_tasks_completed,
    a.total_tasks_failed,
    a.success_rate,
    a.avg_response_time,
    a.trust_level,
    a.last_active_at,
    (SELECT COUNT(*) FROM agent_collective_memory WHERE primary_agent_id = a.id) as memory_entries,
    (SELECT AVG(confidence_score) FROM agent_collective_memory WHERE primary_agent_id = a.id) as avg_memory_confidence
FROM fractal_agents a
WHERE a.enabled = TRUE
ORDER BY a.total_tasks_completed DESC;

-- ============================================
-- SCHEMA COMPLETE
-- ============================================

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_app_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO your_app_user;
