"""
Plugin Registry - Centralized Plugin Management
Manages all agents, skills, tools, and workflows with dependency resolution
"""

import logging
from typing import Dict, List, Optional, Set
from pathlib import Path
import json
from .models import (
    PluginMetadata,
    AgentDefinition,
    SkillMetadata,
    ToolDefinition,
    WorkflowDefinition
)

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Centralized registry for all plugins, agents, skills, and tools
    Provides type-safe registration, validation, and retrieval
    """
    
    def __init__(self, plugins_dir: Optional[Path] = None):
        """
        Initialize the plugin registry
        
        Args:
            plugins_dir: Directory containing plugin definitions
        """
        self.plugins_dir = plugins_dir or Path(__file__).parent.parent / "catalog"
        
        # Storage
        self.plugins: Dict[str, PluginMetadata] = {}
        self.agents: Dict[str, AgentDefinition] = {}
        self.skills: Dict[str, SkillMetadata] = {}
        self.tools: Dict[str, ToolDefinition] = {}
        self.workflows: Dict[str, WorkflowDefinition] = {}
        
        # Dependency tracking
        self.dependency_graph: Dict[str, Set[str]] = {}
        self.load_order: List[str] = []
        
        logger.info(f"Plugin Registry initialized with plugins_dir: {self.plugins_dir}")
    
    def register_plugin(self, plugin: PluginMetadata) -> bool:
        """
        Register a new plugin
        
        Args:
            plugin: Plugin metadata
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Validate plugin
            if plugin.name in self.plugins:
                logger.warning(f"Plugin {plugin.name} already registered, updating...")
            
            # Check for conflicts
            for conflict in plugin.conflicts:
                if conflict in self.plugins:
                    logger.error(f"Plugin {plugin.name} conflicts with {conflict}")
                    return False
            
            # Check dependencies
            for dependency in plugin.requires:
                if dependency not in self.plugins:
                    logger.warning(f"Plugin {plugin.name} requires {dependency} which is not loaded")
            
            # Register plugin
            self.plugins[plugin.name] = plugin
            self.dependency_graph[plugin.name] = set(plugin.requires)
            
            logger.info(f"Plugin {plugin.name} v{plugin.version} registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register plugin {plugin.name}: {str(e)}")
            return False
    
    def register_agent(self, agent: AgentDefinition, plugin_name: str) -> bool:
        """
        Register a new agent
        
        Args:
            agent: Agent definition
            plugin_name: Name of the plugin providing this agent
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            if agent.name in self.agents:
                logger.warning(f"Agent {agent.name} already registered, updating...")
            
            self.agents[agent.name] = agent
            logger.info(f"Agent {agent.name} registered from plugin {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register agent {agent.name}: {str(e)}")
            return False
    
    def register_skill(self, skill: SkillMetadata, plugin_name: str) -> bool:
        """
        Register a new skill
        
        Args:
            skill: Skill metadata
            plugin_name: Name of the plugin providing this skill
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            if skill.name in self.skills:
                logger.warning(f"Skill {skill.name} already registered, updating...")
            
            self.skills[skill.name] = skill
            logger.info(f"Skill {skill.name} registered from plugin {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register skill {skill.name}: {str(e)}")
            return False
    
    def register_tool(self, tool: ToolDefinition, plugin_name: str) -> bool:
        """
        Register a new tool
        
        Args:
            tool: Tool definition
            plugin_name: Name of the plugin providing this tool
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            if tool.name in self.tools:
                logger.warning(f"Tool {tool.name} already registered, updating...")
            
            self.tools[tool.name] = tool
            logger.info(f"Tool {tool.name} registered from plugin {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register tool {tool.name}: {str(e)}")
            return False
    
    def register_workflow(self, workflow: WorkflowDefinition, plugin_name: str) -> bool:
        """
        Register a new workflow
        
        Args:
            workflow: Workflow definition
            plugin_name: Name of the plugin providing this workflow
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            if workflow.name in self.workflows:
                logger.warning(f"Workflow {workflow.name} already registered, updating...")
            
            self.workflows[workflow.name] = workflow
            logger.info(f"Workflow {workflow.name} registered from plugin {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register workflow {workflow.name}: {str(e)}")
            return False
    
    def get_plugin(self, name: str) -> Optional[PluginMetadata]:
        """Get plugin by name"""
        return self.plugins.get(name)
    
    def get_agent(self, name: str) -> Optional[AgentDefinition]:
        """Get agent by name"""
        return self.agents.get(name)
    
    def get_skill(self, name: str) -> Optional[SkillMetadata]:
        """Get skill by name"""
        return self.skills.get(name)
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get tool by name"""
        return self.tools.get(name)
    
    def get_workflow(self, name: str) -> Optional[WorkflowDefinition]:
        """Get workflow by name"""
        return self.workflows.get(name)
    
    def list_plugins(self, category: Optional[str] = None, enabled_only: bool = True) -> List[PluginMetadata]:
        """
        List all plugins, optionally filtered by category
        
        Args:
            category: Optional category filter
            enabled_only: Only return enabled plugins
            
        Returns:
            List of plugins
        """
        plugins = list(self.plugins.values())
        
        if enabled_only:
            plugins = [p for p in plugins if p.enabled]
        
        if category:
            plugins = [p for p in plugins if p.category == category]
        
        return plugins
    
    def list_agents(self, category: Optional[str] = None) -> List[AgentDefinition]:
        """
        List all agents, optionally filtered by category
        
        Args:
            category: Optional category filter
            
        Returns:
            List of agents
        """
        agents = list(self.agents.values())
        
        # TODO: Add category filtering when agents have category field
        
        return agents
    
    def list_skills(self, category: Optional[str] = None) -> List[SkillMetadata]:
        """
        List all skills, optionally filtered by category
        
        Args:
            category: Optional category filter
            
        Returns:
            List of skills
        """
        skills = list(self.skills.values())
        
        if category:
            skills = [s for s in skills if s.category == category]
        
        return skills
    
    def resolve_dependencies(self, plugin_name: str) -> List[str]:
        """
        Resolve plugin dependencies and return load order
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            List of plugin names in load order
        """
        visited = set()
        load_order = []
        
        def visit(name: str):
            if name in visited:
                return
            
            visited.add(name)
            
            # Visit dependencies first
            if name in self.dependency_graph:
                for dep in self.dependency_graph[name]:
                    visit(dep)
            
            load_order.append(name)
        
        visit(plugin_name)
        return load_order
    
    def load_plugins_from_directory(self) -> int:
        """
        Load all plugins from the plugins directory
        
        Returns:
            Number of plugins loaded
        """
        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory does not exist: {self.plugins_dir}")
            return 0
        
        loaded_count = 0
        
        # TODO: Implement plugin loading from directory
        # This will scan for plugin definition files and load them
        
        logger.info(f"Loaded {loaded_count} plugins from {self.plugins_dir}")
        return loaded_count
    
    def export_registry(self, output_path: Path) -> bool:
        """
        Export registry to JSON file
        
        Args:
            output_path: Path to output file
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            registry_data = {
                "plugins": {name: plugin.dict() for name, plugin in self.plugins.items()},
                "agents": {name: agent.dict() for name, agent in self.agents.items()},
                "skills": {name: skill.dict() for name, skill in self.skills.items()},
                "tools": {name: tool.dict() for name, tool in self.tools.items()},
                "workflows": {name: workflow.dict() for name, workflow in self.workflows.items()}
            }
            
            with open(output_path, 'w') as f:
                json.dump(registry_data, f, indent=2, default=str)
            
            logger.info(f"Registry exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export registry: {str(e)}")
            return False


# Global registry instance
_registry: Optional[PluginRegistry] = None


def get_registry() -> PluginRegistry:
    """
    Get the global plugin registry instance
    
    Returns:
        Plugin registry instance
    """
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry
