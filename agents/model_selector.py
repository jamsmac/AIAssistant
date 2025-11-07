"""
Model Selector Module
Intelligent AI model selection based on task analysis, complexity, and credit availability
"""

import sqlite3
import re
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "history.db"


@dataclass
class TaskAnalysis:
    """Result of prompt analysis"""
    task_type: str  # coding, writing, analysis, translation, math, general
    complexity: str  # simple, medium, complex
    estimated_tokens: int
    requires_reasoning: bool
    requires_code_generation: bool
    requires_creativity: bool


@dataclass
class ModelRecommendation:
    """Recommended model with cost estimation"""
    provider: str
    model: str
    estimated_cost_credits: int
    quality_score: float
    reasoning: str
    cost_tier: str  # cheap, medium, expensive
    credits_per_1k_tokens: int


class ModelSelector:
    """Intelligent model selection based on task requirements"""

    def __init__(self, db_path: str = str(DB_PATH)):
        """Initialize model selector"""
        self.db_path = db_path

        # Task type detection patterns
        self.task_patterns = {
            'coding': [
                r'\b(code|function|class|implement|debug|refactor|optimize)\b',
                r'\b(python|javascript|java|c\+\+|rust|go|typescript)\b',
                r'\b(api|endpoint|algorithm|data structure)\b',
                r'```',  # Code blocks
            ],
            'writing': [
                r'\b(write|draft|compose|article|blog|essay|letter)\b',
                r'\b(creative|story|narrative|content|copy)\b',
                r'\b(tone|style|audience|voice)\b',
            ],
            'analysis': [
                r'\b(analyze|examine|evaluate|assess|compare|review)\b',
                r'\b(data|statistics|metrics|trends|patterns)\b',
                r'\b(insights|findings|conclusions|recommendations)\b',
            ],
            'translation': [
                r'\b(translate|translation|language)\b',
                r'\b(english|spanish|french|german|chinese|japanese|russian)\b',
            ],
            'math': [
                r'\b(calculate|solve|equation|formula|mathematics)\b',
                r'\b(algebra|calculus|geometry|statistics|probability)\b',
                r'[\d\+\-\*/\=\(\)]{10,}',  # Math expressions
            ],
        }

        # Complexity indicators
        self.complexity_indicators = {
            'simple': [
                r'\b(simple|basic|quick|easy|straightforward)\b',
                r'\b(what is|define|explain)\b',
            ],
            'complex': [
                r'\b(complex|advanced|comprehensive|detailed|thorough)\b',
                r'\b(architecture|system design|infrastructure)\b',
                r'\b(optimize|performance|scalability|security)\b',
                r'\b(multiple|various|several)\b',
            ],
        }

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def analyze_prompt(self, prompt: str) -> TaskAnalysis:
        """
        Analyze prompt to determine task type and complexity

        Args:
            prompt: User's prompt text

        Returns:
            TaskAnalysis object with detected characteristics
        """
        prompt_lower = prompt.lower()

        # Detect task type
        task_type = 'general'
        max_matches = 0

        for task, patterns in self.task_patterns.items():
            matches = sum(1 for pattern in patterns if re.search(pattern, prompt_lower, re.IGNORECASE))
            if matches > max_matches:
                max_matches = matches
                task_type = task

        # Detect complexity
        complexity = 'medium'  # Default

        simple_matches = sum(
            1 for pattern in self.complexity_indicators['simple']
            if re.search(pattern, prompt_lower, re.IGNORECASE)
        )
        complex_matches = sum(
            1 for pattern in self.complexity_indicators['complex']
            if re.search(pattern, prompt_lower, re.IGNORECASE)
        )

        # Length-based complexity adjustment
        word_count = len(prompt.split())
        if word_count < 20:
            simple_matches += 1
        elif word_count > 100:
            complex_matches += 1

        if simple_matches > complex_matches:
            complexity = 'simple'
        elif complex_matches > simple_matches:
            complexity = 'complex'

        # Estimate token count (rough approximation)
        # Average: 1 word ≈ 1.3 tokens, plus response buffer
        estimated_tokens = int(word_count * 1.3 + 500)  # +500 for response

        # Detect special requirements
        requires_reasoning = bool(re.search(
            r'\b(why|how|explain|reason|logic|think|analyze)\b',
            prompt_lower
        ))

        requires_code_generation = bool(re.search(
            r'\b(code|function|implement|create|build|develop)\b',
            prompt_lower
        )) and task_type == 'coding'

        requires_creativity = bool(re.search(
            r'\b(creative|original|unique|innovative|imaginative)\b',
            prompt_lower
        )) or task_type == 'writing'

        return TaskAnalysis(
            task_type=task_type,
            complexity=complexity,
            estimated_tokens=estimated_tokens,
            requires_reasoning=requires_reasoning,
            requires_code_generation=requires_code_generation,
            requires_creativity=requires_creativity
        )

    def get_model_costs(self, provider: Optional[str] = None, model: Optional[str] = None) -> List[Dict]:
        """
        Get model pricing information

        Args:
            provider: Filter by provider (optional)
            model: Filter by specific model (optional)

        Returns:
            List of model cost dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT provider, model, credits_per_1k_tokens,
                       base_cost_usd, markup_percentage, is_active
                FROM model_credit_costs
                WHERE is_active = 1
            """
            params = []

            if provider:
                query += " AND provider = ?"
                params.append(provider)

            if model:
                query += " AND model = ?"
                params.append(model)

            query += " ORDER BY credits_per_1k_tokens ASC"

            cursor.execute(query, params)
            results = cursor.fetchall()

            return [dict(row) for row in results]

    def get_top_models_for_task(
        self,
        task_type: str,
        complexity: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        Get top-rated models suitable for specific task

        Args:
            task_type: Type of task (coding, writing, etc.)
            complexity: Complexity level (simple, medium, complex)
            limit: Maximum number of models to return

        Returns:
            List of model dictionaries with rankings
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Map task types to use cases in database
            use_case_map = {
                'coding': 'coding',
                'writing': 'writing',
                'analysis': 'analysis',
                'translation': 'general',
                'math': 'math',
                'general': 'general',
            }

            use_case = use_case_map.get(task_type, 'general')

            # First, try to get models from model_credit_costs (which has provider/model split)
            # and join with rankings if available
            query = """
                SELECT DISTINCT
                    c.provider,
                    c.model,
                    COALESCE(r.score, 0.5) as overall_score,
                    COALESCE(r.use_case, 'general') as use_case,
                    COALESCE(r.complexity, 'medium') as complexity,
                    COALESCE(r.cost_tier, 'medium') as cost_tier,
                    c.credits_per_1k_tokens,
                    c.base_cost_usd,
                    c.markup_percentage
                FROM model_credit_costs c
                LEFT JOIN ai_model_rankings r
                    ON (c.provider || '/' || c.model = r.model_name
                        OR c.model = r.model_name)
                WHERE c.is_active = 1
                ORDER BY
                    CASE WHEN COALESCE(r.use_case, 'general') = ? THEN 1 ELSE 2 END,
                    CASE WHEN COALESCE(r.complexity, 'medium') = ? THEN 1 ELSE 2 END,
                    COALESCE(r.score, 0.5) DESC,
                    c.credits_per_1k_tokens ASC
                LIMIT ?
            """

            cursor.execute(query, (use_case, complexity, limit))
            results = cursor.fetchall()

            models = []
            for row in results:
                model_dict = dict(row)
                # Ensure credits_per_1k_tokens exists
                if not model_dict.get('credits_per_1k_tokens'):
                    model_dict['credits_per_1k_tokens'] = 25  # Default like GPT-4o
                models.append(model_dict)

            return models

    def calculate_cost(
        self,
        provider: str,
        model: str,
        estimated_tokens: int
    ) -> int:
        """
        Calculate credit cost for a request

        Args:
            provider: AI provider name
            model: Model name
            estimated_tokens: Estimated number of tokens

        Returns:
            Estimated cost in credits
        """
        costs = self.get_model_costs(provider=provider, model=model)

        if not costs:
            # Fallback: use average cost
            logger.warning(f"No cost data for {provider}/{model}, using default")
            return max(1, int(estimated_tokens / 1000 * 25))  # Default 25 credits/1K

        cost_info = costs[0]
        credits_per_1k = cost_info['credits_per_1k_tokens']

        # Calculate cost based on token estimate
        credit_cost = int((estimated_tokens / 1000) * credits_per_1k)

        # Minimum 1 credit
        return max(1, credit_cost)

    def select_model(
        self,
        prompt: str,
        user_credits: int,
        prefer_cheap: bool = False,
        required_provider: Optional[str] = None
    ) -> ModelRecommendation:
        """
        Select best AI model for a prompt considering user's credits

        Args:
            prompt: User's prompt
            user_credits: User's available credits
            prefer_cheap: Prefer cheaper models even if quality is lower
            required_provider: Force specific provider (optional)

        Returns:
            ModelRecommendation with selected model and cost estimate
        """
        # Analyze the prompt
        analysis = self.analyze_prompt(prompt)

        logger.info(
            f"Task analysis: type={analysis.task_type}, "
            f"complexity={analysis.complexity}, "
            f"tokens={analysis.estimated_tokens}"
        )

        # Get top models for this task
        top_models = self.get_top_models_for_task(
            task_type=analysis.task_type,
            complexity=analysis.complexity,
            limit=10
        )

        if required_provider:
            top_models = [m for m in top_models if m['provider'] == required_provider]

        if not top_models:
            # Fallback to any available model
            logger.warning("No models found for criteria, using fallback")
            return self._fallback_model(analysis.estimated_tokens)

        # Calculate cost for each model and filter by user's credits
        affordable_models = []

        for model in top_models:
            cost = self.calculate_cost(
                provider=model['provider'],
                model=model['model'],
                estimated_tokens=analysis.estimated_tokens
            )

            if cost <= user_credits:
                affordable_models.append({
                    'provider': model['provider'],
                    'model': model['model'],
                    'cost': cost,
                    'quality_score': model.get('overall_score', 0.5),
                    'credits_per_1k': model['credits_per_1k_tokens'],
                    'cost_tier': model.get('cost_tier', 'medium'),
                })

        if not affordable_models:
            # User doesn't have enough credits for any model
            cheapest = top_models[0]
            min_cost = self.calculate_cost(
                cheapest['provider'],
                cheapest['model'],
                analysis.estimated_tokens
            )

            return ModelRecommendation(
                provider=cheapest['provider'],
                model=cheapest['model'],
                estimated_cost_credits=min_cost,
                quality_score=cheapest.get('overall_score', 0.5),
                reasoning=f"Insufficient credits. Need {min_cost}, have {user_credits}",
                cost_tier=cheapest.get('cost_tier', 'medium'),
                credits_per_1k_tokens=cheapest['credits_per_1k_tokens']
            )

        # Select model based on strategy
        if prefer_cheap:
            # Sort by cost ascending, then quality descending
            affordable_models.sort(key=lambda x: (x['cost'], -x['quality_score']))
        else:
            # Sort by quality descending, then cost ascending
            affordable_models.sort(key=lambda x: (-x['quality_score'], x['cost']))

        selected = affordable_models[0]

        # Generate reasoning
        reasoning = self._generate_reasoning(analysis, selected, len(affordable_models))

        return ModelRecommendation(
            provider=selected['provider'],
            model=selected['model'],
            estimated_cost_credits=selected['cost'],
            quality_score=selected['quality_score'],
            reasoning=reasoning,
            cost_tier=selected['cost_tier'],
            credits_per_1k_tokens=selected['credits_per_1k']
        )

    def _generate_reasoning(
        self,
        analysis: TaskAnalysis,
        selected_model: Dict,
        num_options: int
    ) -> str:
        """Generate human-readable reasoning for model selection"""
        reasons = []

        reasons.append(f"Task type: {analysis.task_type}")
        reasons.append(f"Complexity: {analysis.complexity}")
        reasons.append(f"Quality score: {selected_model['quality_score']:.2f}")
        reasons.append(f"Cost: {selected_model['cost']} credits")

        if num_options > 1:
            reasons.append(f"Selected from {num_options} affordable options")

        if selected_model['cost_tier'] == 'cheap':
            reasons.append("Most cost-effective choice")
        elif selected_model['cost_tier'] == 'expensive':
            reasons.append("Premium model for best quality")

        return " | ".join(reasons)

    def _fallback_model(self, estimated_tokens: int) -> ModelRecommendation:
        """Fallback to GPT-4o-mini if no other model found"""
        cost = self.calculate_cost('openai', 'gpt-4o-mini', estimated_tokens)

        return ModelRecommendation(
            provider='openai',
            model='gpt-4o-mini',
            estimated_cost_credits=cost,
            quality_score=0.75,
            reasoning="Fallback model - no matching models found",
            cost_tier='cheap',
            credits_per_1k_tokens=2
        )

    def get_model_info(self, provider: str, model: str) -> Optional[Dict]:
        """
        Get detailed information about a specific model

        Args:
            provider: Provider name
            model: Model name

        Returns:
            Model information dictionary or None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get from model_credit_costs and try to join with rankings
            cursor.execute("""
                SELECT
                    c.provider,
                    c.model,
                    COALESCE(r.score, 0.5) as overall_score,
                    0.5 as speed_score,
                    COALESCE(r.score, 0.5) as quality_score,
                    1.0 - (c.credits_per_1k_tokens / 100.0) as cost_score,
                    COALESCE(r.use_case, 'general') as use_case,
                    COALESCE(r.complexity, 'medium') as complexity,
                    COALESCE(r.cost_tier, 'medium') as cost_tier,
                    c.credits_per_1k_tokens,
                    c.base_cost_usd,
                    c.markup_percentage
                FROM model_credit_costs c
                LEFT JOIN ai_model_rankings r
                    ON (c.provider || '/' || c.model = r.model_name
                        OR c.model = r.model_name)
                WHERE c.provider = ? AND c.model = ?
            """, (provider, model))

            result = cursor.fetchone()
            return dict(result) if result else None


# Convenience function
def get_model_selector() -> ModelSelector:
    """Get ModelSelector instance"""
    return ModelSelector()
