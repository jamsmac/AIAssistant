"""
Plugin Registry Validator
Validates plugins, agents, skills, and tools for correctness and security
"""

import logging
import re
from typing import Tuple, Optional, List
from .models import (
    PluginMetadata,
    AgentDefinition,
    SkillMetadata,
    ToolDefinition,
    WorkflowDefinition
)

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class PluginValidator:
    """
    Validator for plugin registry components
    Ensures all registered items meet quality and security standards
    """
    
    @staticmethod
    def validate_plugin(plugin: PluginMetadata) -> Tuple[bool, Optional[str]]:
        """
        Validate plugin metadata
        
        Args:
            plugin: Plugin metadata to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Name validation
            if not re.match(r'^[a-z0-9-]+$', plugin.name):
                return False, "Plugin name must be lowercase with hyphens only"
            
            # Version validation
            if not re.match(r'^\d+\.\d+\.\d+$', plugin.version):
                return False, "Version must follow semantic versioning (e.g., 1.0.0)"
            
            # Description validation
            if len(plugin.description) < 10:
                return False, "Description must be at least 10 characters"
            
            if len(plugin.description) > 500:
                return False, "Description must not exceed 500 characters"
            
            # Category validation
            allowed_categories = [
                'architecture', 'development', 'testing', 'security',
                'quality', 'infrastructure', 'data', 'ai-ml',
                'documentation', 'business', 'finance'
            ]
            if plugin.category not in allowed_categories:
                return False, f"Category must be one of: {', '.join(allowed_categories)}"
            
            # Dependency validation
            if plugin.name in plugin.requires:
                return False, "Plugin cannot depend on itself"
            
            # Conflict validation
            if plugin.name in plugin.conflicts:
                return False, "Plugin cannot conflict with itself"
            
            # Check for circular dependencies in requires and conflicts
            if set(plugin.requires) & set(plugin.conflicts):
                return False, "Plugin cannot both require and conflict with the same plugin"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Plugin validation error: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def validate_agent(agent: AgentDefinition) -> Tuple[bool, Optional[str]]:
        """
        Validate agent definition
        
        Args:
            agent: Agent definition to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Name validation
            if not agent.name or len(agent.name) < 3:
                return False, "Agent name must be at least 3 characters"
            
            # Description validation
            if not agent.description or len(agent.description) < 10:
                return False, "Agent description must be at least 10 characters"
            
            # System prompt validation
            if not agent.system_prompt or len(agent.system_prompt) < 50:
                return False, "System prompt must be at least 50 characters"
            
            # Check for potentially dangerous patterns in system prompt
            dangerous_patterns = [
                "ignore previous instructions",
                "disregard all",
                "forget everything",
                "system override"
            ]
            system_prompt_lower = agent.system_prompt.lower()
            for pattern in dangerous_patterns:
                if pattern in system_prompt_lower:
                    logger.warning(f"Agent {agent.name} contains potentially dangerous pattern: {pattern}")
            
            # Model validation
            allowed_models = ["haiku", "sonnet", "opus", "gpt-4", "gpt-3.5-turbo", "gemini"]
            if agent.model not in allowed_models:
                return False, f"Model must be one of: {', '.join(allowed_models)}"
            
            # Performance metrics validation
            if agent.estimated_tokens < 0:
                return False, "Estimated tokens must be non-negative"
            
            if agent.avg_response_time < 0:
                return False, "Average response time must be non-negative"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Agent validation error: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def validate_skill(skill: SkillMetadata) -> Tuple[bool, Optional[str]]:
        """
        Validate skill metadata
        
        Args:
            skill: Skill metadata to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Name validation
            if not skill.name or len(skill.name) < 3:
                return False, "Skill name must be at least 3 characters"
            
            # Description validation
            if not skill.description or len(skill.description) < 10:
                return False, "Skill description must be at least 10 characters"
            
            # Level validation
            if skill.level not in [1, 2, 3]:
                return False, "Skill level must be 1, 2, or 3"
            
            # Path validation for levels 2 and 3
            if skill.level >= 2 and not skill.instructions_path:
                return False, "Level 2+ skills must have instructions_path"
            
            if skill.level == 3 and not skill.resources_path:
                return False, "Level 3 skills must have resources_path"
            
            # Circular dependency check
            if skill.name in skill.requires_skills:
                return False, "Skill cannot depend on itself"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Skill validation error: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def validate_tool(tool: ToolDefinition) -> Tuple[bool, Optional[str]]:
        """
        Validate tool definition
        
        Args:
            tool: Tool definition to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Name validation
            if not tool.name or len(tool.name) < 3:
                return False, "Tool name must be at least 3 characters"
            
            # Description validation
            if not tool.description or len(tool.description) < 10:
                return False, "Tool description must be at least 10 characters"
            
            # Parameters validation
            if not isinstance(tool.parameters, dict):
                return False, "Tool parameters must be a dictionary"
            
            # Returns validation
            if not isinstance(tool.returns, dict):
                return False, "Tool returns must be a dictionary"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Tool validation error: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def validate_workflow(workflow: WorkflowDefinition) -> Tuple[bool, Optional[str]]:
        """
        Validate workflow definition
        
        Args:
            workflow: Workflow definition to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Name validation
            if not workflow.name or len(workflow.name) < 3:
                return False, "Workflow name must be at least 3 characters"
            
            # Description validation
            if not workflow.description or len(workflow.description) < 10:
                return False, "Workflow description must be at least 10 characters"
            
            # Steps validation
            if not workflow.steps or len(workflow.steps) == 0:
                return False, "Workflow must have at least one step"
            
            # Validate each step has required fields
            for i, step in enumerate(workflow.steps):
                if not isinstance(step, dict):
                    return False, f"Step {i} must be a dictionary"
                
                if 'agent' not in step and 'action' not in step:
                    return False, f"Step {i} must have either 'agent' or 'action' field"
            
            # Timeout validation
            if workflow.timeout <= 0:
                return False, "Workflow timeout must be positive"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Workflow validation error: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def validate_all(
        plugin: Optional[PluginMetadata] = None,
        agent: Optional[AgentDefinition] = None,
        skill: Optional[SkillMetadata] = None,
        tool: Optional[ToolDefinition] = None,
        workflow: Optional[WorkflowDefinition] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate multiple components at once
        
        Args:
            plugin: Optional plugin to validate
            agent: Optional agent to validate
            skill: Optional skill to validate
            tool: Optional tool to validate
            workflow: Optional workflow to validate
            
        Returns:
            Tuple of (all_valid, list_of_errors)
        """
        errors = []
        
        if plugin:
            is_valid, error = PluginValidator.validate_plugin(plugin)
            if not is_valid:
                errors.append(f"Plugin validation failed: {error}")
        
        if agent:
            is_valid, error = PluginValidator.validate_agent(agent)
            if not is_valid:
                errors.append(f"Agent validation failed: {error}")
        
        if skill:
            is_valid, error = PluginValidator.validate_skill(skill)
            if not is_valid:
                errors.append(f"Skill validation failed: {error}")
        
        if tool:
            is_valid, error = PluginValidator.validate_tool(tool)
            if not is_valid:
                errors.append(f"Tool validation failed: {error}")
        
        if workflow:
            is_valid, error = PluginValidator.validate_workflow(workflow)
            if not is_valid:
                errors.append(f"Workflow validation failed: {error}")
        
        return len(errors) == 0, errors
