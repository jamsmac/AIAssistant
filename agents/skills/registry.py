"""
Skills Registry - Progressive Disclosure System
Three-level skill loading system to conserve context:
- Level 1: Metadata (always in memory) - ~50 tokens per skill
- Level 2: Instructions (load on activation) - ~500 tokens per skill
- Level 3: Resources (load on use) - ~2000 tokens per skill

This achieves up to 90% context savings by loading only what's needed
"""

import logging
from typing import Dict, List, Optional, Set
from pathlib import Path
import json
from agents.registry.models import SkillMetadata

logger = logging.getLogger(__name__)


class SkillsRegistry:
    """
    Progressive Disclosure Skills Registry
    Manages skill loading across three disclosure levels
    """
    
    def __init__(self, skills_dir: Optional[Path] = None):
        """
        Initialize Skills Registry
        
        Args:
            skills_dir: Directory containing skill definitions
        """
        self.skills_dir = skills_dir or Path(__file__).parent / "definitions"
        
        # Level 1: Metadata (always loaded)
        self.metadata: Dict[str, SkillMetadata] = {}
        
        # Level 2: Instructions (loaded on activation)
        self.instructions: Dict[str, str] = {}
        
        # Level 3: Resources (loaded on use)
        self.resources: Dict[str, Dict] = {}
        
        # Track active skills
        self.active_skills: Set[str] = set()
        
        # Statistics
        self.stats = {
            'total_skills': 0,
            'active_skills': 0,
            'level_2_loaded': 0,
            'level_3_loaded': 0,
            'context_saved': 0  # Estimated tokens saved
        }
        
        logger.info(f"Skills Registry initialized with skills_dir: {self.skills_dir}")
    
    def register_skill(self, skill: SkillMetadata) -> bool:
        """
        Register a new skill (Level 1 - metadata only)
        
        Args:
            skill: Skill metadata
            
        Returns:
            True if registration successful
        """
        try:
            if skill.name in self.metadata:
                logger.warning(f"Skill {skill.name} already registered, updating...")
            
            # Store metadata (Level 1)
            self.metadata[skill.name] = skill
            self.stats['total_skills'] = len(self.metadata)
            
            logger.info(f"Skill {skill.name} registered (Level 1)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register skill {skill.name}: {str(e)}")
            return False
    
    async def activate_skill(self, skill_name: str) -> bool:
        """
        Activate a skill (load Level 2 - instructions)
        
        Args:
            skill_name: Name of the skill to activate
            
        Returns:
            True if activation successful
        """
        if skill_name not in self.metadata:
            logger.error(f"Skill {skill_name} not found in registry")
            return False
        
        if skill_name in self.active_skills:
            logger.debug(f"Skill {skill_name} already active")
            return True
        
        try:
            skill = self.metadata[skill_name]
            
            # Load Level 2: Instructions
            if skill.instructions_path:
                instructions = await self._load_instructions(skill.instructions_path)
                self.instructions[skill_name] = instructions
                self.stats['level_2_loaded'] += 1
            
            # Mark as active
            self.active_skills.add(skill_name)
            self.stats['active_skills'] = len(self.active_skills)
            
            logger.info(f"Skill {skill_name} activated (Level 2 loaded)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to activate skill {skill_name}: {str(e)}")
            return False
    
    async def load_resources(self, skill_name: str) -> Optional[Dict]:
        """
        Load skill resources (Level 3)
        
        Args:
            skill_name: Name of the skill
            
        Returns:
            Resources dictionary or None
        """
        if skill_name not in self.metadata:
            logger.error(f"Skill {skill_name} not found in registry")
            return None
        
        if skill_name in self.resources:
            logger.debug(f"Resources for {skill_name} already loaded")
            return self.resources[skill_name]
        
        try:
            skill = self.metadata[skill_name]
            
            # Load Level 3: Resources
            if skill.resources_path:
                resources = await self._load_resources(skill.resources_path)
                self.resources[skill_name] = resources
                self.stats['level_3_loaded'] += 1
                
                logger.info(f"Resources loaded for skill {skill_name} (Level 3)")
                return resources
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to load resources for {skill_name}: {str(e)}")
            return None
    
    def deactivate_skill(self, skill_name: str) -> bool:
        """
        Deactivate a skill (unload Level 2 and 3)
        
        Args:
            skill_name: Name of the skill to deactivate
            
        Returns:
            True if deactivation successful
        """
        if skill_name not in self.active_skills:
            logger.debug(f"Skill {skill_name} not active")
            return True
        
        try:
            # Unload Level 2
            if skill_name in self.instructions:
                del self.instructions[skill_name]
                self.stats['level_2_loaded'] -= 1
            
            # Unload Level 3
            if skill_name in self.resources:
                del self.resources[skill_name]
                self.stats['level_3_loaded'] -= 1
            
            # Remove from active set
            self.active_skills.remove(skill_name)
            self.stats['active_skills'] = len(self.active_skills)
            
            logger.info(f"Skill {skill_name} deactivated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deactivate skill {skill_name}: {str(e)}")
            return False
    
    def get_skill_metadata(self, skill_name: str) -> Optional[SkillMetadata]:
        """Get skill metadata (Level 1)"""
        return self.metadata.get(skill_name)
    
    def get_skill_instructions(self, skill_name: str) -> Optional[str]:
        """Get skill instructions (Level 2) if loaded"""
        return self.instructions.get(skill_name)
    
    def get_skill_resources(self, skill_name: str) -> Optional[Dict]:
        """Get skill resources (Level 3) if loaded"""
        return self.resources.get(skill_name)
    
    def list_skills(
        self,
        category: Optional[str] = None,
        level: Optional[int] = None
    ) -> List[SkillMetadata]:
        """
        List skills, optionally filtered
        
        Args:
            category: Optional category filter
            level: Optional level filter (1, 2, or 3)
            
        Returns:
            List of skill metadata
        """
        skills = list(self.metadata.values())
        
        if category:
            skills = [s for s in skills if s.category == category]
        
        if level:
            skills = [s for s in skills if s.level == level]
        
        return skills
    
    def list_active_skills(self) -> List[str]:
        """Get list of currently active skill names"""
        return list(self.active_skills)
    
    def get_statistics(self) -> Dict:
        """
        Get registry statistics
        
        Returns:
            Statistics dictionary
        """
        # Calculate context savings
        # Assume: Level 1 = 50 tokens, Level 2 = 500 tokens, Level 3 = 2000 tokens
        total_possible_tokens = self.stats['total_skills'] * (50 + 500 + 2000)
        
        actual_tokens = (
            self.stats['total_skills'] * 50 +  # All Level 1
            self.stats['level_2_loaded'] * 500 +  # Active Level 2
            self.stats['level_3_loaded'] * 2000  # Used Level 3
        )
        
        if total_possible_tokens > 0:
            context_saved_pct = (1 - actual_tokens / total_possible_tokens) * 100
        else:
            context_saved_pct = 0
        
        self.stats['context_saved'] = int(context_saved_pct)
        
        return self.stats.copy()
    
    async def _load_instructions(self, path: str) -> str:
        """
        Load instructions from file
        
        Args:
            path: Path to instructions file
            
        Returns:
            Instructions text
        """
        try:
            file_path = self.skills_dir / path
            
            if not file_path.exists():
                logger.warning(f"Instructions file not found: {file_path}")
                return ""
            
            with open(file_path, 'r') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"Failed to load instructions from {path}: {str(e)}")
            return ""
    
    async def _load_resources(self, path: str) -> Dict:
        """
        Load resources from file
        
        Args:
            path: Path to resources file
            
        Returns:
            Resources dictionary
        """
        try:
            file_path = self.skills_dir / path
            
            if not file_path.exists():
                logger.warning(f"Resources file not found: {file_path}")
                return {}
            
            with open(file_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Failed to load resources from {path}: {str(e)}")
            return {}
    
    def load_skills_from_directory(self) -> int:
        """
        Load all skills from the skills directory
        
        Returns:
            Number of skills loaded
        """
        if not self.skills_dir.exists():
            logger.warning(f"Skills directory does not exist: {self.skills_dir}")
            self.skills_dir.mkdir(parents=True, exist_ok=True)
            return 0
        
        loaded_count = 0
        
        # TODO: Implement skill loading from directory
        # This will scan for skill definition files and load them
        
        logger.info(f"Loaded {loaded_count} skills from {self.skills_dir}")
        return loaded_count


# Global skills registry instance
_skills_registry: Optional[SkillsRegistry] = None


def get_skills_registry() -> SkillsRegistry:
    """
    Get the global skills registry instance
    
    Returns:
        Skills registry instance
    """
    global _skills_registry
    if _skills_registry is None:
        _skills_registry = SkillsRegistry()
    return _skills_registry
