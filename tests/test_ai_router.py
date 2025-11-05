"""
Unit tests for AI Router module
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import asyncio

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.ai_router import AIRouter


class TestAIRouter:
    """Test AI Router functionality"""

    @pytest.fixture
    def router(self):
        """Create router instance for testing"""
        return AIRouter()

    def test_initialization(self, router):
        """Test router initialization"""
        assert router is not None
        assert hasattr(router, 'models')
        assert hasattr(router, 'call_count')
        assert hasattr(router, 'total_cost')

    def test_select_model_by_task(self, router):
        """Test model selection based on task type"""
        # Test architecture task
        model = router._select_model('architecture', 'expensive', 10)
        assert model in ['claude', 'openai']

        # Test code task
        model = router._select_model('code', 'cheap', 5)
        assert model in ['openrouter', 'openai', 'gemini']

        # Test review task with free budget
        model = router._select_model('review', 'free', 3)
        assert model in ['gemini', 'ollama']

    def test_select_model_by_budget(self, router):
        """Test model selection respects budget"""
        # Free budget should only return free models
        model = router._select_model('general', 'free', 5)
        assert model in ['gemini', 'ollama']

        # Expensive budget can use any model
        model = router._select_model('general', 'expensive', 5)
        assert model is not None

    def test_get_available_models(self, router):
        """Test getting available models"""
        available = router._get_available_models()

        assert isinstance(available, dict)
        assert 'claude' in available
        assert 'openai' in available
        assert 'gemini' in available
        assert 'ollama' in available

    @patch('agents.ai_router.anthropic.Anthropic')
    def test_call_claude(self, mock_anthropic, router):
        """Test calling Claude model"""
        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Claude response")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        # Set API key
        import os
        os.environ['ANTHROPIC_API_KEY'] = 'test-key'

        # Call Claude
        result = router._call_claude("Test prompt")

        assert result == "Claude response"
        mock_client.messages.create.assert_called_once()

    def test_estimate_cost(self, router):
        """Test cost estimation"""
        # Test Claude cost
        cost = router._estimate_cost('claude', 1000)
        assert cost > 0

        # Test free model cost
        cost = router._estimate_cost('gemini', 1000)
        assert cost == 0

        # Test unknown model
        cost = router._estimate_cost('unknown', 1000)
        assert cost == 0

    def test_get_stats(self, router):
        """Test getting router statistics"""
        # Increment counters
        router.call_count = 10
        router.total_cost = 1.5
        router.model_usage = {'claude': 3, 'openai': 7}

        stats = router.get_stats()

        assert stats['calls'] == 10
        assert stats['cost'] == 1.5
        assert stats['models']['claude'] == 3
        assert stats['models']['openai'] == 7

    @pytest.mark.asyncio
    async def test_route_async(self):
        """Test async routing"""
        router = AIRouter()

        # Mock the internal call
        with patch.object(router, '_call_ollama', return_value="Test response"):
            result = await router.route_async(
                prompt="Test",
                task_type="general",
                budget="free",
                complexity=5
            )

            assert result['response'] == "Test response"
            assert result['model'] == 'ollama'
            assert 'tokens' in result
            assert 'cost' in result

    def test_fallback_mechanism(self, router):
        """Test fallback to alternative models on failure"""
        # Mock all models to fail except the last one
        with patch.object(router, '_call_claude', side_effect=Exception("Claude failed")):
            with patch.object(router, '_call_openai', side_effect=Exception("OpenAI failed")):
                with patch.object(router, '_call_gemini', return_value="Gemini success"):
                    result = router.route(
                        prompt="Test",
                        task_type="general",
                        budget="expensive",
                        complexity=5
                    )

                    assert result['response'] == "Gemini success"
                    assert result['model'] == 'gemini'

    def test_cache_integration(self, router):
        """Test cache integration if database is available"""
        # Create mock database
        mock_db = MagicMock()
        mock_db.get_cached_response.return_value = {
            'response': 'Cached response',
            'model': 'cached-model'
        }

        router.db = mock_db

        result = router.route(
            prompt="Test prompt",
            task_type="test",
            budget="cheap",
            complexity=5
        )

        # Should use cached response
        assert result['response'] == 'Cached response'
        assert result['model'] == 'cached-model'
        assert result['cached'] == True

    def test_error_handling(self, router):
        """Test error handling when all models fail"""
        # Mock all models to fail
        with patch.object(router, '_call_claude', side_effect=Exception("Failed")):
            with patch.object(router, '_call_openai', side_effect=Exception("Failed")):
                with patch.object(router, '_call_openrouter', side_effect=Exception("Failed")):
                    with patch.object(router, '_call_gemini', side_effect=Exception("Failed")):
                        with patch.object(router, '_call_ollama', side_effect=Exception("Failed")):
                            with pytest.raises(Exception) as exc_info:
                                router.route(
                                    prompt="Test",
                                    task_type="general",
                                    budget="expensive",
                                    complexity=5
                                )

                            assert "All AI models failed" in str(exc_info.value)

    def test_model_priority_order(self, router):
        """Test that models are tried in correct priority order"""
        call_order = []

        def mock_claude(*args):
            call_order.append('claude')
            raise Exception("Claude failed")

        def mock_openai(*args):
            call_order.append('openai')
            raise Exception("OpenAI failed")

        def mock_gemini(*args):
            call_order.append('gemini')
            return "Success"

        with patch.object(router, '_call_claude', side_effect=mock_claude):
            with patch.object(router, '_call_openai', side_effect=mock_openai):
                with patch.object(router, '_call_gemini', side_effect=mock_gemini):
                    result = router.route(
                        prompt="Test",
                        task_type="architecture",  # Should prefer Claude
                        budget="expensive",
                        complexity=10
                    )

                    # Claude should be tried first for architecture tasks
                    assert call_order[0] == 'claude'
                    assert result['response'] == "Success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])