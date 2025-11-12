"""
Enhanced Fractal Agent - v3.0
Extends the base Fractal Agent with Plugin Registry integration,
Progressive Disclosure skills, and LLM Router support
"""

import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from .base_agent import FractalAgent
from agents.registry import get_registry, AgentDefinition, SkillMetadata
from agents.routing.llm_router import LLMRouter
from agents.skills.registry import SkillsRegistry

logger = logging.getLogger(__name__)


class EnhancedFractalAgent(FractalAgent):
    """
    Enhanced Fractal Agent with v3.0 capabilities:
    - Plugin Registry integration
    - Progressive Disclosure skills
    - Intelligent LLM routing
    - Dynamic agent loading from catalog
    """
    
    def __init__(
        self,
        agent_id: str,
        db,
        anthropic_api_key: Optional[str] = None,
        use_plugin_registry: bool = True,
        use_llm_router: bool = True
    ):
        """
        Initialize Enhanced Fractal Agent
        
        Args:
            agent_id: Agent identifier
            db: Database instance
            anthropic_api_key: Anthropic API key
            use_plugin_registry: Enable Plugin Registry integration
            use_llm_router: Enable intelligent LLM routing
        """
        super().__init__(agent_id, db, anthropic_api_key)
        
        # v3.0 components
        self.use_plugin_registry = use_plugin_registry
        self.use_llm_router = use_llm_router
        
        # Initialize registries
        self.plugin_registry = get_registry() if use_plugin_registry else None
        self.skills_registry = SkillsRegistry() if use_plugin_registry else None
        self.llm_router = LLMRouter() if use_llm_router else None
        
        # Enhanced capabilities
        self.catalog_agents: Dict[str, AgentDefinition] = {}
        self.active_skills: Dict[str, SkillMetadata] = {}
        
        logger.info(
            f"Enhanced Fractal Agent initialized: "
            f"plugin_registry={use_plugin_registry}, "
            f"llm_router={use_llm_router}"
        )
    
    async def initialize(self):
        """Enhanced initialization with plugin registry"""
        # Call parent initialization
        await super().initialize()
        
        # Load agents from plugin registry
        if self.plugin_registry:
            await self._load_catalog_agents()
        
        # Load skills from skills registry
        if self.skills_registry:
            await self._load_skills()
        
        logger.info(
            f"Enhanced Agent {self.data['name']} initialized: "
            f"{len(self.catalog_agents)} catalog agents, "
            f"{len(self.active_skills)} active skills"
        )
    
    async def _load_catalog_agents(self):
        """Load agents from plugin registry catalog"""
        try:
            agents = self.plugin_registry.list_agents()
            
            for agent in agents:
                self.catalog_agents[agent.name] = agent
            
            logger.info(f"Loaded {len(agents)} agents from catalog")
            
        except Exception as e:
            logger.error(f"Failed to load catalog agents: {str(e)}")
    
    async def _load_skills(self):
        """Load skills from skills registry"""
        try:
            # Load Level 1 skills (metadata only - always in memory)
            skills = self.skills_registry.list_skills(level=1)
            
            for skill in skills:
                self.active_skills[skill.name] = skill
            
            logger.info(f"Loaded {len(skills)} Level 1 skills")
            
        except Exception as e:
            logger.error(f"Failed to load skills: {str(e)}")
    
    async def can_handle(self, task: Dict) -> Tuple[bool, float]:
        """
        Enhanced task handling check with catalog agents and skills
        
        Args:
            task: Task dictionary
            
        Returns:
            (can_handle, confidence)
        """
        # Check base Fractal Agent capabilities
        can_handle_base, confidence_base = await super().can_handle(task)
        
        # Check catalog agents
        if self.plugin_registry:
            catalog_confidence = await self._check_catalog_agents(task)
            confidence_base = max(confidence_base, catalog_confidence)
        
        # Check skills
        if self.skills_registry:
            skills_confidence = await self._check_skills(task)
            confidence_base = max(confidence_base, skills_confidence)
        
        return confidence_base > 0.3, confidence_base
    
    async def _check_catalog_agents(self, task: Dict) -> float:
        """
        Check if any catalog agent can handle the task
        
        Args:
            task: Task dictionary
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        task_description = task.get('description', '').lower()
        max_confidence = 0.0
        
        for agent_name, agent_def in self.catalog_agents.items():
            # Check trigger keywords
            matches = sum(
                1 for keyword in agent_def.trigger_keywords
                if keyword.lower() in task_description
            )
            
            if matches > 0:
                # Calculate confidence based on keyword matches
                confidence = min(0.9, 0.5 + (matches * 0.1))
                max_confidence = max(max_confidence, confidence)
        
        return max_confidence
    
    async def _check_skills(self, task: Dict) -> float:
        """
        Check if any skill can handle the task
        
        Args:
            task: Task dictionary
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        task_description = task.get('description', '').lower()
        max_confidence = 0.0
        
        for skill_name, skill in self.active_skills.items():
            # Check trigger keywords
            matches = sum(
                1 for trigger in skill.triggers
                if trigger.lower() in task_description
            )
            
            if matches > 0:
                confidence = min(0.8, 0.4 + (matches * 0.1))
                max_confidence = max(max_confidence, confidence)
        
        return max_confidence
    
    async def execute_task(self, task: Dict) -> Dict:
        """
        Enhanced task execution with LLM routing
        
        Args:
            task: Task dictionary
            
        Returns:
            Result dictionary
        """
        if not self._initialized:
            await self.initialize()
        
        # Use LLM Router to select best model
        if self.llm_router:
            task = await self._enhance_task_with_routing(task)
        
        # Activate required skills (Progressive Disclosure)
        if self.skills_registry:
            await self._activate_required_skills(task)
        
        # Execute task using parent implementation
        result = await super().execute_task(task)
        
        return result
    
    async def _enhance_task_with_routing(self, task: Dict) -> Dict:
        """
        Enhance task with intelligent model routing
        
        Args:
            task: Task dictionary
            
        Returns:
            Enhanced task with model selection
        """
        try:
            # Analyze task complexity
            complexity = await self.llm_router.analyze_complexity(
                task.get('description', '')
            )
            
            # Select best model
            model = await self.llm_router.select_model(complexity)
            
            # Add to task
            task['selected_model'] = model
            task['complexity'] = complexity
            
            logger.info(
                f"LLM Router selected: {model} "
                f"(complexity: {complexity})"
            )
            
        except Exception as e:
            logger.error(f"LLM routing failed: {str(e)}")
        
        return task
    
    async def _activate_required_skills(self, task: Dict):
        """
        Activate required skills using Progressive Disclosure
        
        Args:
            task: Task dictionary
        """
        try:
            task_description = task.get('description', '').lower()
            
            # Find skills that should be activated
            skills_to_activate = []
            
            for skill_name, skill in self.active_skills.items():
                for trigger in skill.triggers:
                    if trigger.lower() in task_description:
                        skills_to_activate.append(skill_name)
                        break
            
            # Activate skills (load Level 2 and 3 resources)
            for skill_name in skills_to_activate:
                await self.skills_registry.activate_skill(skill_name)
                logger.info(f"Activated skill: {skill_name}")
            
        except Exception as e:
            logger.error(f"Skill activation failed: {str(e)}")
    
    async def get_agent_from_catalog(self, agent_name: str) -> Optional[AgentDefinition]:
        """
        Get agent definition from catalog
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent definition or None
        """
        if not self.plugin_registry:
            return None
        
        return self.plugin_registry.get_agent(agent_name)
    
    async def execute_catalog_agent(
        self,
        agent_name: str,
        task: Dict
    ) -> Dict:
        """
        Execute a catalog agent on a task
        
        Args:
            agent_name: Name of the catalog agent
            task: Task dictionary
            
        Returns:
            Result dictionary
        """
        agent_def = await self.get_agent_from_catalog(agent_name)
        
        if not agent_def:
            return {
                'success': False,
                'error': f'Agent {agent_name} not found in catalog'
            }
        
        try:
            # Use the agent's system prompt and preferred model
            result = await self._execute_with_agent_def(agent_def, task)
            return result
            
        except Exception as e:
            logger.error(f"Catalog agent execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _execute_with_agent_def(
        self,
        agent_def: AgentDefinition,
        task: Dict
    ) -> Dict:
        """
        Execute task using agent definition
        
        Args:
            agent_def: Agent definition
            task: Task dictionary
            
        Returns:
            Result dictionary
        """
        # TODO: Implement actual execution using agent's system prompt
        # This will use the Anthropic API with the agent's configuration
        
        logger.info(
            f"Executing with catalog agent: {agent_def.name} "
            f"(model: {agent_def.model})"
        )
        
        return {
            'success': True,
            'agent_name': agent_def.name,
            'model': agent_def.model,
            'result': 'Catalog agent execution not yet fully implemented'
        }
