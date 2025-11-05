"""
FractalAgentOrchestrator - Main coordinator for the fractal agent system
Manages root agent, agent creation, task processing, and system health
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
from .base_agent import FractalAgent

logger = logging.getLogger(__name__)


class FractalAgentOrchestrator:
    """
    Main orchestrator for fractal agent system

    Responsibilities:
    - Initialize and manage root agent
    - Create and configure new agents
    - Process tasks through the agent network
    - Manage agent connectors
    - Monitor system health
    - Query collective memory
    """

    def __init__(self, db, anthropic_api_key: Optional[str] = None):
        """
        Initialize orchestrator

        Args:
            db: PostgresDB instance
            anthropic_api_key: Optional Anthropic API key
        """
        self.db = db
        self.anthropic_api_key = anthropic_api_key
        self.root_agent: Optional[FractalAgent] = None
        self._initialized = False

    async def initialize(self, organization_id: str):
        """
        Initialize orchestrator with root agent for organization

        Args:
            organization_id: Organization ID
        """
        if self._initialized:
            return

        try:
            # Get or create root agent for organization
            root_data = await self.db.fetchrow("""
                SELECT * FROM fractal_agents
                WHERE organization_id = $1
                AND type = 'root'
                AND enabled = TRUE
                ORDER BY created_at ASC
                LIMIT 1
            """, organization_id)

            if not root_data:
                logger.info(f"No root agent found for org {organization_id}, creating one...")
                root_id = await self.create_root_agent(organization_id)
            else:
                root_id = str(root_data['id'])

            # Initialize root agent
            self.root_agent = FractalAgent(
                root_id,
                self.db,
                self.anthropic_api_key
            )
            await self.root_agent.initialize()

            self._initialized = True

            logger.info(
                f"Orchestrator initialized with root agent: {self.root_agent.data['name']} "
                f"(org: {organization_id})"
            )

        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            raise

    async def process_task(self, task: Dict) -> Dict:
        """
        Process task through fractal agent system

        Args:
            task: Task dictionary with keys:
                - description: str
                - required_skills: List[str]
                - type: str (optional)
                - organization_id: str
                - id: str (optional)

        Returns:
            Result dictionary
        """
        if not self._initialized:
            raise ValueError("Orchestrator not initialized. Call initialize() first.")

        # Ensure task has ID
        if 'id' not in task:
            task['id'] = str(uuid.uuid4())

        logger.info(f"Processing task {task['id']}: {task.get('description', '')[:100]}")

        start_time = datetime.now()

        try:
            # Start with root agent
            result = await self.root_agent.execute_task(task)

            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            logger.info(
                f"Task {task['id']} completed in {execution_time}ms: "
                f"success={result.get('success', False)}"
            )

            # Update routing history with execution result
            await self.db.execute("""
                UPDATE task_routing_history
                SET
                    execution_completed_at = NOW(),
                    execution_time = $2,
                    was_successful = $3,
                    final_agent_id = $4
                WHERE task_id = $1
                AND execution_completed_at IS NULL
            """, task['id'], execution_time, result.get('success', False), result.get('agent_id'))

            return result

        except Exception as e:
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            logger.error(f"Task {task['id']} failed: {e}")

            # Update routing history with error
            await self.db.execute("""
                UPDATE task_routing_history
                SET
                    execution_completed_at = NOW(),
                    execution_time = $2,
                    was_successful = FALSE,
                    error_occurred = TRUE,
                    error_message = $3
                WHERE task_id = $1
                AND execution_completed_at IS NULL
            """, task['id'], execution_time, str(e))

            return {
                'task_id': task['id'],
                'success': False,
                'error': str(e),
                'execution_time': execution_time
            }

    async def create_agent(
        self,
        organization_id: str,
        name: str,
        skills: List[str],
        agent_type: str = 'specialist',
        parent_agent_id: Optional[str] = None,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
        model: str = 'claude-sonnet-4-20250514'
    ) -> str:
        """
        Create new agent in the fractal system

        Args:
            organization_id: Organization ID
            name: Agent name
            skills: List of skills
            agent_type: Agent type ('root', 'specialist', 'bridge', 'helper')
            parent_agent_id: Optional parent agent ID
            description: Optional description
            system_prompt: Optional system prompt
            model: LLM model to use

        Returns:
            Agent ID
        """
        # Generate default system prompt if not provided
        if not system_prompt:
            system_prompt = self._generate_system_prompt(name, skills, agent_type)

        # Determine level
        level = 0
        if parent_agent_id:
            parent_level = await self.db.fetchval("""
                SELECT level FROM fractal_agents WHERE id = $1
            """, parent_agent_id)
            level = (parent_level or 0) + 1

        agent_id = await self.db.fetchval("""
            INSERT INTO fractal_agents (
                organization_id,
                name,
                type,
                description,
                skills,
                parent_agent_id,
                level,
                model,
                system_prompt,
                trust_level,
                enabled
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id
        """,
        organization_id,
        name,
        agent_type,
        description or f"{name} agent specializing in {', '.join(skills[:3])}",
        skills,
        parent_agent_id,
        level,
        model,
        system_prompt,
        0.7,  # Initial trust level
        True
        )

        logger.info(f"Created agent: {name} (ID: {agent_id}, skills: {skills})")

        # Auto-create connector to parent if parent exists
        if parent_agent_id:
            await self.create_connector(
                from_agent_id=parent_agent_id,
                to_agent_id=str(agent_id),
                connector_type='parent-child',
                strength=0.8
            )

        return str(agent_id)

    async def create_root_agent(self, organization_id: str) -> str:
        """
        Create root orchestrator agent for organization

        Args:
            organization_id: Organization ID

        Returns:
            Root agent ID
        """
        system_prompt = """You are the Root Orchestrator Agent, the central coordinator of a fractal agent network.

Your responsibilities:
1. Analyze incoming tasks and understand their requirements
2. Route tasks to the most appropriate specialist agents based on their skills
3. Break down complex tasks into manageable sub-tasks
4. Coordinate execution across multiple agents
5. Aggregate results and provide coherent final outputs
6. Learn from past executions to improve routing decisions

You have access to a network of specialist agents, each with unique skills. When you receive a task:
1. Identify required skills
2. Check which agents have those skills
3. Consider past performance and trust levels
4. Route to the best-suited agent or break into sub-tasks

Always provide clear, well-structured responses."""

        agent_id = await self.create_agent(
            organization_id=organization_id,
            name='RootOrchestrator',
            skills=['task_routing', 'planning', 'coordination', 'delegation', 'aggregation'],
            agent_type='root',
            description='Main orchestrator that coordinates all other agents',
            system_prompt=system_prompt
        )

        logger.info(f"Created root agent for org {organization_id}: {agent_id}")

        return agent_id

    async def create_connector(
        self,
        from_agent_id: str,
        to_agent_id: str,
        connector_type: str = 'peer',
        strength: float = 0.5,
        trust: float = 0.5,
        routing_rules: Optional[Dict] = None
    ):
        """
        Create connection between two agents

        Args:
            from_agent_id: Source agent ID
            to_agent_id: Target agent ID
            connector_type: Type of connection
            strength: Connection strength (0-1)
            trust: Trust level (0-1)
            routing_rules: Optional routing rules
        """
        # Get organization from source agent
        org_id = await self.db.fetchval("""
            SELECT organization_id FROM fractal_agents WHERE id = $1
        """, from_agent_id)

        await self.db.execute("""
            INSERT INTO agent_connectors (
                organization_id,
                from_agent_id,
                to_agent_id,
                connector_type,
                strength,
                trust,
                routing_rules,
                enabled
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (from_agent_id, to_agent_id)
            DO UPDATE SET
                connector_type = EXCLUDED.connector_type,
                strength = EXCLUDED.strength,
                trust = EXCLUDED.trust,
                routing_rules = EXCLUDED.routing_rules,
                updated_at = NOW()
        """,
        org_id,
        from_agent_id,
        to_agent_id,
        connector_type,
        strength,
        trust,
        routing_rules or {},
        True
        )

        logger.info(f"Created connector: {from_agent_id} -> {to_agent_id} ({connector_type})")

    async def delete_agent(self, agent_id: str, soft: bool = True):
        """
        Delete agent (soft or hard delete)

        Args:
            agent_id: Agent ID
            soft: If True, just disable. If False, actually delete.
        """
        if soft:
            await self.db.execute("""
                UPDATE fractal_agents
                SET enabled = FALSE, updated_at = NOW()
                WHERE id = $1
            """, agent_id)
            logger.info(f"Agent {agent_id} disabled")
        else:
            await self.db.execute("""
                DELETE FROM fractal_agents WHERE id = $1
            """, agent_id)
            logger.info(f"Agent {agent_id} deleted")

    async def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Get agent details"""
        return await self.db.fetchrow("""
            SELECT * FROM fractal_agents WHERE id = $1
        """, agent_id)

    async def list_agents(
        self,
        organization_id: str,
        agent_type: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[Dict]:
        """
        List agents for organization

        Args:
            organization_id: Organization ID
            agent_type: Optional filter by type
            enabled_only: Only return enabled agents

        Returns:
            List of agent dictionaries
        """
        query = """
            SELECT
                a.*,
                (SELECT COUNT(*) FROM fractal_agents WHERE parent_agent_id = a.id) as child_count,
                (SELECT COUNT(*) FROM agent_connectors WHERE from_agent_id = a.id) as outgoing_connections,
                (SELECT COUNT(*) FROM agent_connectors WHERE to_agent_id = a.id) as incoming_connections
            FROM fractal_agents a
            WHERE a.organization_id = $1
        """

        params = [organization_id]
        param_count = 1

        if agent_type:
            param_count += 1
            query += f" AND a.type = ${param_count}"
            params.append(agent_type)

        if enabled_only:
            query += " AND a.enabled = TRUE"

        query += " ORDER BY a.level, a.name"

        agents = await self.db.fetch(query, *params)
        return agents

    async def get_system_status(self, organization_id: str) -> Dict[str, Any]:
        """
        Get status of entire fractal agent system

        Returns comprehensive metrics about the system
        """
        # Count agents by type
        agent_stats = await self.db.fetch("""
            SELECT
                type,
                COUNT(*) as count,
                AVG(success_rate) as avg_success_rate,
                AVG(total_tasks_completed) as avg_tasks_completed
            FROM fractal_agents
            WHERE organization_id = $1 AND enabled = TRUE
            GROUP BY type
            ORDER BY type
        """, organization_id)

        # Total connectors
        total_connectors = await self.db.fetchval("""
            SELECT COUNT(*) FROM agent_connectors
            WHERE organization_id = $1 AND enabled = TRUE
        """, organization_id)

        # Memory stats
        memory_stats = await self.db.fetchrow("""
            SELECT
                COUNT(*) as total_entries,
                COUNT(*) FILTER (WHERE success = TRUE) as successful_entries,
                AVG(confidence_score) as avg_confidence,
                AVG(execution_time) as avg_execution_time
            FROM agent_collective_memory
            WHERE organization_id = $1
        """, organization_id)

        # Recent routing history
        recent_tasks = await self.db.fetchval("""
            SELECT COUNT(*) FROM task_routing_history
            WHERE organization_id = $1
            AND created_at > NOW() - INTERVAL '24 hours'
        """, organization_id)

        recent_success_rate = await self.db.fetchval("""
            SELECT
                COALESCE(
                    COUNT(*) FILTER (WHERE was_successful = TRUE)::FLOAT /
                    NULLIF(COUNT(*), 0),
                    0
                )
            FROM task_routing_history
            WHERE organization_id = $1
            AND created_at > NOW() - INTERVAL '24 hours'
            AND was_successful IS NOT NULL
        """, organization_id)

        # Most active agents
        top_agents = await self.db.fetch("""
            SELECT
                name,
                type,
                total_tasks_completed,
                success_rate,
                last_active_at
            FROM fractal_agents
            WHERE organization_id = $1
            AND enabled = TRUE
            ORDER BY total_tasks_completed DESC
            LIMIT 5
        """, organization_id)

        return {
            'organization_id': organization_id,
            'agents': {
                'by_type': [dict(row) for row in agent_stats],
                'total': sum(row['count'] for row in agent_stats),
                'top_performers': [dict(row) for row in top_agents]
            },
            'connectors': {
                'total': total_connectors
            },
            'collective_memory': {
                'total_entries': memory_stats['total_entries'],
                'successful_entries': memory_stats['successful_entries'],
                'success_rate': (
                    memory_stats['successful_entries'] / memory_stats['total_entries']
                    if memory_stats['total_entries'] > 0 else 0
                ),
                'avg_confidence': float(memory_stats['avg_confidence'] or 0),
                'avg_execution_time_ms': int(memory_stats['avg_execution_time'] or 0)
            },
            'recent_activity': {
                'tasks_24h': recent_tasks,
                'success_rate_24h': float(recent_success_rate or 0)
            },
            'status': 'healthy' if recent_success_rate > 0.7 else 'degraded',
            'timestamp': datetime.now().isoformat()
        }

    async def query_memory(
        self,
        organization_id: str,
        task_type: Optional[str] = None,
        task_category: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: int = 10
    ) -> List[Dict]:
        """
        Query collective memory

        Args:
            organization_id: Organization ID
            task_type: Optional task type filter
            task_category: Optional category filter
            min_confidence: Minimum confidence score
            limit: Max results

        Returns:
            List of memory entries
        """
        query = """
            SELECT
                m.*,
                a.name as primary_agent_name
            FROM agent_collective_memory m
            LEFT JOIN fractal_agents a ON m.primary_agent_id = a.id
            WHERE m.organization_id = $1
            AND m.confidence_score >= $2
        """

        params = [organization_id, min_confidence]
        param_count = 2

        if task_type:
            param_count += 1
            query += f" AND m.task_type = ${param_count}"
            params.append(task_type)

        if task_category:
            param_count += 1
            query += f" AND m.task_category = ${param_count}"
            params.append(task_category)

        query += f" ORDER BY m.confidence_score DESC, m.created_at DESC LIMIT ${param_count + 1}"
        params.append(limit)

        results = await self.db.fetch(query, *params)
        return results

    async def get_routing_history(
        self,
        organization_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """Get recent routing history"""
        history = await self.db.fetch("""
            SELECT
                r.*,
                ra.name as router_agent_name,
                aa.name as assigned_agent_name
            FROM task_routing_history r
            LEFT JOIN fractal_agents ra ON r.router_agent_id = ra.id
            LEFT JOIN fractal_agents aa ON r.assigned_to_agent_id = aa.id
            WHERE r.organization_id = $1
            ORDER BY r.created_at DESC
            LIMIT $2
        """, organization_id, limit)

        return history

    def _generate_system_prompt(
        self,
        name: str,
        skills: List[str],
        agent_type: str
    ) -> str:
        """Generate default system prompt for agent"""
        prompt = f"""You are {name}, a {agent_type} agent in a fractal agent network.

Your specialized skills: {', '.join(skills)}

Your role:
- Use your skills to handle tasks assigned to you
- Provide clear, accurate, and well-structured responses
- Collaborate with other agents when needed
- Learn from each interaction to improve performance

When you receive a task:
1. Assess if you have the required skills
2. If yes, execute it using your expertise
3. If no, or if task is too complex, delegate or request decomposition
4. Always provide detailed explanations of your approach

Focus on quality and accuracy in your responses."""

        return prompt

    async def update_agent(
        self,
        agent_id: str,
        **kwargs
    ):
        """
        Update agent properties

        Allowed kwargs: name, description, skills, system_prompt, model, temperature, max_tokens, trust_level
        """
        allowed_fields = [
            'name', 'description', 'skills', 'system_prompt', 'model',
            'temperature', 'max_tokens', 'trust_level', 'enabled'
        ]

        updates = []
        values = []
        param_count = 1

        for field, value in kwargs.items():
            if field in allowed_fields:
                param_count += 1
                updates.append(f"{field} = ${param_count}")
                values.append(value)

        if not updates:
            return

        # Add agent_id as first param
        values.insert(0, agent_id)
        updates.append(f"updated_at = NOW()")

        query = f"""
            UPDATE fractal_agents
            SET {', '.join(updates)}
            WHERE id = $1
        """

        await self.db.execute(query, *values)

        logger.info(f"Updated agent {agent_id}: {list(kwargs.keys())}")
