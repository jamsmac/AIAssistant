"""
Integration tests for Plugin Registry v3.0
"""

import pytest
import hashlib
from agents.registry import (
    get_registry,
    PluginMetadata,
    AgentDefinition,
    SkillMetadata,
    ToolDefinition
)


@pytest.fixture
def registry():
    """Get fresh registry instance for each test"""
    return get_registry()


@pytest.fixture
def sample_plugin():
    """Create sample plugin metadata"""
    return PluginMetadata(
        name="test-plugin",
        version="1.0.0",
        description="Test plugin",
        category="testing",
        author="Test Author",
        checksum=hashlib.md5(b"test-plugin1.0.0").hexdigest()
    )


@pytest.fixture
def sample_agent():
    """Create sample agent definition"""
    return AgentDefinition(
        name="test-agent",
        description="Test agent",
        model="sonnet",
        system_prompt="You are a test agent.",
        trigger_keywords=["test"],
        estimated_tokens=1000,
        avg_response_time=2.0
    )


class TestPluginRegistry:
    """Test Plugin Registry functionality"""
    
    def test_register_plugin(self, registry, sample_plugin):
        """Test plugin registration"""
        result = registry.register_plugin(sample_plugin)
        assert result is True
        assert "test-plugin" in registry.plugins
    
    def test_register_duplicate_plugin(self, registry, sample_plugin):
        """Test registering duplicate plugin"""
        registry.register_plugin(sample_plugin)
        
        # Try to register same plugin again
        result = registry.register_plugin(sample_plugin)
        assert result is False  # Should fail
    
    def test_register_agent(self, registry, sample_plugin, sample_agent):
        """Test agent registration"""
        # Register plugin first
        registry.register_plugin(sample_plugin)
        
        # Register agent
        result = registry.register_agent(sample_agent, "test-plugin")
        assert result is True
        assert "test-agent" in registry.agents
    
    def test_register_agent_without_plugin(self, registry, sample_agent):
        """Test registering agent without plugin"""
        # Try to register agent without plugin
        result = registry.register_agent(sample_agent, "nonexistent-plugin")
        assert result is False
    
    def test_get_agent(self, registry, sample_plugin, sample_agent):
        """Test retrieving agent"""
        registry.register_plugin(sample_plugin)
        registry.register_agent(sample_agent, "test-plugin")
        
        agent = registry.get_agent("test-agent")
        assert agent is not None
        assert agent.name == "test-agent"
        assert agent.model == "sonnet"
    
    def test_list_agents(self, registry, sample_plugin):
        """Test listing agents"""
        registry.register_plugin(sample_plugin)
        
        # Register multiple agents
        for i in range(3):
            agent = AgentDefinition(
                name=f"agent-{i}",
                description=f"Agent {i}",
                model="sonnet",
                system_prompt=f"Agent {i}",
                trigger_keywords=[f"agent{i}"]
            )
            registry.register_agent(agent, "test-plugin")
        
        agents = registry.list_agents()
        assert len(agents) >= 3
    
    def test_list_agents_by_category(self, registry):
        """Test listing agents by category"""
        # Register plugins with different categories
        for category in ["development", "testing", "security"]:
            plugin = PluginMetadata(
                name=f"{category}-plugin",
                version="1.0.0",
                description=f"{category} plugin",
                category=category,
                checksum=hashlib.md5(f"{category}1.0.0".encode()).hexdigest()
            )
            registry.register_plugin(plugin)
            
            agent = AgentDefinition(
                name=f"{category}-agent",
                description=f"{category} agent",
                model="sonnet",
                system_prompt=f"{category} agent",
                trigger_keywords=[category]
            )
            registry.register_agent(agent, f"{category}-plugin")
        
        # Get agents by category
        dev_agents = registry.list_agents(category="development")
        assert len(dev_agents) >= 1
        assert all(a.name.startswith("development") for a in dev_agents)


