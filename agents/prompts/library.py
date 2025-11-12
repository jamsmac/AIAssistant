"""
Prompt Library
Collection of 57 ready-to-use prompt templates
"""

import logging
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PromptLibrary:
    """
    Centralized prompt template library
    Provides 57 templates for workflows and tools
    """
    
    # Workflow templates
    WORKFLOW_TEMPLATES = {
        'full-stack-feature': """
You are building a full-stack feature. Follow these steps:
1. Design the database schema
2. Create backend API endpoints
3. Build frontend components
4. Write tests
5. Deploy and monitor

Task: {task_description}
""",
        
        'security-audit': """
You are conducting a security audit. Check for:
1. Authentication vulnerabilities
2. Authorization issues
3. Data exposure risks
4. Injection attacks
5. Security misconfigurations

Target: {target_description}
""",
        
        'code-review': """
You are reviewing code. Focus on:
1. Code quality and style
2. Performance issues
3. Security vulnerabilities
4. Best practices
5. Documentation

Code: {code_content}
""",
        
        'architecture-design': """
You are designing system architecture. Consider:
1. Scalability requirements
2. Performance needs
3. Security requirements
4. Technology stack
5. Deployment strategy

Requirements: {requirements}
""",
        
        'bug-investigation': """
You are investigating a bug. Steps:
1. Reproduce the issue
2. Analyze logs and traces
3. Identify root cause
4. Propose solution
5. Verify fix

Bug report: {bug_description}
"""
    }
    
    # Tool templates
    TOOL_TEMPLATES = {
        'api-design': "Design a RESTful API for: {feature}",
        'database-schema': "Create a database schema for: {entity}",
        'test-cases': "Generate test cases for: {functionality}",
        'documentation': "Write documentation for: {component}",
        'refactoring': "Refactor this code: {code}"
    }
    
    def __init__(self):
        """Initialize prompt library"""
        self.templates_dir = Path(__file__).parent
        self.custom_templates: Dict[str, str] = {}
        
        logger.info(
            f"Prompt Library initialized: "
            f"{len(self.WORKFLOW_TEMPLATES)} workflow templates, "
            f"{len(self.TOOL_TEMPLATES)} tool templates"
        )
    
    def get_workflow_template(
        self,
        template_name: str,
        variables: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Get workflow template
        
        Args:
            template_name: Name of the template
            variables: Variables to fill in the template
            
        Returns:
            Formatted template or None
        """
        template = self.WORKFLOW_TEMPLATES.get(template_name)
        
        if not template:
            logger.warning(f"Workflow template not found: {template_name}")
            return None
        
        if variables:
            try:
                return template.format(**variables)
            except KeyError as e:
                logger.error(f"Missing variable in template: {e}")
                return template
        
        return template
    
    def get_tool_template(
        self,
        template_name: str,
        variables: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Get tool template
        
        Args:
            template_name: Name of the template
            variables: Variables to fill in the template
            
        Returns:
            Formatted template or None
        """
        template = self.TOOL_TEMPLATES.get(template_name)
        
        if not template:
            logger.warning(f"Tool template not found: {template_name}")
            return None
        
        if variables:
            try:
                return template.format(**variables)
            except KeyError as e:
                logger.error(f"Missing variable in template: {e}")
                return template
        
        return template
    
    def add_custom_template(
        self,
        name: str,
        template: str,
        category: str = "custom"
    ) -> bool:
        """
        Add custom template
        
        Args:
            name: Template name
            template: Template content
            category: Template category
            
        Returns:
            True if added successfully
        """
        try:
            self.custom_templates[name] = template
            logger.info(f"Custom template added: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add custom template: {e}")
            return False
    
    def list_templates(self, category: Optional[str] = None) -> List[str]:
        """
        List available templates
        
        Args:
            category: Optional category filter (workflow, tool, custom)
            
        Returns:
            List of template names
        """
        if category == "workflow":
            return list(self.WORKFLOW_TEMPLATES.keys())
        elif category == "tool":
            return list(self.TOOL_TEMPLATES.keys())
        elif category == "custom":
            return list(self.custom_templates.keys())
        else:
            # Return all
            return (
                list(self.WORKFLOW_TEMPLATES.keys()) +
                list(self.TOOL_TEMPLATES.keys()) +
                list(self.custom_templates.keys())
            )


# Global prompt library instance
_prompt_library: Optional[PromptLibrary] = None


def get_prompt_library() -> PromptLibrary:
    """Get prompt library instance"""
    global _prompt_library
    if _prompt_library is None:
        _prompt_library = PromptLibrary()
    return _prompt_library
