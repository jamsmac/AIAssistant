"""
Comprehensive tests for FractalAgents system
"""
import pytest
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.postgres_db import PostgresDB
from agents.fractal import FractalAgent, FractalAgentOrchestrator


@pytest.fixture
async def db():
    """Database fixture"""
    db = PostgresDB()
    await db.connect()
    yield db
    await db.disconnect()


@pytest.fixture
async def orchestrator(db):
    """Orchestrator fixture"""
    orch = FractalAgentOrchestrator(db)
    await orch.initialize('test-org')
    return orch


class TestFractalAgentOrchestrator:
    """Test orchestrator functionality"""

    @pytest.mark.asyncio
    async def test_initialization(self, orchestrator):
        """Test orchestrator initializes correctly"""
        assert orchestrator.root_agent is not None
        assert orchestrator._initialized is True

    @pytest.mark.asyncio
    async def test_create_agent(self, orchestrator):
        """Test agent creation"""
        agent_id = await orchestrator.create_agent(
            organization_id='test-org',
            name='TestAgent',
            skills=['test_skill', 'another_skill'],
            agent_type='specialist'
        )

        assert agent_id is not None

        # Verify agent exists
        agent = await orchestrator.get_agent(agent_id)
        assert agent is not None
        assert agent['name'] == 'TestAgent'
        assert 'test_skill' in agent['skills']

    @pytest.mark.asyncio
    async def test_create_connector(self, orchestrator):
        """Test connector creation"""
        # Create two agents
        agent1_id = await orchestrator.create_agent(
            organization_id='test-org',
            name='Agent1',
            skills=['skill1']
        )

        agent2_id = await orchestrator.create_agent(
            organization_id='test-org',
            name='Agent2',
            skills=['skill2']
        )

        # Create connector
        await orchestrator.create_connector(
            from_agent_id=agent1_id,
            to_agent_id=agent2_id,
            strength=0.8,
            trust=0.9
        )

        # Verify connector exists
        connectors = await orchestrator.db.fetch("""
            SELECT * FROM agent_connectors
            WHERE from_agent_id = $1 AND to_agent_id = $2
        """, agent1_id, agent2_id)

        assert len(connectors) > 0
        assert connectors[0]['strength'] == 0.8

    @pytest.mark.asyncio
    async def test_system_status(self, orchestrator):
        """Test system status retrieval"""
        status = await orchestrator.get_system_status('test-org')

        assert 'agents' in status
        assert 'connectors' in status
        assert 'collective_memory' in status
        assert 'status' in status


class TestFractalAgent:
    """Test individual agent functionality"""

    @pytest.mark.asyncio
    async def test_agent_initialization(self, orchestrator):
        """Test agent initialization"""
        agent_id = await orchestrator.create_agent(
            organization_id='test-org',
            name='InitTestAgent',
            skills=['test_skill']
        )

        agent = FractalAgent(agent_id, orchestrator.db)
        await agent.initialize()

        assert agent._initialized is True
        assert agent.data is not None
        assert agent.skills is not None

    @pytest.mark.asyncio
    async def test_can_handle(self, orchestrator):
        """Test agent capability assessment"""
        agent_id = await orchestrator.create_agent(
            organization_id='test-org',
            name='SkillTestAgent',
            skills=['data_analysis', 'reporting']
        )

        agent = FractalAgent(agent_id, orchestrator.db)
        await agent.initialize()

        # Test with matching skills
        can_handle, confidence = await agent.can_handle({
            'required_skills': ['data_analysis'],
            'description': 'Test task'
        })

        assert can_handle is True
        assert confidence > 0

        # Test with non-matching skills
        can_handle, confidence = await agent.can_handle({
            'required_skills': ['nonexistent_skill'],
            'description': 'Test task'
        })

        assert can_handle is False

    @pytest.mark.asyncio
    async def test_task_routing(self, orchestrator):
        """Test task routing logic"""
        # Create root agent
        root_id = orchestrator.root_agent.agent_id

        # Create specialist agent
        specialist_id = await orchestrator.create_agent(
            organization_id='test-org',
            name='SpecialistAgent',
            skills=['specialized_skill']
        )

        # Create connector
        await orchestrator.create_connector(
            from_agent_id=root_id,
            to_agent_id=specialist_id,
            strength=0.9
        )

        # Test routing
        root_agent = orchestrator.root_agent
        best_agent_id, confidence = await root_agent.route_task({
            'required_skills': ['specialized_skill'],
            'description': 'Test routing',
            'organization_id': 'test-org'
        })

        assert best_agent_id == specialist_id


class TestTaskProcessing:
    """Test end-to-end task processing"""

    @pytest.mark.asyncio
    async def test_simple_task(self, orchestrator):
        """Test processing a simple task"""
        task = {
            'description': 'Write a short paragraph about AI',
            'required_skills': ['writing'],
            'type': 'content_creation',
            'organization_id': 'test-org'
        }

        result = await orchestrator.process_task(task)

        assert 'success' in result
        assert 'response' in result or 'error' in result

    @pytest.mark.asyncio
    async def test_memory_storage(self, orchestrator):
        """Test that tasks are stored in memory"""
        task = {
            'description': 'Test memory task',
            'required_skills': ['test_skill'],
            'type': 'test',
            'organization_id': 'test-org'
        }

        # Process task
        await orchestrator.process_task(task)

        # Check memory
        memory = await orchestrator.query_memory(
            organization_id='test-org',
            task_type='test',
            limit=1
        )

        assert len(memory) > 0


def run_tests():
    """Run all tests"""
    pytest.main([__file__, '-v', '--asyncio-mode=auto'])


if __name__ == '__main__':
    run_tests()
