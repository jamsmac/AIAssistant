"""
Integration tests for LLM Router v3.0
"""

import pytest
from agents.routing import LLMRouter, ComplexityLevel, ComplexityAnalyzer


@pytest.fixture
def router():
    """Get fresh LLM Router instance"""
    return LLMRouter(prefer_cost_efficiency=True)


@pytest.fixture
def analyzer():
    """Get complexity analyzer instance"""
    return ComplexityAnalyzer()


class TestComplexityAnalyzer:
    """Test complexity analysis"""
    
    def test_simple_task_analysis(self, analyzer):
        """Test analysis of simple task"""
        task = "List all files in the directory"
        complexity, confidence, details = analyzer.analyze(task)
        
        assert complexity == ComplexityLevel.SIMPLE
        assert confidence > 0.5
        assert details['text_length'] > 0
    
    def test_moderate_task_analysis(self, analyzer):
        """Test analysis of moderate complexity task"""
        task = "Create a REST API endpoint for user registration with validation"
        complexity, confidence, details = analyzer.analyze(task)
        
        assert complexity in [ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX]
        assert confidence > 0.5
    
    def test_complex_task_analysis(self, analyzer):
        """Test analysis of complex task"""
        task = """
        Design a scalable microservices architecture with:
        1. API Gateway
        2. Service discovery
        3. Load balancing
        4. Database sharding
        5. Caching layer
        """
        complexity, confidence, details = analyzer.analyze(task)
        
        assert complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.EXPERT]
        assert confidence > 0.5
        assert details['word_count'] > 20
    
    def test_expert_task_analysis(self, analyzer):
        """Test analysis of expert-level task"""
        task = """
        Implement a distributed consensus algorithm for blockchain
        with Byzantine fault tolerance, proof of stake, and
        cryptographic verification using elliptic curve cryptography.
        """
        complexity, confidence, details = analyzer.analyze(task)
        
        assert complexity == ComplexityLevel.EXPERT
        assert confidence > 0.5


class TestLLMRouter:
    """Test LLM Router functionality"""
    
    @pytest.mark.asyncio
    async def test_analyze_complexity(self, router):
        """Test complexity analysis through router"""
        task = "Write a simple hello world program"
        complexity = await router.analyze_complexity(task)
        
        assert complexity == ComplexityLevel.SIMPLE
        assert router.stats['total_requests'] > 0
        assert router.stats['simple_tasks'] > 0
    
    @pytest.mark.asyncio
    async def test_select_model_for_simple_task(self, router):
        """Test model selection for simple task"""
        model = await router.select_model(ComplexityLevel.SIMPLE)
        
        # Should select a cheap model
        assert model in ['haiku', 'gpt-3.5-turbo', 'gemini']
    
    @pytest.mark.asyncio
    async def test_select_model_for_complex_task(self, router):
        """Test model selection for complex task"""
        model = await router.select_model(ComplexityLevel.COMPLEX)
        
        # Should select a more capable model
        assert model in ['opus', 'sonnet']
    
    @pytest.mark.asyncio
    async def test_select_model_for_expert_task(self, router):
        """Test model selection for expert task"""
        model = await router.select_model(ComplexityLevel.EXPERT)
        
        # Should select the most capable model
        assert model in ['gpt-4', 'opus']
    
    @pytest.mark.asyncio
    async def test_route_task(self, router):
        """Test complete task routing"""
        task = "Build a full-stack web application with authentication"
        
        model, complexity, details = await router.route_task(task)
        
        assert model is not None
        assert complexity in [ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX]
        assert 'estimated_cost' in details
        assert 'cost_saved_vs_gpt4' in details
        assert details['estimated_cost'] > 0
    
    @pytest.mark.asyncio
    async def test_cost_tracking(self, router):
        """Test cost tracking"""
        # Route multiple tasks
        tasks = [
            "List files",
            "Create API endpoint",
            "Design microservices architecture"
        ]
        
        for task in tasks:
            await router.route_task(task)
        
        stats = router.get_statistics()
        assert stats['total_requests'] == 3
        assert stats['estimated_cost_saved'] >= 0
    
    @pytest.mark.asyncio
    async def test_model_preference(self, router):
        """Test user model preference"""
        preferences = {'model': 'sonnet'}
        model = await router.select_model(
            ComplexityLevel.SIMPLE,
            preferences=preferences
        )
        
        # Should respect user preference if valid
        assert model == 'sonnet'


class TestCostOptimization:
    """Test cost optimization features"""
    
    @pytest.mark.asyncio
    async def test_cost_efficient_routing(self):
        """Test cost-efficient routing"""
        router = LLMRouter(prefer_cost_efficiency=True)
        
        # Simple task should use cheap model
        model = await router.select_model(ComplexityLevel.SIMPLE)
        cost = router._estimate_cost(model, 100)
        
        # Should be significantly cheaper than GPT-4
        gpt4_cost = router._estimate_cost('gpt-4', 100)
        assert cost < gpt4_cost * 0.5  # At least 50% cheaper
    
    @pytest.mark.asyncio
    async def test_cost_savings_calculation(self, router):
        """Test cost savings calculation"""
        # Route several tasks
        tasks = [
            "Simple task",
            "Moderate task with some complexity",
            "Complex task requiring deep analysis"
        ]
        
        for task in tasks:
            await router.route_task(task)
        
        stats = router.get_statistics()
        
        # Should show cost savings
        if 'cost_savings_percentage' in stats:
            assert stats['cost_savings_percentage'] > 0


class TestModelCapabilities:
    """Test model capability information"""
    
    def test_get_model_info(self, router):
        """Test retrieving model information"""
        info = router.get_model_info('haiku')
        
        assert info is not None
        assert 'max_tokens' in info
        assert 'speed' in info
        assert 'reasoning' in info
        assert 'cost_tier' in info
        assert 'costs' in info
    
    def test_model_costs(self, router):
        """Test model cost information"""
        for model in ['haiku', 'sonnet', 'opus', 'gpt-4']:
            info = router.get_model_info(model)
            assert info is not None
            assert 'input' in info['costs']
            assert 'output' in info['costs']
            assert info['costs']['input'] > 0
            assert info['costs']['output'] > 0


class TestStatistics:
    """Test statistics tracking"""
    
    @pytest.mark.asyncio
    async def test_request_counting(self, router):
        """Test request counting"""
        initial_count = router.stats['total_requests']
        
        await router.route_task("Test task")
        
        assert router.stats['total_requests'] == initial_count + 1
    
    @pytest.mark.asyncio
    async def test_complexity_distribution(self, router):
        """Test complexity distribution tracking"""
        # Route tasks of different complexity
        await router.route_task("List files")  # Simple
        await router.route_task("Create API with validation")  # Moderate
        await router.route_task("Design distributed system")  # Complex
        
        stats = router.get_statistics()
        
        # Should have distribution across complexity levels
        total = (stats['simple_tasks'] + stats['moderate_tasks'] + 
                stats['complex_tasks'] + stats['expert_tasks'])
        assert total == stats['total_requests']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