class TestSkillRegistration:
    """Test skill registration in Plugin Registry"""
    
    def test_register_skill(self, registry, sample_plugin):
        """Test skill registration"""
        registry.register_plugin(sample_plugin)
        
        skill = SkillMetadata(
            name="test-skill",
            description="Test skill",
            category="testing",
            level=1,
            triggers=["test"],
            instructions_path="skills/test/instructions.md",
            resources_path="skills/test/resources.json"
        )
        
        result = registry.register_skill(skill, "test-plugin")
        assert result is True
        assert "test-skill" in registry.skills
    
    def test_get_skill(self, registry, sample_plugin):
        """Test retrieving skill"""
        registry.register_plugin(sample_plugin)
        
        skill = SkillMetadata(
            name="test-skill",
            description="Test skill",
            category="testing",
            level=1,
            triggers=["test"]
        )
        registry.register_skill(skill, "test-plugin")
        
        retrieved = registry.get_skill("test-skill")
        assert retrieved is not None
        assert retrieved.name == "test-skill"
        assert retrieved.level == 1


class TestToolRegistration:
    """Test tool registration in Plugin Registry"""
    
    def test_register_tool(self, registry, sample_plugin):
        """Test tool registration"""
        registry.register_plugin(sample_plugin)
        
        tool = ToolDefinition(
            name="test-tool",
            description="Test tool",
            category="testing",
            function_name="test_function",
            parameters={"param1": "string"}
        )
        
        result = registry.register_tool(tool, "test-plugin")
        assert result is True
        assert "test-tool" in registry.tools


class TestDependencyResolution:
    """Test plugin dependency resolution"""
    
    def test_resolve_dependencies(self, registry):
        """Test dependency resolution"""
        # Create plugins with dependencies
        plugin_a = PluginMetadata(
            name="plugin-a",
            version="1.0.0",
            description="Plugin A",
            category="testing",
            checksum=hashlib.md5(b"plugin-a1.0.0").hexdigest()
        )
        
        plugin_b = PluginMetadata(
            name="plugin-b",
            version="1.0.0",
            description="Plugin B",
            category="testing",
            dependencies=["plugin-a"],
            checksum=hashlib.md5(b"plugin-b1.0.0").hexdigest()
        )
        
        registry.register_plugin(plugin_a)
        registry.register_plugin(plugin_b)
        
        # Resolve dependencies
        order = registry.resolve_dependencies()
        assert order is not None
        assert order.index("plugin-a") < order.index("plugin-b")
    
    def test_circular_dependency_detection(self, registry):
        """Test circular dependency detection"""
        plugin_a = PluginMetadata(
            name="plugin-a",
            version="1.0.0",
            description="Plugin A",
            category="testing",
            dependencies=["plugin-b"],
            checksum=hashlib.md5(b"plugin-a1.0.0").hexdigest()
        )
        
        plugin_b = PluginMetadata(
            name="plugin-b",
            version="1.0.0",
            description="Plugin B",
            category="testing",
            dependencies=["plugin-a"],
            checksum=hashlib.md5(b"plugin-b1.0.0").hexdigest()
        )
        
        registry.register_plugin(plugin_a)
        registry.register_plugin(plugin_b)
        
        # Should detect circular dependency
        order = registry.resolve_dependencies()
        assert order is None  # Circular dependency should return None


class TestConflictDetection:
    """Test plugin conflict detection"""
    
    def test_detect_version_conflict(self, registry):
        """Test version conflict detection"""
        plugin_v1 = PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            description="Version 1",
            category="testing",
            checksum=hashlib.md5(b"test-plugin1.0.0").hexdigest()
        )
        
        plugin_v2 = PluginMetadata(
            name="test-plugin",
            version="2.0.0",
            description="Version 2",
            category="testing",
            checksum=hashlib.md5(b"test-plugin2.0.0").hexdigest()
        )
        
        registry.register_plugin(plugin_v1)
        
        # Try to register different version
        result = registry.register_plugin(plugin_v2)
        assert result is False  # Should detect conflict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
