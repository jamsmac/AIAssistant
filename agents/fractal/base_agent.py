"""
FractalAgent - Base class for self-organizing agents
Each agent can:
- Know its skills and competencies
- Know connections to other agents
- Access collective memory
- Spawn sub-agents
- Route tasks dynamically
"""
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import json
import anthropic

logger = logging.getLogger(__name__)


class FractalAgent:
    """
    Base class for fractal agent

    Each agent is a mini-copy of the entire system with:
    - Skills and competencies
    - Connections to other agents
    - Access to collective memory
    - Ability to spawn sub-agents
    - Dynamic task routing
    """

    def __init__(
        self,
        agent_id: str,
        db,  # PostgresDB instance
        anthropic_api_key: Optional[str] = None
    ):
        self.agent_id = agent_id
        self.db = db

        # Initialize Anthropic client
        if anthropic_api_key:
            self.anthropic = anthropic.Anthropic(api_key=anthropic_api_key)
        else:
            import os
            self.anthropic = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

        # Agent data (loaded from DB)
        self.data: Optional[Dict] = None
        self.skills: List[str] = []
        self.connectors: List[Dict] = []
        self.sub_agents: List[Dict] = []

        self._initialized = False

    async def initialize(self):
        """Load agent data from database"""
        if self._initialized:
            return

        try:
            # Get agent info
            self.data = await self.db.fetchrow("""
                SELECT * FROM fractal_agents WHERE id = $1
            """, self.agent_id)

            if not self.data:
                raise ValueError(f"Agent {self.agent_id} not found")

            self.skills = self.data.get('skills', [])

            # Load connectors (outgoing connections)
            self.connectors = await self.db.fetch("""
                SELECT
                    c.*,
                    a.name as to_agent_name,
                    a.skills as to_agent_skills,
                    a.success_rate as to_agent_success_rate
                FROM agent_connectors c
                LEFT JOIN fractal_agents a ON c.to_agent_id = a.id
                WHERE c.from_agent_id = $1
                AND c.enabled = TRUE
                AND a.enabled = TRUE
                ORDER BY c.strength DESC, c.trust DESC
            """, self.agent_id)

            # Load sub-agents
            self.sub_agents = await self.db.fetch("""
                SELECT * FROM fractal_agents
                WHERE parent_agent_id = $1
                AND enabled = TRUE
            """, self.agent_id)

            self._initialized = True

            logger.info(
                f"Agent {self.data['name']} initialized: "
                f"{len(self.skills)} skills, "
                f"{len(self.connectors)} connections, "
                f"{len(self.sub_agents)} sub-agents"
            )

        except Exception as e:
            logger.error(f"Failed to initialize agent {self.agent_id}: {e}")
            raise

    async def can_handle(self, task: Dict) -> Tuple[bool, float]:
        """
        Determine if this agent can handle the task

        Args:
            task: Task dictionary with 'required_skills', 'description', etc.

        Returns:
            (can_handle: bool, confidence: float)
        """
        if not self._initialized:
            await self.initialize()

        required_skills = task.get('required_skills', [])

        if not required_skills:
            # No specific skills required, base on description
            return True, 0.5

        # Check if agent has required skills
        matching_skills = set(self.skills) & set(required_skills)

        if not matching_skills:
            return False, 0.0

        # Calculate confidence based on:
        # - Skills match percentage
        # - Past performance (success_rate)
        # - Agent trust level

        skills_match_ratio = len(matching_skills) / len(required_skills)
        performance_score = self.data.get('success_rate', 0.5)
        trust_score = self.data.get('trust_level', 0.5)

        # Weighted combination
        confidence = (
            skills_match_ratio * 0.5 +
            performance_score * 0.3 +
            trust_score * 0.2
        )

        can_handle = confidence >= 0.3  # Minimum threshold

        return can_handle, confidence

    async def route_task(self, task: Dict) -> Tuple[str, float]:
        """
        Route task to best agent (self or connected agent)

        Returns:
            (agent_id, confidence)
        """
        if not self._initialized:
            await self.initialize()

        # Check if I can handle it
        can_handle, my_confidence = await self.can_handle(task)

        best_agent_id = self.agent_id
        best_confidence = my_confidence if can_handle else 0.0
        best_agent_name = self.data['name']

        # Check connected agents
        candidates = []

        for connector in self.connectors:
            connected_agent_id = connector['to_agent_id']

            # Create temporary agent instance to check capability
            connected_agent = FractalAgent(
                connected_agent_id,
                self.db,
                None  # Reuse same anthropic client
            )
            connected_agent.anthropic = self.anthropic

            await connected_agent.initialize()

            can_handle_conn, confidence = await connected_agent.can_handle(task)

            # Adjust confidence by connector strength and trust
            adjusted_confidence = confidence * connector['strength'] * connector['trust']

            if can_handle_conn:
                candidates.append({
                    'agent_id': connected_agent_id,
                    'agent_name': connector['to_agent_name'],
                    'confidence': adjusted_confidence,
                    'original_confidence': confidence
                })

                if adjusted_confidence > best_confidence:
                    best_agent_id = connected_agent_id
                    best_confidence = adjusted_confidence
                    best_agent_name = connector['to_agent_name']

        # Log routing decision
        await self._log_routing_decision(
            task=task,
            chosen_agent_id=best_agent_id,
            chosen_agent_name=best_agent_name,
            confidence=best_confidence,
            alternatives=candidates
        )

        logger.info(
            f"Task routed: {best_agent_name} "
            f"(confidence: {best_confidence:.2f})"
        )

        return best_agent_id, best_confidence

    async def execute_task(self, task: Dict) -> Dict:
        """
        Execute task or delegate to sub-agents

        Args:
            task: Task dictionary

        Returns:
            Result dictionary
        """
        if not self._initialized:
            await self.initialize()

        logger.info(f"Agent {self.data['name']} executing task: {task.get('description', '')[:100]}")

        start_time = datetime.now()

        try:
            # Route task to best agent
            best_agent_id, confidence = await self.route_task(task)

            if best_agent_id != self.agent_id:
                # Delegate to another agent
                logger.info(f"Delegating task to agent {best_agent_id}")

                delegated_agent = FractalAgent(
                    best_agent_id,
                    self.db,
                    None
                )
                delegated_agent.anthropic = self.anthropic

                result = await delegated_agent.execute_task(task)

                # Track delegation
                await self._track_delegation(best_agent_id, success=result['success'])

                return result

            # I will handle this task
            # Check if task needs decomposition
            if self._is_complex_task(task):
                result = await self._execute_hierarchical(task)
            else:
                result = await self._execute_direct(task)

            # Calculate execution time
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            result['execution_time'] = execution_time

            # Update performance metrics
            await self._update_metrics(
                success=result['success'],
                execution_time=execution_time
            )

            return result

        except Exception as e:
            logger.error(f"Task execution failed: {e}")

            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            await self._update_metrics(
                success=False,
                execution_time=execution_time
            )

            return {
                'task_id': task.get('id'),
                'agent_id': self.agent_id,
                'agent_name': self.data['name'],
                'success': False,
                'error': str(e),
                'execution_time': execution_time
            }

    async def _execute_hierarchical(self, task: Dict) -> Dict:
        """
        Break task into sub-tasks and coordinate execution
        """
        logger.info(f"Decomposing complex task...")

        # Decompose task into sub-tasks
        sub_tasks = await self._decompose_task(task)

        logger.info(f"Task decomposed into {len(sub_tasks)} sub-tasks")

        results = []

        for i, sub_task in enumerate(sub_tasks, 1):
            logger.info(f"Executing sub-task {i}/{len(sub_tasks)}")

            # Add metadata
            sub_task['id'] = f"{task.get('id', 'task')}_sub_{i}"
            sub_task['organization_id'] = task.get('organization_id')

            # Find best sub-agent or execute ourselves
            best_agent_id, confidence = await self.route_task(sub_task)

            if best_agent_id == self.agent_id:
                # Execute directly
                result = await self._execute_direct(sub_task)
            else:
                # Delegate
                sub_agent = FractalAgent(best_agent_id, self.db, None)
                sub_agent.anthropic = self.anthropic
                result = await sub_agent.execute_task(sub_task)

            results.append(result)

        # Aggregate results
        final_result = await self._aggregate_results(task, results)

        # Store in collective memory
        await self._store_in_memory(task, final_result, participating_agents=[
            r.get('agent_id') for r in results if r.get('agent_id')
        ])

        return final_result

    async def _execute_direct(self, task: Dict) -> Dict:
        """
        Execute task directly using LLM
        """
        # Check collective memory for similar tasks
        similar_solutions = await self._query_memory(task)

        # Build context
        context = self._build_context(task, similar_solutions)

        logger.info(f"Calling LLM (model: {self.data['model']})")

        try:
            # Call LLM
            response = self.anthropic.messages.create(
                model=self.data.get('model', 'claude-sonnet-4-20250514'),
                max_tokens=self.data.get('max_tokens', 4096),
                temperature=self.data.get('temperature', 0.7),
                system=self.data.get('system_prompt', ''),
                messages=[{
                    "role": "user",
                    "content": context
                }]
            )

            response_text = response.content[0].text

            result = {
                'task_id': task.get('id'),
                'agent_id': self.agent_id,
                'agent_name': self.data['name'],
                'response': response_text,
                'success': True,
                'tokens_used': response.usage.total_tokens,
                'model': self.data['model']
            }

            # Store in memory
            await self._store_in_memory(task, result)

            return result

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    async def _decompose_task(self, task: Dict) -> List[Dict]:
        """
        Use LLM to decompose complex task into sub-tasks
        """
        prompt = f"""
You are a task decomposition expert. Break down this complex task into smaller, manageable sub-tasks.

TASK:
{task.get('description', '')}

REQUIRED SKILLS:
{', '.join(task.get('required_skills', []))}

Return a JSON array of sub-tasks. Each sub-task should have:
- description: Clear description of the sub-task
- required_skills: Array of skills needed
- dependencies: Array of sub-task indices this depends on (0-indexed)

Format:
[
    {{
        "description": "...",
        "required_skills": ["..."],
        "dependencies": []
    }},
    ...
]

Return ONLY the JSON array, no other text.
"""

        response = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text.strip()

        # Extract JSON from response
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0].strip()

        sub_tasks = json.loads(response_text)

        return sub_tasks

    async def _query_memory(self, task: Dict) -> List[Dict]:
        """
        Query collective memory for similar past solutions
        """
        task_type = task.get('type', 'general')

        similar = await self.db.fetch("""
            SELECT *
            FROM agent_collective_memory
            WHERE task_type = $1
            AND success = TRUE
            AND organization_id = $2
            ORDER BY confidence_score DESC, created_at DESC
            LIMIT 5
        """, task_type, task.get('organization_id'))

        return similar

    async def _store_in_memory(
        self,
        task: Dict,
        result: Dict,
        participating_agents: Optional[List[str]] = None
    ):
        """
        Store task execution in collective memory
        """
        if participating_agents is None:
            participating_agents = [self.agent_id]

        try:
            await self.db.execute("""
                INSERT INTO agent_collective_memory (
                    organization_id,
                    task_type,
                    task_category,
                    input_context,
                    solution_approach,
                    solution_summary,
                    participating_agents,
                    primary_agent_id,
                    success,
                    execution_time,
                    confidence_score
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
            task.get('organization_id'),
            task.get('type', 'general'),
            task.get('category'),
            task.get('description', '')[:5000],  # Limit length
            result.get('response', '')[:5000],
            result.get('response', '')[:500],
            participating_agents,
            self.agent_id,
            result.get('success', False),
            result.get('execution_time', 0),
            result.get('confidence', 0.8)
            )

            logger.debug("Task stored in collective memory")

        except Exception as e:
            logger.warning(f"Failed to store in memory: {e}")

    async def _update_metrics(self, success: bool, execution_time: int):
        """Update agent performance metrics"""
        try:
            # Note: success_rate is auto-updated by trigger
            await self.db.execute("""
                UPDATE fractal_agents
                SET
                    last_active_at = NOW(),
                    updated_at = NOW(),
                    avg_response_time = CASE
                        WHEN avg_response_time IS NULL THEN $2
                        ELSE (avg_response_time * 0.9 + $2 * 0.1)::INTEGER
                    END
                WHERE id = $1
            """, self.agent_id, execution_time)

        except Exception as e:
            logger.warning(f"Failed to update metrics: {e}")

    async def _track_delegation(self, delegated_to: str, success: bool):
        """Track delegation to another agent"""
        try:
            await self.db.execute("""
                UPDATE agent_connectors
                SET
                    total_interactions = total_interactions + 1,
                    successful_handoffs = successful_handoffs + CASE WHEN $3 THEN 1 ELSE 0 END,
                    failed_handoffs = failed_handoffs + CASE WHEN NOT $3 THEN 1 ELSE 0 END,
                    last_interaction_at = NOW()
                WHERE from_agent_id = $1 AND to_agent_id = $2
            """, self.agent_id, delegated_to, success)

        except Exception as e:
            logger.warning(f"Failed to track delegation: {e}")

    async def _log_routing_decision(
        self,
        task: Dict,
        chosen_agent_id: str,
        chosen_agent_name: str,
        confidence: float,
        alternatives: List[Dict]
    ):
        """Log routing decision for analysis"""
        try:
            await self.db.execute("""
                INSERT INTO task_routing_history (
                    organization_id,
                    task_id,
                    task_description,
                    task_type,
                    required_skills,
                    router_agent_id,
                    assigned_to_agent_id,
                    routing_reason,
                    routing_confidence,
                    alternatives
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            task.get('organization_id'),
            task.get('id'),
            task.get('description', '')[:1000],
            task.get('type'),
            task.get('required_skills', []),
            self.agent_id,
            chosen_agent_id,
            f"Routed by {self.data['name']} to {chosen_agent_name}",
            confidence,
            json.dumps(alternatives)
            )

        except Exception as e:
            logger.warning(f"Failed to log routing: {e}")

    def _is_complex_task(self, task: Dict) -> bool:
        """Determine if task needs decomposition"""
        description_length = len(task.get('description', ''))
        num_requirements = len(task.get('required_skills', []))

        # Simple heuristic
        is_complex = description_length > 500 or num_requirements > 3

        # Could also check task.get('complexity_score') if provided
        if task.get('complexity_score', 0) > 7:
            is_complex = True

        return is_complex

    def _build_context(
        self,
        task: Dict,
        similar_solutions: List[Dict]
    ) -> str:
        """Build context for LLM"""
        context = f"TASK: {task.get('description', '')}\n\n"

        if task.get('required_skills'):
            context += f"REQUIRED SKILLS: {', '.join(task['required_skills'])}\n\n"

        if similar_solutions:
            context += "SIMILAR PAST SOLUTIONS:\n"
            for i, sol in enumerate(similar_solutions, 1):
                context += f"{i}. {sol['solution_summary'][:200]}...\n"
            context += "\n"

        context += "Please complete this task providing a detailed solution."

        return context

    async def _aggregate_results(self, task: Dict, results: List[Dict]) -> Dict:
        """Aggregate results from sub-tasks"""
        successful_results = [r for r in results if r.get('success')]

        # Combine all responses
        combined_response = "\n\n".join([
            f"Sub-task {i+1}: {r.get('response', '')}"
            for i, r in enumerate(successful_results)
        ])

        total_tokens = sum(r.get('tokens_used', 0) for r in results)
        total_time = sum(r.get('execution_time', 0) for r in results)

        return {
            'task_id': task.get('id'),
            'agent_id': self.agent_id,
            'agent_name': self.data['name'],
            'response': combined_response,
            'success': len(successful_results) > 0,
            'sub_results': results,
            'total_sub_tasks': len(results),
            'successful_sub_tasks': len(successful_results),
            'tokens_used': total_tokens,
            'execution_time': total_time
        }
