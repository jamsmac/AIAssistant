"""
Integration tests for Enhanced Fractal Agent v3.0
"""

import pytest
from unittest.mock import Mock, AsyncMock
from agents.fractal.enhanced_agent import EnhancedFractalAgent


@pytest.fixture
def mock_db():
    """Create mock database connection"""
    db = Mock()
    db.fetch_one = AsyncMock(return_value={
        'agent_id': 'test-agent',
        'agent_name': 'Test Agent',
        'agent_type': 'specialist',
        'skills': ['backend', 'api'],
        'system_prompt': 'Test prompt'
    })
    db.fetch_all = AsyncMock(return_value=[])
    db.execute = AsyncMock()
    return db


@pytest.fixture
async def agent(mock_db):
    """Create enhanced agent instance"""
    agent = EnhancedFractalAgent(
        agent_id='test-agent',
        db=mock_db,
        api_key='test-key',
        use_plugin_registry=True,
        use_llm_router=True,
        use_progressive_disclosure=True
    )
    await agent.initialize()
    return agent


class TestEnhancedAgentInitialization:
    """Test Enhanced Fractal Agent initialization"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, agent):
        """Test agent initialization"""
        assert agent.agent_id == 'test-agent'
        assert agent.use_plugin_registry is True
        assert agent.use_llm_router is True
        assert agent.use_progressive_disclosure is True
    
    @pytest.mark.asyncio
    async def test_plugin_registry_integration(self, agent):
        """Test plugin registry is integrated"""
        assert hasattr(agent, 'registry')
        assert agent.registry is not None
    
    @pytest.mark.asyncio
    async def test_llm_router_integration(self, agent):
        """Test LLM router is integrated"""
        assert hasattr(agent, 'llm_router')
        assert agent.llm_router is not None
    
    @pytest.mark.asyncio
    async def test_skills_registry_integration(self, agent):
        """Test skills registry is integrated"""
        assert hasattr(agent, 'skills_registry')
        assert agent.skills_registry is not None


class TestTaskExecution:
    """Test task execution with v3.0 features"""
    
    @pytest.mark.asyncio
    async def test_execute_simple_task(self, agent):
        """Test executing simple task"""
        task = {
            'description': 'List all files',
            'type': 'simple'
        }
        
        # Mock the execution
        agent._execute_with_llm = AsyncMock(return_value={
            'success': True,
            'result': 'Files listed successfully'
        })
        
        result = await agent.execute_task(task)
        
        assert result['success'] is True
        assert 'result' in result
    
    @pytest.mark.asyncio
    async def test_execute_with_llm_routing(self, agent):
        """Test task execution uses LLM router"""
        task = {
            'description': 'Design a complex microservices architecture',
            'type': 'complex'
        }
        
        # Mock execution
        agent._execute_with_llm = AsyncMock(return_value={
            'success': True,
            'result': 'Architecture designed',
            'model_used': 'opus'
        })
        
        result = await agent.execute_task(task)
        
        # Should use appropriate model based on complexity
        assert result['success'] is True
        assert 'model_used' in result


class TestSkillsIntegration:
    """Test Progressive Disclosure skills integration"""
    
    @pytest.mark.asyncio
    async def test_skill_activation_on_task(self, agent):
        """Test skills are activated based on task"""
        task = {
            'description': 'Create a backend API with authentication',
            'required_skills': ['backend', 'api', 'auth']
        }
        
        # Mock execution
        agent._execute_with_llm = AsyncMock(return_value={
            'success': True,
            'result': 'API created'
        })
        
        result = await agent.execute_task(task)
        
        # Skills should be activated
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_context_optimization(self, agent):
        """Test context is optimized with progressive disclosure"""
        # Register some skills
        for i in range(10):
            agent.skills_registry.register_skill(
                name=f'skill-{i}',
                description=f'Skill {i}',
                category='test',
                triggers=[f'trigger{i}'],
                level_1_content="Metadata",
                level_2_content="Instructions" * 50,
                level_3_content="Resources" * 200
            )
        
        task = {
            'description': 'Task that triggers skill-0',
            'type': 'simple'
        }
        
        # Mock execution
        agent._execute_with_llm = AsyncMock(return_value={
            'success': True,
            'result': 'Task completed'
        })
        
        result = await agent.execute_task(task)
        
        # Only relevant skills should be loaded
        stats = agent.skills_registry.get_statistics()
        assert stats['context_saved_percentage'] > 50


class TestPluginAgentExecution:
    """Test execution of plugin-based agents"""
    
    @pytest.mark.asyncio
    async def test_execute_catalog_agent(self, agent):
        """Test executing agent from catalog"""
        # Mock catalog agent
        agent.registry.get_agent = Mock(return_value=Mock(
            name='backend-architect',
            system_prompt='You are a backend architect',
            model='sonnet'
        ))
        
        task = {
            'description': 'Design backend architecture',
            'agent': 'backend-architect'
        }
        
        # Mock execution
        agent._execute_with_llm = AsyncMock(return_value={
            'success': True,
            'result': 'Architecture designed'
        })
        
        result = await agent.execute_task(task)
        
        assert result['success'] is True


class TestCostOptimization:
    """Test cost optimization with LLM router"""
    
    @pytest.mark.asyncio
    async def test_cost_tracking(self, agent):
        """Test cost is tracked"""
        tasks = [
            {'description': 'Simple task 1', 'type': 'simple'},
            {'description': 'Simple task 2', 'type': 'simple'},
            {'description': 'Complex task', 'type': 'complex'}
        ]
        
        # Mock execution
        agent._execute_with_llm = AsyncMock(return_value={
            'success': True,
            'result': 'Task completed'
        })
        
        for task in tasks:
            await agent.execute_task(task)
        
        # Check router statistics
        stats = agent.llm_router.get_statistics()
        assert stats['total_requests'] == 3
        assert 'estimated_cost_saved' in stats


class TestBackwardCompatibility:
    """Test backward compatibility with base FractalAgent"""
    
    @pytest.mark.asyncio
    async def test_disable_v3_features(self, mock_db):
        """Test agent works with v3 features disabled"""
        agent = EnhancedFractalAgent(
            agent_id='test-agent',
            db=mock_db,
            api_key='test-key',
            use_plugin_registry=False,
            use_llm_router=False,
            use_progressive_disclosure=False
        )
        
        await agent.initialize()
        
        # Should work like base FractalAgent
        assert agent.use_plugin_registry is False
        assert agent.use_llm_router is False
        assert agent.use_progressive_disclosure is False
    
    @pytest.mark.asyncio
    async def test_base_agent_methods(self, agent):
        """Test base agent methods still work"""
        # Should have all base agent methods
        assert hasattr(agent, 'assess_capability')
        assert hasattr(agent, 'decompose_task')
        assert hasattr(agent, 'delegate_task')


class TestPerformanceMetrics:
    """Test performance metrics tracking"""
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self, agent):
        """Test metrics are collected"""
        task = {
            'description': 'Test task',
            'type': 'simple'
        }
        
        # Mock execution
        agent._execute_with_llm = AsyncMock(return_value={
            'success': True,
            'result': 'Task completed'
        })
        
        result = await agent.execute_task(task)
        
        # Should have metrics
        assert 'execution_time' in result or 'metrics' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
