"""
Collective Memory System for FractalAgents
Shared learning and experience across the agent network
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import logging

logger = logging.getLogger(__name__)


class CollectiveMemory:
    """
    Manages collective memory for the fractal agent system
    Stores task executions, learnings, and enables similarity-based retrieval
    """

    def __init__(self, db, organization_id: str = 'default'):
        """
        Initialize collective memory

        Args:
            db: Database connection (PostgresDB instance)
            organization_id: Organization identifier for multi-tenancy
        """
        self.db = db
        self.organization_id = organization_id

    async def store_task_execution(
        self,
        task_description: str,
        task_type: str,
        required_skills: List[str],
        agent_id: str,
        agent_name: str,
        success: bool,
        confidence_score: float,
        execution_time_ms: int,
        tokens_used: int = 0,
        cost: float = 0.0,
        result_summary: Optional[str] = None,
        learnings: Optional[Dict[str, Any]] = None,
        errors: Optional[List[str]] = None,
        improvements: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        complexity_score: int = 5
    ) -> str:
        """
        Store a task execution in collective memory

        Returns:
            memory_id: UUID of the stored memory entry
        """
        # Calculate input hash for similarity matching
        input_hash = self._calculate_input_hash(task_description, required_skills)

        # Store in database
        memory_id = await self.db.fetchval("""
            INSERT INTO agent_collective_memory (
                organization_id,
                task_description,
                task_type,
                required_skills,
                complexity_score,
                agent_id,
                agent_name,
                success,
                confidence_score,
                execution_time_ms,
                tokens_used,
                cost,
                result_summary,
                learnings,
                errors_encountered,
                improvements_suggested,
                context,
                input_hash
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                $11, $12, $13, $14, $15, $16, $17, $18
            ) RETURNING id
        """,
            self.organization_id,
            task_description,
            task_type,
            required_skills,
            complexity_score,
            agent_id,
            agent_name,
            success,
            confidence_score,
            execution_time_ms,
            tokens_used,
            cost,
            result_summary,
            learnings,
            errors or [],
            improvements or [],
            context or {},
            input_hash
        )

        logger.info(f"Stored task execution in collective memory: {memory_id}")
        return str(memory_id)

    async def find_similar_tasks(
        self,
        task_description: str,
        required_skills: List[str],
        limit: int = 5,
        min_similarity: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Find similar tasks from collective memory

        Args:
            task_description: Description of the task to match
            required_skills: Skills required for the task
            limit: Maximum number of results to return
            min_similarity: Minimum similarity score (0-1)

        Returns:
            List of similar task executions with similarity scores
        """
        # Calculate input hash
        input_hash = self._calculate_input_hash(task_description, required_skills)

        # First try exact hash match (fastest)
        exact_matches = await self.db.fetch("""
            SELECT
                id,
                task_description,
                agent_name,
                success,
                confidence_score,
                execution_time_ms,
                learnings,
                result_summary,
                1.0 as similarity_score
            FROM agent_collective_memory
            WHERE organization_id = $1
              AND input_hash = $2
              AND success = true
            ORDER BY created_at DESC
            LIMIT $3
        """, self.organization_id, input_hash, limit)

        if exact_matches:
            return [dict(m) for m in exact_matches]

        # Use database function for similarity search
        similar = await self.db.fetch("""
            SELECT * FROM find_similar_tasks($1, $2, $3)
            WHERE similarity_score >= $4
        """, task_description, required_skills, limit, min_similarity)

        return [dict(s) for s in similar]

    async def get_agent_learnings(
        self,
        agent_id: str,
        task_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get learnings from a specific agent's past executions

        Returns:
            List of learning entries
        """
        if task_type:
            results = await self.db.fetch("""
                SELECT
                    task_description,
                    task_type,
                    success,
                    learnings,
                    improvements_suggested,
                    created_at
                FROM agent_collective_memory
                WHERE organization_id = $1
                  AND agent_id = $2
                  AND task_type = $3
                  AND learnings IS NOT NULL
                ORDER BY created_at DESC
                LIMIT $4
            """, self.organization_id, agent_id, task_type, limit)
        else:
            results = await self.db.fetch("""
                SELECT
                    task_description,
                    task_type,
                    success,
                    learnings,
                    improvements_suggested,
                    created_at
                FROM agent_collective_memory
                WHERE organization_id = $1
                  AND agent_id = $2
                  AND learnings IS NOT NULL
                ORDER BY created_at DESC
                LIMIT $3
            """, self.organization_id, agent_id, limit)

        return [dict(r) for r in results]

    async def get_success_patterns(
        self,
        task_type: str,
        required_skills: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze success patterns for a task type

        Returns:
            {
                'success_rate': float,
                'avg_confidence': float,
                'best_agents': [str],
                'common_approaches': [str],
                'failure_reasons': [str]
            }
        """
        # Get statistics
        stats = await self.db.fetchrow("""
            SELECT
                COUNT(*) as total_attempts,
                COUNT(*) FILTER (WHERE success = true) as successful,
                AVG(confidence_score) FILTER (WHERE success = true) as avg_confidence,
                AVG(execution_time_ms) FILTER (WHERE success = true) as avg_time
            FROM agent_collective_memory
            WHERE organization_id = $1
              AND task_type = $2
        """, self.organization_id, task_type)

        # Find best performing agents
        best_agents = await self.db.fetch("""
            SELECT
                agent_name,
                COUNT(*) FILTER (WHERE success = true) as successful_tasks,
                AVG(confidence_score) as avg_confidence
            FROM agent_collective_memory
            WHERE organization_id = $1
              AND task_type = $2
              AND success = true
            GROUP BY agent_name
            ORDER BY successful_tasks DESC, avg_confidence DESC
            LIMIT 3
        """, self.organization_id, task_type)

        # Extract common learnings
        learnings = await self.db.fetch("""
            SELECT learnings
            FROM agent_collective_memory
            WHERE organization_id = $1
              AND task_type = $2
              AND success = true
              AND learnings IS NOT NULL
            ORDER BY confidence_score DESC
            LIMIT 10
        """, self.organization_id, task_type)

        # Extract failure reasons
        failures = await self.db.fetch("""
            SELECT errors_encountered
            FROM agent_collective_memory
            WHERE organization_id = $1
              AND task_type = $2
              AND success = false
              AND errors_encountered IS NOT NULL
              AND array_length(errors_encountered, 1) > 0
            LIMIT 10
        """, self.organization_id, task_type)

        success_rate = 0
        if stats['total_attempts'] > 0:
            success_rate = (stats['successful'] / stats['total_attempts']) * 100

        return {
            'task_type': task_type,
            'total_attempts': stats['total_attempts'],
            'success_rate': round(success_rate, 2),
            'avg_confidence': round(stats['avg_confidence'] or 0, 2),
            'avg_execution_time_ms': round(stats['avg_time'] or 0, 2),
            'best_agents': [
                {
                    'name': a['agent_name'],
                    'successful_tasks': a['successful_tasks'],
                    'avg_confidence': round(a['avg_confidence'], 2)
                }
                for a in best_agents
            ],
            'learnings': [l['learnings'] for l in learnings if l['learnings']],
            'common_errors': [
                error
                for f in failures
                if f['errors_encountered']
                for error in f['errors_encountered']
            ][:5]  # Top 5 errors
        }

    async def get_memory_statistics(self) -> Dict[str, Any]:
        """
        Get overall collective memory statistics

        Returns:
            Statistics about the collective memory
        """
        stats = await self.db.fetchrow("""
            SELECT
                COUNT(*) as total_entries,
                COUNT(*) FILTER (WHERE success = true) as successful_entries,
                AVG(confidence_score) as avg_confidence,
                AVG(execution_time_ms) as avg_execution_time,
                COUNT(DISTINCT agent_id) as unique_agents,
                COUNT(DISTINCT task_type) as unique_task_types
            FROM agent_collective_memory
            WHERE organization_id = $1
        """, self.organization_id)

        # Recent activity
        recent = await self.db.fetch("""
            SELECT
                DATE(created_at) as date,
                COUNT(*) as tasks,
                AVG(confidence_score) as avg_confidence
            FROM agent_collective_memory
            WHERE organization_id = $1
              AND created_at >= NOW() - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """, self.organization_id)

        success_rate = 0
        if stats['total_entries'] > 0:
            success_rate = (stats['successful_entries'] / stats['total_entries']) * 100

        return {
            'organization_id': self.organization_id,
            'total_entries': stats['total_entries'],
            'successful_entries': stats['successful_entries'],
            'success_rate': round(success_rate, 2),
            'avg_confidence': round(stats['avg_confidence'] or 0, 2),
            'avg_execution_time_ms': round(stats['avg_execution_time'] or 0, 2),
            'unique_agents': stats['unique_agents'],
            'unique_task_types': stats['unique_task_types'],
            'recent_activity': [
                {
                    'date': r['date'].isoformat(),
                    'tasks': r['tasks'],
                    'avg_confidence': round(r['avg_confidence'] or 0, 2)
                }
                for r in recent
            ]
        }

    def _calculate_input_hash(self, task_description: str, required_skills: List[str]) -> str:
        """
        Calculate a hash of task inputs for fast similarity matching

        Args:
            task_description: Task description
            required_skills: Required skills

        Returns:
            SHA-256 hash string
        """
        # Normalize inputs
        normalized_desc = task_description.lower().strip()
        normalized_skills = sorted([s.lower().strip() for s in required_skills])

        # Combine
        combined = f"{normalized_desc}|{'|'.join(normalized_skills)}"

        # Hash
        return hashlib.sha256(combined.encode()).hexdigest()

    async def clear_old_memories(self, days_to_keep: int = 90) -> int:
        """
        Clear old memory entries to prevent database bloat

        Args:
            days_to_keep: Number of days of memories to retain

        Returns:
            Number of entries deleted
        """
        deleted_count = await self.db.fetchval("""
            WITH deleted AS (
                DELETE FROM agent_collective_memory
                WHERE organization_id = $1
                  AND created_at < NOW() - INTERVAL '$2 days'
                  AND success = false  -- Keep successful ones longer
                RETURNING id
            )
            SELECT COUNT(*) FROM deleted
        """, self.organization_id, days_to_keep)

        logger.info(f"Cleared {deleted_count} old memory entries")
        return deleted_count


# Export
__all__ = ['CollectiveMemory']
