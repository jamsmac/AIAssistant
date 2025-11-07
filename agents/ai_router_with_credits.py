"""
AI Router with Credit System Integration
Integrates ModelSelector and CreditManager for automatic credit-based routing
"""

import logging
from typing import Dict, Any, Optional
from .ai_router import AIRouter
from .model_selector import ModelSelector
from .credit_manager import CreditManager

logger = logging.getLogger(__name__)


class AIRouterWithCredits(AIRouter):
    """Extended AIRouter with credit system integration"""

    def __init__(self):
        """Initialize router with credit system"""
        super().__init__()
        self.model_selector = ModelSelector()
        self.credit_manager = CreditManager()

    def route_with_credits(
        self,
        prompt: str,
        user_id: int,
        task_type: str = 'general',
        complexity: str = 'medium',
        prefer_cheap: bool = False,
        required_provider: Optional[str] = None,
        session_id: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Route request with automatic credit management

        Args:
            prompt: User's prompt
            user_id: User ID for credit operations
            task_type: Task type (overrides auto-detection if provided)
            complexity: Complexity level (overrides auto-detection)
            prefer_cheap: Prefer cheaper models
            required_provider: Force specific provider
            session_id: Session ID for context
            use_cache: Use response caching

        Returns:
            Dict with response, model, cost, balance, etc.
        """
        try:
            # 1. Check user balance
            user_balance = self.credit_manager.get_balance(user_id)
            logger.info(f"User {user_id} balance: {user_balance} credits")

            if user_balance <= 0:
                return {
                    'error': True,
                    'message': 'Insufficient credits. Please purchase more credits.',
                    'balance': 0,
                    'required_credits': None
                }

            # 2. Analyze prompt and select model
            recommendation = self.model_selector.select_model(
                prompt=prompt,
                user_credits=user_balance,
                prefer_cheap=prefer_cheap,
                required_provider=required_provider
            )

            logger.info(
                f"Selected model: {recommendation.provider}/{recommendation.model} "
                f"(cost: {recommendation.estimated_cost_credits} credits)"
            )

            # 3. Check if user has sufficient credits
            if not self.credit_manager.has_sufficient_credits(
                user_id,
                recommendation.estimated_cost_credits
            ):
                return {
                    'error': True,
                    'message': f'Insufficient credits. Need {recommendation.estimated_cost_credits}, have {user_balance}',
                    'balance': user_balance,
                    'required_credits': recommendation.estimated_cost_credits,
                    'selected_model': f"{recommendation.provider}/{recommendation.model}"
                }

            # 4. Reserve credits (mark as pending)
            # Note: In production, you'd lock these credits to prevent double-spending
            reserved_amount = recommendation.estimated_cost_credits

            # 5. Execute AI request
            try:
                # Map provider/model to AIRouter format
                model_name = self._map_to_router_model(
                    recommendation.provider,
                    recommendation.model
                )

                # Call parent route method
                result = self._execute(model_name, prompt)

                # Check for errors
                if result.get('error'):
                    # Request failed - no charge
                    logger.warning(f"Request failed: {result.get('response')}")
                    return {
                        'error': True,
                        'message': result.get('response', 'Request failed'),
                        'balance': user_balance,
                        'model': model_name
                    }

                # 6. Calculate actual cost based on tokens used
                actual_tokens = result.get('tokens', recommendation.estimated_tokens)
                actual_cost = self.model_selector.calculate_cost(
                    provider=recommendation.provider,
                    model=recommendation.model,
                    estimated_tokens=actual_tokens
                )

                logger.info(
                    f"Actual usage: {actual_tokens} tokens, "
                    f"{actual_cost} credits (estimated: {reserved_amount})"
                )

                # 7. Charge credits
                charge_success = self.credit_manager.charge_credits(
                    user_id=user_id,
                    amount=actual_cost,
                    description=f"AI request: {recommendation.provider}/{recommendation.model}",
                    metadata={
                        'provider': recommendation.provider,
                        'model': recommendation.model,
                        'tokens': actual_tokens,
                        'task_type': recommendation.reasoning,
                        'session_id': session_id
                    }
                )

                if not charge_success:
                    logger.error(f"Failed to charge credits for user {user_id}")
                    # Still return response but log the issue
                    # In production, you might want to handle this differently

                # 8. Get updated balance
                new_balance = self.credit_manager.get_balance(user_id)

                # 9. Save to session if provided
                if session_id:
                    try:
                        self.db.add_message_to_session(
                            session_id=session_id,
                            role='user',
                            content=prompt,
                            tokens=len(prompt.split())
                        )
                        self.db.add_message_to_session(
                            session_id=session_id,
                            role='assistant',
                            content=result.get('response', ''),
                            model=model_name,
                            tokens=actual_tokens
                        )
                    except Exception as e:
                        logger.warning(f"Failed to save to session: {e}")

                # 10. Cache response if enabled
                if use_cache and not session_id:
                    try:
                        self.db.cache_response(
                            prompt=prompt,
                            response=result.get('response', ''),
                            model=model_name,
                            task_type=task_type,
                            ttl_hours=24
                        )
                    except Exception as e:
                        logger.warning(f"Failed to cache response: {e}")

                # 11. Return successful response
                return {
                    'error': False,
                    'response': result.get('response', ''),
                    'model': model_name,
                    'provider': recommendation.provider,
                    'tokens': actual_tokens,
                    'cost_credits': actual_cost,
                    'balance_before': user_balance,
                    'balance_after': new_balance,
                    'quality_score': recommendation.quality_score,
                    'reasoning': recommendation.reasoning,
                    'cached': False
                }

            except Exception as exec_error:
                # Request execution failed
                logger.error(f"Execution error: {exec_error}")

                # Refund reserved credits if charge was made
                # (In this implementation, we only charge after success, so no refund needed)

                return {
                    'error': True,
                    'message': f'Request failed: {str(exec_error)}',
                    'balance': user_balance,
                    'model': f"{recommendation.provider}/{recommendation.model}"
                }

        except Exception as e:
            logger.error(f"Router error: {e}")
            return {
                'error': True,
                'message': f'System error: {str(e)}',
                'balance': None
            }

    def _map_to_router_model(self, provider: str, model: str) -> str:
        """
        Map ModelSelector provider/model to AIRouter model name

        Args:
            provider: Provider name (openai, anthropic, google, etc.)
            model: Model name

        Returns:
            AIRouter-compatible model name
        """
        # Direct mappings
        mappings = {
            ('openai', 'gpt-4o'): 'gpt-4o',
            ('openai', 'gpt-4o-mini'): 'gpt-4o-mini',
            ('openai', 'gpt-4-turbo'): 'gpt-4-turbo',
            ('openai', 'gpt-3.5-turbo'): 'gpt-3.5-turbo',
            ('anthropic', 'claude-3-5-sonnet-20241022'): 'claude-sonnet-4-20250514',
            ('anthropic', 'claude-3-5-haiku-20241022'): 'claude-3-5-haiku-20241022',
            ('anthropic', 'claude-3-opus-20240229'): 'claude-3-opus-20240229',
            ('anthropic', 'claude-sonnet-4-5-20250929'): 'claude-sonnet-4-20250514',
            ('google', 'gemini-1.5-pro'): 'gemini-1.5-pro',
            ('google', 'gemini-1.5-flash'): 'gemini-2.0-flash',
            ('google', 'gemini-2.0-flash-exp'): 'gemini-2.0-flash',
        }

        # Check if we have a direct mapping
        key = (provider, model)
        if key in mappings:
            return mappings[key]

        # For other models, try to use OpenRouter format
        if provider == 'deepseek':
            return f"deepseek/{model}"
        elif provider in ['mistral', 'cohere', 'meta', 'xai']:
            return f"{provider}/{model}"

        # Fallback: return as-is
        return model

    def get_cost_estimate(
        self,
        prompt: str,
        user_id: int,
        prefer_cheap: bool = False,
        required_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get cost estimate without making the request

        Args:
            prompt: User's prompt
            user_id: User ID
            prefer_cheap: Prefer cheaper models
            required_provider: Force specific provider

        Returns:
            Dict with estimation details
        """
        try:
            user_balance = self.credit_manager.get_balance(user_id)

            recommendation = self.model_selector.select_model(
                prompt=prompt,
                user_credits=user_balance,
                prefer_cheap=prefer_cheap,
                required_provider=required_provider
            )

            analysis = self.model_selector.analyze_prompt(prompt)

            return {
                'estimated_cost_credits': recommendation.estimated_cost_credits,
                'estimated_tokens': analysis.estimated_tokens,
                'selected_model': recommendation.model,
                'provider': recommendation.provider,
                'quality_score': recommendation.quality_score,
                'cost_tier': recommendation.cost_tier,
                'user_balance': user_balance,
                'sufficient_credits': user_balance >= recommendation.estimated_cost_credits,
                'task_analysis': {
                    'task_type': analysis.task_type,
                    'complexity': analysis.complexity,
                    'requires_reasoning': analysis.requires_reasoning,
                    'requires_code_generation': analysis.requires_code_generation,
                    'requires_creativity': analysis.requires_creativity
                },
                'reasoning': recommendation.reasoning,
                'credits_per_1k_tokens': recommendation.credits_per_1k_tokens
            }

        except Exception as e:
            logger.error(f"Estimation error: {e}")
            return {
                'error': True,
                'message': str(e)
            }


# Convenience function
def get_router_with_credits() -> AIRouterWithCredits:
    """Get AIRouterWithCredits instance"""
    return AIRouterWithCredits()
