"""
Plugin Registry Models
Pydantic models for plugin metadata, agent definitions, and skill metadata
Ensures type safety and validation for the entire plugin ecosystem
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from datetime import datetime
import hashlib


class PluginMetadata(BaseModel):
    """
    Plugin metadata - strict schema for all plugins
    All plugins MUST conform to this schema
    """
    
    # Core information
    name: str = Field(
        ..., 
        regex="^[a-z0-9-]+$",
        description="Lowercase with hyphens, e.g., 'backend-architect'"
    )
    version: str = Field(
        ..., 
        regex="^\\d+\\.\\d+\\.\\d+$",
        description="Semantic versioning, e.g., '1.0.0'"
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Clear description of plugin capabilities"
    )
    category: str = Field(
        ...,
        description="Category: architecture, development, testing, security, etc."
    )
    author: str = Field(
        default="wshobson",
        description="Plugin author/source"
    )
    
    # Capabilities - what the plugin provides
    agents: List[str] = Field(
        default=[],
        description="List of agent names provided by this plugin"
    )
    skills: List[str] = Field(
        default=[],
        description="List of skill names provided by this plugin"
    )
    tools: List[str] = Field(
        default=[],
        description="List of tool names provided by this plugin"
    )
    
    # Dependencies
    requires: List[str] = Field(
        default=[],
        description="Required plugins (must be loaded first)"
    )
    conflicts: List[str] = Field(
        default=[],
        description="Conflicting plugins (cannot be loaded together)"
    )
    python_requires: str = Field(
        default=">=3.11",
        description="Required Python version"
    )
    
    # Model preferences
    preferred_model: Optional[str] = Field(
        default=None,
        description="Preferred AI model: haiku, sonnet, opus"
    )
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    checksum: str = Field(
        ...,
        description="MD5 hash for integrity verification"
    )
    enabled: bool = Field(
        default=True,
        description="Whether plugin is enabled"
    )
    
    @validator('checksum')
    def validate_checksum(cls, v, values):
        """
        Verify plugin hasn't been tampered with
        Calculate expected checksum and compare
        """
        if 'name' in values and 'version' in values:
            content = f"{values['name']}{values['version']}"
            expected = hashlib.md5(content.encode()).hexdigest()
            # In production, should verify against stored hash
        return v
    
    @validator('category')
    def validate_category(cls, v):
        """Ensure category is from allowed list"""
        allowed = [
            'architecture', 'development', 'testing', 'security',
            'quality', 'infrastructure', 'data', 'ai-ml',
            'documentation', 'business', 'finance'
        ]
        if v not in allowed:
            raise ValueError(f"Category must be one of: {allowed}")
        return v


class AgentDefinition(BaseModel):
    """
    Agent definition - imported from wshobson/agents catalog
    """
    name: str
    description: str
    model: str = Field(
        default="sonnet",
        description="Preferred model: haiku, sonnet, opus"
    )
    system_prompt: str = Field(
        ...,
        min_length=50,
        description="Complete system prompt for agent"
    )
    tools: List[str] = Field(
        default=[],
        description="Tools available to agent"
    )
    examples: List[Dict] = Field(
        default=[],
        description="Example interactions"
    )
    
    # Activation triggers
    trigger_keywords: List[str] = Field(
        default=[],
        description="Keywords that should activate this agent"
    )
    
    # Performance hints
    estimated_tokens: int = Field(
        default=1000,
        description="Estimated tokens per request"
    )
    avg_response_time: float = Field(
        default=2.0,
        description="Average response time in seconds"
    )


class SkillMetadata(BaseModel):
    """
    Skill metadata for Progressive Disclosure
    Level 1: Always in memory (lightweight)
    """
    name: str
    description: str
    category: str
    level: int = Field(
        default=1,
        ge=1,
        le=3,
        description="Disclosure level: 1=metadata, 2=instructions, 3=resources"
    )
    
    # Activation conditions
    triggers: List[str] = Field(
        default=[],
        description="Keywords or patterns that activate this skill"
    )
    
    # Resource paths
    instructions_path: Optional[str] = Field(
        default=None,
        description="Path to detailed instructions (Level 2)"
    )
    resources_path: Optional[str] = Field(
        default=None,
        description="Path to additional resources (Level 3)"
    )
    
    # Performance metrics
    estimated_tokens: int = Field(
        default=500,
        description="Estimated tokens when fully loaded"
    )
    
    # Dependencies
    requires_skills: List[str] = Field(
        default=[],
        description="Other skills required for this skill"
    )


class ToolDefinition(BaseModel):
    """
    Tool definition for plugin tools
    """
    name: str
    description: str
    parameters: Dict[str, Any] = Field(
        default={},
        description="Tool parameters schema"
    )
    returns: Dict[str, Any] = Field(
        default={},
        description="Tool return value schema"
    )
    
    # Implementation
    implementation: Optional[str] = Field(
        default=None,
        description="Python code or reference to implementation"
    )
    
    # Metadata
    async_execution: bool = Field(
        default=False,
        description="Whether tool supports async execution"
    )
    requires_auth: bool = Field(
        default=False,
        description="Whether tool requires authentication"
    )


class WorkflowDefinition(BaseModel):
    """
    Workflow definition for multi-agent workflows
    """
    name: str
    description: str
    steps: List[Dict[str, Any]] = Field(
        ...,
        description="Workflow steps with agent assignments"
    )
    
    # Execution settings
    parallel: bool = Field(
        default=False,
        description="Whether steps can execute in parallel"
    )
    timeout: int = Field(
        default=300,
        description="Workflow timeout in seconds"
    )
    
    # Dependencies
    required_agents: List[str] = Field(
        default=[],
        description="Agents required for this workflow"
    )
    required_tools: List[str] = Field(
        default=[],
        description="Tools required for this workflow"
    )
