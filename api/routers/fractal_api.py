"""
FractalAgents API Router
API for managing fractal agent system
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.postgres_db import get_db
from agents.fractal import FractalAgentOrchestrator
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fractal", tags=["fractal-agents"])

# ============================================
# Pydantic Models
# ============================================

class TaskRequest(BaseModel):
    description: str
    required_skills: List[str] = []
    type: str = 'general'
    complexity_score: Optional[int] = 5

class AgentCreate(BaseModel):
    name: str
    skills: List[str]
    agent_type: str = 'specialist'
    parent_agent_id: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None

class ConnectorCreate(BaseModel):
    from_agent_id: str
    to_agent_id: str
    connector_type: str = 'peer'
    strength: float = 0.5
    trust: float = 0.5

# ============================================
# Task Processing Endpoints
# ============================================

@router.post("/task")
async def process_task(
    task: TaskRequest,
    organization_id: str = "default"
):
    """Process task through fractal agent system"""
    db = get_db()
    await db.connect()

    logger.info(f"Processing task: {task.description[:100]}")

    # Initialize orchestrator
    orchestrator = FractalAgentOrchestrator(db)
    await orchestrator.initialize(organization_id)

    # Prepare task dict
    task_dict = {
        'description': task.description,
        'required_skills': task.required_skills,
        'type': task.type,
        'complexity_score': task.complexity_score,
        'organization_id': organization_id
    }

    # Process task
    result = await orchestrator.process_task(task_dict)

    return result

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get task status and result"""
    db = get_db()
    await db.connect()

    task = await db.fetchrow("""
        SELECT
            r.*,
            ra.name as router_agent_name,
            aa.name as assigned_agent_name,
            fa.name as final_agent_name
        FROM task_routing_history r
        LEFT JOIN fractal_agents ra ON r.router_agent_id = ra.id
        LEFT JOIN fractal_agents aa ON r.assigned_to_agent_id = aa.id
        LEFT JOIN fractal_agents fa ON r.final_agent_id = fa.id
        WHERE r.task_id = $1
        ORDER BY r.created_at DESC
        LIMIT 1
    """, task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task

# ============================================
# Agent Management Endpoints
# ============================================

@router.get("/agents")
async def list_agents(
    organization_id: str = "default",
    agent_type: Optional[str] = None
):
    """List all fractal agents"""
    db = get_db()
    await db.connect()

    orchestrator = FractalAgentOrchestrator(db)

    agents = await orchestrator.list_agents(
        organization_id=organization_id,
        agent_type=agent_type
    )

    return {'agents': agents}

@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get agent details"""
    db = get_db()
    await db.connect()

    orchestrator = FractalAgentOrchestrator(db)
    agent = await orchestrator.get_agent(agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Get agent's connections
    connectors = await db.fetch("""
        SELECT
            c.*,
            a.name as to_agent_name,
            a.type as to_agent_type
        FROM agent_connectors c
        LEFT JOIN fractal_agents a ON c.to_agent_id = a.id
        WHERE c.from_agent_id = $1
        ORDER BY c.strength DESC
    """, agent_id)

    # Get agent's task history
    task_history = await db.fetch("""
        SELECT
            task_id,
            task_description,
            was_successful,
            execution_time,
            created_at
        FROM task_routing_history
        WHERE assigned_to_agent_id = $1
        OR final_agent_id = $1
        ORDER BY created_at DESC
        LIMIT 10
    """, agent_id)

    return {
        'agent': agent,
        'connectors': connectors,
        'recent_tasks': task_history
    }

@router.post("/agents")
async def create_agent(
    agent: AgentCreate,
    organization_id: str = "default"
):
    """Create new fractal agent"""
    db = get_db()
    await db.connect()

    orchestrator = FractalAgentOrchestrator(db)

    agent_id = await orchestrator.create_agent(
        organization_id=organization_id,
        name=agent.name,
        skills=agent.skills,
        agent_type=agent.agent_type,
        parent_agent_id=agent.parent_agent_id,
        description=agent.description,
        system_prompt=agent.system_prompt
    )

    return {'agent_id': agent_id, 'message': f'Agent {agent.name} created successfully'}

@router.put("/agents/{agent_id}")
async def update_agent(
    agent_id: str,
    updates: Dict[str, Any]
):
    """Update agent properties"""
    db = get_db()
    await db.connect()

    orchestrator = FractalAgentOrchestrator(db)

    await orchestrator.update_agent(agent_id, **updates)

    return {'message': 'Agent updated successfully'}

@router.delete("/agents/{agent_id}")
async def delete_agent(
    agent_id: str,
    hard_delete: bool = False
):
    """Delete agent (soft or hard)"""
    db = get_db()
    await db.connect()

    orchestrator = FractalAgentOrchestrator(db)

    await orchestrator.delete_agent(agent_id, soft=not hard_delete)

    return {'message': f'Agent {"deleted" if hard_delete else "disabled"} successfully'}

# ============================================
# Connector Management Endpoints
# ============================================

@router.get("/connectors")
async def list_connectors(organization_id: str = "default"):
    """List all agent connectors"""
    db = get_db()
    await db.connect()

    connectors = await db.fetch("""
        SELECT
            c.*,
            fa.name as from_agent_name,
            ta.name as to_agent_name
        FROM agent_connectors c
        LEFT JOIN fractal_agents fa ON c.from_agent_id = fa.id
        LEFT JOIN fractal_agents ta ON c.to_agent_id = ta.id
        WHERE c.organization_id = $1
        ORDER BY c.strength DESC
    """, organization_id)

    return {'connectors': connectors}

@router.post("/connectors")
async def create_connector(connector: ConnectorCreate):
    """Create connection between agents"""
    db = get_db()
    await db.connect()

    orchestrator = FractalAgentOrchestrator(db)

    await orchestrator.create_connector(
        from_agent_id=connector.from_agent_id,
        to_agent_id=connector.to_agent_id,
        connector_type=connector.connector_type,
        strength=connector.strength,
        trust=connector.trust
    )

    return {'message': 'Connector created successfully'}

@router.delete("/connectors/{from_agent_id}/{to_agent_id}")
async def delete_connector(from_agent_id: str, to_agent_id: str):
    """Delete connector"""
    db = get_db()
    await db.connect()

    await db.execute("""
        DELETE FROM agent_connectors
        WHERE from_agent_id = $1 AND to_agent_id = $2
    """, from_agent_id, to_agent_id)

    return {'message': 'Connector deleted successfully'}

# ============================================
# Memory & Analytics Endpoints
# ============================================

@router.get("/memory")
async def query_memory(
    organization_id: str = "default",
    task_type: Optional[str] = None,
    limit: int = 10
):
    """Query collective memory"""
    db = get_db()
    await db.connect()

    orchestrator = FractalAgentOrchestrator(db)

    memory = await orchestrator.query_memory(
        organization_id=organization_id,
        task_type=task_type,
        limit=limit
    )

    return {'memory': memory}

@router.get("/system-status")
async def get_system_status(organization_id: str = "default"):
    """Get fractal system health and metrics"""
    db = get_db()
    await db.connect()

    orchestrator = FractalAgentOrchestrator(db)
    await orchestrator.initialize(organization_id)

    status = await orchestrator.get_system_status(organization_id)

    return status

@router.get("/routing-history")
async def get_routing_history(
    organization_id: str = "default",
    limit: int = 50
):
    """Get recent routing history"""
    db = get_db()
    await db.connect()

    orchestrator = FractalAgentOrchestrator(db)

    history = await orchestrator.get_routing_history(organization_id, limit)

    return {'routing_history': history}

# ============================================
# Skills Registry Endpoints
# ============================================

@router.get("/skills")
async def list_skills():
    """List all registered skills"""
    db = get_db()
    await db.connect()

    skills = await db.fetch("""
        SELECT * FROM agent_skills
        ORDER BY skill_category, skill_name
    """)

    return {'skills': skills}

@router.get("/skills/{skill_name}/agents")
async def get_agents_with_skill(
    skill_name: str,
    organization_id: str = "default"
):
    """Get all agents with specific skill"""
    db = get_db()
    await db.connect()

    agents = await db.fetch("""
        SELECT *
        FROM fractal_agents
        WHERE organization_id = $1
        AND $2 = ANY(skills)
        AND enabled = TRUE
        ORDER BY success_rate DESC
    """, organization_id, skill_name)

    return {'agents': agents, 'skill': skill_name}
