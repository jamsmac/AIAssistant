"""
Connector Management for FractalAgents
Manages relationships and routing between agents
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConnectorManager:
    """
    Manages connections between fractal agents
    Handles connector creation, strength/trust updates, and routing logic
    """

    def __init__(self, db, organization_id: str = 'default'):
        """
        Initialize connector manager

        Args:
            db: Database connection (PostgresDB instance)
            organization_id: Organization identifier
        """
        self.db = db
        self.organization_id = organization_id

    async def create_connector(
        self,
        from_agent_id: str,
        to_agent_id: str,
        connector_type: str = 'peer',
        strength: float = 0.5,
        trust: float = 0.5,
        routing_rules: Optional[Dict[str, Any]] = None,
        priority: int = 0
    ) -> str:
        """
        Create a connector between two agents

        Args:
            from_agent_id: Source agent UUID
            to_agent_id: Target agent UUID
            connector_type: Type (parent_child, peer, specialist, fallback)
            strength: Connection strength (0-1)
            trust: Trust level (0-1)
            routing_rules: Optional routing conditions
            priority: Priority (higher = tried first)

        Returns:
            connector_id: UUID of created connector
        """
        # Validate agents exist
        from_agent = await self.db.fetchval(
            "SELECT id FROM fractal_agents WHERE id = $1",
            from_agent_id
        )
        to_agent = await self.db.fetchval(
            "SELECT id FROM fractal_agents WHERE id = $1",
            to_agent_id
        )

        if not from_agent:
            raise ValueError(f"From agent {from_agent_id} not found")
        if not to_agent:
            raise ValueError(f"To agent {to_agent_id} not found")

        # Create connector
        connector_id = await self.db.fetchval("""
            INSERT INTO agent_connectors (
                from_agent_id,
                to_agent_id,
                connector_type,
                strength,
                trust,
                routing_rules,
                priority
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (from_agent_id, to_agent_id, connector_type) DO UPDATE
                SET strength = EXCLUDED.strength,
                    trust = EXCLUDED.trust,
                    routing_rules = EXCLUDED.routing_rules,
                    priority = EXCLUDED.priority,
                    updated_at = NOW()
            RETURNING id
        """, from_agent_id, to_agent_id, connector_type, strength, trust,
            routing_rules or {}, priority)

        logger.info(f"Created connector: {from_agent_id} -> {to_agent_id} ({connector_type})")
        return str(connector_id)

    async def get_connectors_from_agent(
        self,
        agent_id: str,
        connector_type: Optional[str] = None,
        is_active: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all connectors originating from an agent

        Args:
            agent_id: Source agent UUID
            connector_type: Filter by type (optional)
            is_active: Only active connectors

        Returns:
            List of connectors with target agent info
        """
        query = """
            SELECT
                c.*,
                a.name as to_agent_name,
                a.agent_type as to_agent_type,
                a.skills as to_agent_skills,
                a.avg_confidence_score as to_agent_confidence
            FROM agent_connectors c
            JOIN fractal_agents a ON c.to_agent_id = a.id
            WHERE c.from_agent_id = $1
        """

        params = [agent_id]
        param_count = 1

        if is_active:
            query += " AND c.is_active = true AND a.is_active = true"

        if connector_type:
            param_count += 1
            query += f" AND c.connector_type = ${param_count}"
            params.append(connector_type)

        query += " ORDER BY c.priority DESC, c.strength DESC"

        connectors = await self.db.fetch(query, *params)
        return [dict(c) for c in connectors]

    async def get_best_connector(
        self,
        from_agent_id: str,
        required_skills: List[str],
        task_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find the best connector for routing a task

        Args:
            from_agent_id: Source agent UUID
            required_skills: Skills needed for the task
            task_context: Additional context for routing decisions

        Returns:
            Best connector or None
        """
        # Get all active connectors
        connectors = await self.get_connectors_from_agent(from_agent_id)

        if not connectors:
            return None

        # Score each connector
        scored = []
        for conn in connectors:
            score = await self._calculate_connector_score(
                conn,
                required_skills,
                task_context
            )
            scored.append({
                'connector': conn,
                'score': score
            })

        # Sort by score
        scored.sort(key=lambda x: x['score'], reverse=True)

        if scored and scored[0]['score'] > 0:
            return scored[0]['connector']

        return None

    async def _calculate_connector_score(
        self,
        connector: Dict[str, Any],
        required_skills: List[str],
        task_context: Optional[Dict[str, Any]]
    ) -> float:
        """
        Calculate routing score for a connector

        Score components:
        - Skill match (40%)
        - Trust level (20%)
        - Connection strength (15%)
        - Success rate (15%)
        - Priority (10%)
        """
        score = 0.0

        # Skill match score
        if required_skills and connector['to_agent_skills']:
            matching_skills = set(required_skills) & set(connector['to_agent_skills'])
            skill_score = len(matching_skills) / max(len(required_skills), 1)
            score += skill_score * 0.4

        # Trust score
        score += connector['trust'] * 0.2

        # Strength score
        score += connector['strength'] * 0.15

        # Success rate score
        if connector['times_used'] > 0:
            success_rate = connector['successful_routes'] / connector['times_used']
            score += success_rate * 0.15

        # Priority score (normalize 0-10 to 0-1)
        priority_score = min(connector['priority'] / 10.0, 1.0)
        score += priority_score * 0.10

        # Check routing rules
        if connector['routing_rules'] and task_context:
            if not self._check_routing_rules(connector['routing_rules'], task_context):
                score *= 0.5  # Penalize if rules don't match

        return score

    def _check_routing_rules(
        self,
        rules: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """
        Check if routing rules match the task context

        Rules can include:
        - task_type: Required task type
        - min_complexity: Minimum complexity score
        - max_complexity: Maximum complexity score
        - required_skills: Skills that must be present
        """
        if not rules:
            return True

        # Check task type
        if 'task_type' in rules:
            if context.get('task_type') != rules['task_type']:
                return False

        # Check complexity range
        if 'min_complexity' in rules:
            if context.get('complexity_score', 0) < rules['min_complexity']:
                return False

        if 'max_complexity' in rules:
            if context.get('complexity_score', 10) > rules['max_complexity']:
                return False

        # Check required skills
        if 'required_skills' in rules:
            context_skills = set(context.get('required_skills', []))
            rule_skills = set(rules['required_skills'])
            if not rule_skills.issubset(context_skills):
                return False

        return True

    async def update_connector_metrics(
        self,
        connector_id: str,
        success: bool,
        satisfaction_score: Optional[float] = None
    ):
        """
        Update connector metrics after use

        Args:
            connector_id: Connector UUID
            success: Whether the routing was successful
            satisfaction_score: Optional quality score (0-1)
        """
        await self.db.execute("""
            SELECT update_connector_metrics($1, $2, $3)
        """, connector_id, success, satisfaction_score)

        logger.debug(f"Updated connector {connector_id} metrics")

    async def adjust_connector_strength(
        self,
        connector_id: str,
        adjustment: float
    ):
        """
        Adjust connector strength based on performance

        Args:
            connector_id: Connector UUID
            adjustment: Amount to adjust (-1.0 to 1.0)
        """
        await self.db.execute("""
            UPDATE agent_connectors
            SET
                strength = GREATEST(0, LEAST(1, strength + $2)),
                updated_at = NOW()
            WHERE id = $1
        """, connector_id, adjustment)

    async def adjust_connector_trust(
        self,
        connector_id: str,
        adjustment: float
    ):
        """
        Adjust connector trust based on performance

        Args:
            connector_id: Connector UUID
            adjustment: Amount to adjust (-1.0 to 1.0)
        """
        await self.db.execute("""
            UPDATE agent_connectors
            SET
                trust = GREATEST(0, LEAST(1, trust + $2)),
                updated_at = NOW()
            WHERE id = $1
        """, connector_id, adjustment)

    async def auto_tune_connectors(
        self,
        from_agent_id: str,
        learning_rate: float = 0.1
    ) -> int:
        """
        Auto-tune connector strengths based on performance

        Args:
            from_agent_id: Source agent UUID
            learning_rate: How quickly to adjust (0-1)

        Returns:
            Number of connectors adjusted
        """
        connectors = await self.get_connectors_from_agent(from_agent_id)

        adjusted = 0
        for conn in connectors:
            if conn['times_used'] < 5:
                continue  # Need minimum data

            # Calculate success rate
            success_rate = 0
            if conn['times_used'] > 0:
                success_rate = conn['successful_routes'] / conn['times_used']

            # Adjust strength based on performance
            target_strength = success_rate
            current_strength = conn['strength']
            adjustment = (target_strength - current_strength) * learning_rate

            if abs(adjustment) > 0.01:  # Only adjust if significant
                await self.adjust_connector_strength(str(conn['id']), adjustment)
                adjusted += 1

            # Adjust trust based on consistency
            if conn['avg_satisfaction_score']:
                target_trust = conn['avg_satisfaction_score']
                current_trust = conn['trust']
                trust_adjustment = (target_trust - current_trust) * learning_rate

                if abs(trust_adjustment) > 0.01:
                    await self.adjust_connector_trust(str(conn['id']), trust_adjustment)

        logger.info(f"Auto-tuned {adjusted} connectors for agent {from_agent_id}")
        return adjusted

    async def get_connector_statistics(
        self,
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get connector statistics

        Args:
            agent_id: Filter by agent (optional)

        Returns:
            Connector statistics
        """
        if agent_id:
            stats = await self.db.fetchrow("""
                SELECT
                    COUNT(*) as total_connectors,
                    AVG(strength) as avg_strength,
                    AVG(trust) as avg_trust,
                    SUM(times_used) as total_uses,
                    AVG(CASE WHEN times_used > 0
                        THEN successful_routes::FLOAT / times_used
                        ELSE 0 END) as avg_success_rate
                FROM agent_connectors
                WHERE from_agent_id = $1
                  AND is_active = true
            """, agent_id)

            connectors_by_type = await self.db.fetch("""
                SELECT
                    connector_type,
                    COUNT(*) as count,
                    AVG(strength) as avg_strength
                FROM agent_connectors
                WHERE from_agent_id = $1
                  AND is_active = true
                GROUP BY connector_type
            """, agent_id)
        else:
            stats = await self.db.fetchrow("""
                SELECT
                    COUNT(*) as total_connectors,
                    AVG(strength) as avg_strength,
                    AVG(trust) as avg_trust,
                    SUM(times_used) as total_uses,
                    AVG(CASE WHEN times_used > 0
                        THEN successful_routes::FLOAT / times_used
                        ELSE 0 END) as avg_success_rate
                FROM agent_connectors
                WHERE is_active = true
            """)

            connectors_by_type = await self.db.fetch("""
                SELECT
                    connector_type,
                    COUNT(*) as count,
                    AVG(strength) as avg_strength
                FROM agent_connectors
                WHERE is_active = true
                GROUP BY connector_type
            """)

        return {
            'total_connectors': stats['total_connectors'],
            'avg_strength': round(stats['avg_strength'] or 0, 2),
            'avg_trust': round(stats['avg_trust'] or 0, 2),
            'total_uses': stats['total_uses'],
            'avg_success_rate': round((stats['avg_success_rate'] or 0) * 100, 2),
            'by_type': [
                {
                    'type': c['connector_type'],
                    'count': c['count'],
                    'avg_strength': round(c['avg_strength'], 2)
                }
                for c in connectors_by_type
            ]
        }

    async def delete_connector(self, connector_id: str):
        """
        Delete a connector

        Args:
            connector_id: Connector UUID
        """
        await self.db.execute("""
            DELETE FROM agent_connectors WHERE id = $1
        """, connector_id)

        logger.info(f"Deleted connector: {connector_id}")

    async def deactivate_connector(self, connector_id: str):
        """
        Deactivate a connector without deleting

        Args:
            connector_id: Connector UUID
        """
        await self.db.execute("""
            UPDATE agent_connectors
            SET is_active = false, updated_at = NOW()
            WHERE id = $1
        """, connector_id)


# Export
__all__ = ['ConnectorManager']
