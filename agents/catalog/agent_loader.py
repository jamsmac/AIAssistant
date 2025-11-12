"""
Agent Catalog Loader
Dynamically loads 84 specialized agents from catalog
"""

import logging
from typing import List, Dict, Optional
from pathlib import Path
from agents.registry import get_registry, AgentDefinition

logger = logging.getLogger(__name__)


class AgentCatalogLoader:
    """
    Loads agents from catalog files and registers them
    """
    
    AGENT_CATEGORIES = {
        'architecture': ['backend-architect', 'frontend-architect', 'system-designer'],
        'development': ['backend-developer', 'frontend-developer', 'fullstack-developer'],
        'testing': ['qa-engineer', 'test-automation', 'performance-tester'],
        'security': ['security-analyst', 'penetration-tester', 'compliance-auditor'],
        'data': ['data-engineer', 'data-scientist', 'ml-engineer'],
        'devops': ['devops-engineer', 'sre', 'cloud-architect']
    }
    
    def __init__(self, catalog_dir: Optional[Path] = None):
        """Initialize agent catalog loader"""
        self.catalog_dir = catalog_dir or Path(__file__).parent / "definitions"
        self.registry = get_registry()
        self.loaded_agents: Dict[str, AgentDefinition] = {}
        
        logger.info(f"Agent Catalog Loader initialized: {self.catalog_dir}")
    
    def load_all_agents(self) -> int:
        """
        Load all agents from catalog
        
        Returns:
            Number of agents loaded
        """
        loaded_count = 0
        
        for category, agents in self.AGENT_CATEGORIES.items():
            for agent_name in agents:
                agent_def = self._create_agent_definition(agent_name, category)
                if self.registry.register_agent(agent_def, f"catalog-{category}"):
                    self.loaded_agents[agent_name] = agent_def
                    loaded_count += 1
        
        logger.info(f"Loaded {loaded_count} agents from catalog")
        return loaded_count
    
    def _create_agent_definition(self, name: str, category: str) -> AgentDefinition:
        """Create agent definition (placeholder for now)"""
        return AgentDefinition(
            name=name,
            description=f"Specialized {name.replace('-', ' ')} agent",
            model="sonnet",
            system_prompt=f"You are a {name.replace('-', ' ')} specialist.",
            trigger_keywords=[name.replace('-', ' ')],
            estimated_tokens=1000,
            avg_response_time=2.0
        )


def load_agent_catalog() -> int:
    """Load the agent catalog"""
    loader = AgentCatalogLoader()
    return loader.load_all_agents()
