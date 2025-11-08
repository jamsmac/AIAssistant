"""
FractalAgents Module
Self-organizing AI agent system with collective intelligence
"""
from .base_agent import FractalAgent
from .orchestrator import FractalAgentOrchestrator
from .memory import CollectiveMemory
from .skills import SkillsManager
from .connectors import ConnectorManager

__all__ = [
    'FractalAgent',
    'FractalAgentOrchestrator',
    'CollectiveMemory',
    'SkillsManager',
    'ConnectorManager'
]
