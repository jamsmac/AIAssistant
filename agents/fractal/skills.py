"""
Skills System for FractalAgents
Manages agent capabilities and skill-based routing
"""
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class SkillsManager:
    """
    Manages skills across the fractal agent system
    Tracks skill usage, success rates, and agent capabilities
    """

    def __init__(self, db, organization_id: str = 'default'):
        """
        Initialize skills manager

        Args:
            db: Database connection (PostgresDB instance)
            organization_id: Organization identifier
        """
        self.db = db
        self.organization_id = organization_id

    async def register_skill(
        self,
        skill_name: str,
        category: str = 'general',
        description: Optional[str] = None,
        required_capabilities: Optional[List[str]] = None,
        min_tokens: int = 1000
    ) -> str:
        """
        Register a new skill in the system

        Args:
            skill_name: Unique name of the skill
            category: Category (technical, creative, analysis, etc.)
            description: Human-readable description
            required_capabilities: Model capabilities needed
            min_tokens: Minimum token context required

        Returns:
            skill_id: UUID of the registered skill
        """
        skill_id = await self.db.fetchval("""
            INSERT INTO agent_skills (
                skill_name,
                skill_category,
                description,
                required_model_capabilities,
                min_tokens
            ) VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (skill_name) DO UPDATE
                SET description = EXCLUDED.description,
                    skill_category = EXCLUDED.skill_category,
                    updated_at = NOW()
            RETURNING id
        """, skill_name, category, description, required_capabilities or [], min_tokens)

        logger.info(f"Registered skill: {skill_name}")
        return str(skill_id)

    async def get_skill(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """
        Get skill information

        Returns:
            Skill details or None if not found
        """
        skill = await self.db.fetchrow("""
            SELECT * FROM agent_skills WHERE skill_name = $1
        """, skill_name)

        return dict(skill) if skill else None

    async def find_agents_with_skill(
        self,
        skill_name: str,
        is_active: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Find all agents that have a specific skill

        Args:
            skill_name: Name of the skill to search for
            is_active: Only return active agents

        Returns:
            List of agents with their skill-related metrics
        """
        query = """
            SELECT
                id,
                name,
                agent_type,
                skills,
                total_tasks_processed,
                successful_tasks,
                avg_confidence_score,
                trust_level
            FROM fractal_agents
            WHERE $1 = ANY(skills)
        """

        params = [skill_name]

        if is_active:
            query += " AND is_active = true"

        query += " ORDER BY successful_tasks DESC, avg_confidence_score DESC"

        agents = await self.db.fetch(query, *params)
        return [dict(a) for a in agents]

    async def get_best_agent_for_skills(
        self,
        required_skills: List[str],
        exclude_agents: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find the best agent for a set of required skills

        Args:
            required_skills: List of skills needed
            exclude_agents: Agent IDs to exclude

        Returns:
            Best matching agent or None
        """
        # Build exclusion clause
        exclude_clause = ""
        params = [required_skills]

        if exclude_agents:
            exclude_clause = f"AND id != ALL($2::UUID[])"
            params.append(exclude_agents)

        query = f"""
            WITH skill_matches AS (
                SELECT
                    id,
                    name,
                    agent_type,
                    skills,
                    total_tasks_processed,
                    successful_tasks,
                    avg_confidence_score,
                    trust_level,
                    -- Calculate skill overlap score
                    (
                        SELECT COUNT(*)
                        FROM unnest(skills) AS skill
                        WHERE skill = ANY($1)
                    )::FLOAT / GREATEST(array_length($1, 1), 1) as skill_match_score,
                    -- Calculate success rate
                    CASE
                        WHEN total_tasks_processed > 0
                        THEN (successful_tasks::FLOAT / total_tasks_processed)
                        ELSE 0
                    END as success_rate
                FROM fractal_agents
                WHERE is_active = true
                  {exclude_clause}
            )
            SELECT
                *,
                -- Combined score: skill match (60%) + success rate (20%) + confidence (10%) + trust (10%)
                (
                    skill_match_score * 0.6 +
                    success_rate * 0.2 +
                    avg_confidence_score * 0.1 +
                    trust_level * 0.1
                ) as combined_score
            FROM skill_matches
            WHERE skill_match_score > 0  -- Must have at least one matching skill
            ORDER BY combined_score DESC, total_tasks_processed DESC
            LIMIT 1
        """

        result = await self.db.fetchrow(query, *params)
        return dict(result) if result else None

    async def update_skill_metrics(
        self,
        skill_name: str,
        success: bool,
        confidence: float,
        execution_time_ms: int
    ):
        """
        Update metrics for a skill after use

        Args:
            skill_name: Name of the skill
            success: Whether the task was successful
            confidence: Confidence score (0-1)
            execution_time_ms: Execution time in milliseconds
        """
        # Check if skill exists
        skill = await self.get_skill(skill_name)
        if not skill:
            # Auto-register unknown skill
            await self.register_skill(skill_name, category='auto')

        # Update metrics
        await self.db.execute("""
            UPDATE agent_skills
            SET
                total_uses = total_uses + 1,
                success_rate = (
                    (success_rate * total_uses + CASE WHEN $2 THEN 1 ELSE 0 END) /
                    (total_uses + 1)
                ),
                avg_confidence = (
                    (avg_confidence * total_uses + $3) /
                    (total_uses + 1)
                ),
                avg_execution_time_ms = (
                    (avg_execution_time_ms * total_uses + $4) /
                    (total_uses + 1)
                ),
                updated_at = NOW()
            WHERE skill_name = $1
        """, skill_name, success, confidence, execution_time_ms)

        logger.debug(f"Updated metrics for skill: {skill_name}")

    async def get_skill_statistics(
        self,
        category: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get statistics for all skills

        Args:
            category: Filter by category (optional)
            limit: Maximum number of results

        Returns:
            List of skills with statistics
        """
        query = """
            SELECT
                skill_name,
                skill_category,
                description,
                total_uses,
                success_rate,
                avg_confidence,
                avg_execution_time_ms,
                agent_count
            FROM agent_skills
        """

        params = []
        if category:
            query += " WHERE skill_category = $1"
            params.append(category)

        query += " ORDER BY total_uses DESC, success_rate DESC LIMIT $" + str(len(params) + 1)
        params.append(limit)

        results = await self.db.fetch(query, *params)
        return [dict(r) for r in results]

    async def get_trending_skills(
        self,
        days: int = 7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get trending skills based on recent usage

        Args:
            days: Number of days to look back
            limit: Maximum results

        Returns:
            List of trending skills
        """
        results = await self.db.fetch("""
            WITH recent_usage AS (
                SELECT
                    unnest(required_skills) as skill_name,
                    COUNT(*) as recent_uses,
                    AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as recent_success_rate
                FROM agent_collective_memory
                WHERE created_at >= NOW() - INTERVAL '$1 days'
                GROUP BY skill_name
            )
            SELECT
                s.skill_name,
                s.skill_category,
                s.total_uses,
                s.success_rate as overall_success_rate,
                r.recent_uses,
                r.recent_success_rate,
                s.agent_count
            FROM agent_skills s
            JOIN recent_usage r ON s.skill_name = r.skill_name
            ORDER BY r.recent_uses DESC
            LIMIT $2
        """, days, limit)

        return [dict(r) for r in results]

    async def suggest_skills_for_task(
        self,
        task_description: str,
        task_type: Optional[str] = None
    ) -> List[str]:
        """
        Suggest relevant skills for a task based on description

        Args:
            task_description: Description of the task
            task_type: Type of task (optional)

        Returns:
            List of suggested skill names
        """
        # Simple keyword matching for now
        # In production, use ML/embedding-based matching

        task_lower = task_description.lower()

        # Keyword to skill mapping
        keyword_map = {
            'write': ['blog_writing', 'content_creation', 'copywriting'],
            'code': ['coding', 'programming', 'debugging'],
            'analyze': ['data_analysis', 'insights', 'reporting'],
            'design': ['ui_design', 'ux_design', 'visual_design'],
            'test': ['testing', 'qa', 'validation'],
            'seo': ['seo_optimization', 'keywords', 'meta_tags'],
            'social': ['social_media', 'engagement', 'community'],
            'image': ['image_generation', 'visual_content', 'graphics'],
            'edit': ['editing', 'proofreading', 'improvement'],
            'research': ['research', 'investigation', 'discovery']
        }

        suggested = set()
        for keyword, skills in keyword_map.items():
            if keyword in task_lower:
                suggested.update(skills)

        # If task_type is provided, get successful skills for that type
        if task_type and not suggested:
            past_successes = await self.db.fetch("""
                SELECT
                    unnest(required_skills) as skill,
                    COUNT(*) as uses
                FROM agent_collective_memory
                WHERE task_type = $1
                  AND success = true
                GROUP BY skill
                ORDER BY uses DESC
                LIMIT 5
            """, task_type)

            suggested.update([s['skill'] for s in past_successes])

        return list(suggested)

    async def get_skill_gaps(self) -> List[Dict[str, Any]]:
        """
        Identify skill gaps in the agent network

        Returns:
            List of underserved skills or task types
        """
        # Find task types with low success rates
        low_success = await self.db.fetch("""
            SELECT
                task_type,
                COUNT(*) as total_attempts,
                AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate,
                array_agg(DISTINCT unnest(required_skills)) as skills_used
            FROM agent_collective_memory
            WHERE created_at >= NOW() - INTERVAL '30 days'
            GROUP BY task_type
            HAVING AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) < 0.7
            ORDER BY success_rate ASC
            LIMIT 10
        """)

        # Find skills with low agent count
        low_coverage = await self.db.fetch("""
            SELECT
                skill_name,
                agent_count,
                total_uses,
                success_rate
            FROM agent_skills
            WHERE agent_count < 3
              AND total_uses > 10
            ORDER BY total_uses DESC
            LIMIT 10
        """)

        gaps = []

        for task in low_success:
            gaps.append({
                'type': 'low_success_task_type',
                'task_type': task['task_type'],
                'success_rate': round(task['success_rate'] * 100, 2),
                'attempts': task['total_attempts'],
                'recommendation': f"Improve agents for {task['task_type']} tasks or add specialists"
            })

        for skill in low_coverage:
            gaps.append({
                'type': 'low_coverage_skill',
                'skill_name': skill['skill_name'],
                'agent_count': skill['agent_count'],
                'success_rate': round(skill['success_rate'] * 100, 2),
                'recommendation': f"Add more agents with '{skill['skill_name']}' skill"
            })

        return gaps


# Export
__all__ = ['SkillsManager']
