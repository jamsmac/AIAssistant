"""
Integration tests for Progressive Disclosure Skills Registry v3.0
"""

import pytest
from agents.skills import SkillsRegistry, SkillLevel


@pytest.fixture
def registry():
    """Get fresh skills registry instance"""
    return SkillsRegistry()


@pytest.fixture
def sample_skill():
    """Create sample skill"""
    return {
        'name': 'backend-development',
        'description': 'Backend development and API design',
        'category': 'development',
        'triggers': ['backend', 'api', 'server'],
        'level_1_content': 'Skill: Backend Development',
        'level_2_content': 'Instructions for backend development...',
        'level_3_content': 'Detailed resources and examples...'
    }


class TestSkillRegistration:
    """Test skill registration"""
    
    def test_register_skill(self, registry, sample_skill):
        """Test registering a new skill"""
        result = registry.register_skill(
            name=sample_skill['name'],
            description=sample_skill['description'],
            category=sample_skill['category'],
            triggers=sample_skill['triggers'],
            level_1_content=sample_skill['level_1_content'],
            level_2_content=sample_skill['level_2_content'],
            level_3_content=sample_skill['level_3_content']
        )
        
        assert result is True
        assert sample_skill['name'] in registry.skills
    
    def test_register_duplicate_skill(self, registry, sample_skill):
        """Test registering duplicate skill"""
        registry.register_skill(**sample_skill)
        
        # Try to register again
        result = registry.register_skill(**sample_skill)
        assert result is False  # Should fail
    
    def test_get_skill(self, registry, sample_skill):
        """Test retrieving skill"""
        registry.register_skill(**sample_skill)
        
        skill = registry.get_skill(sample_skill['name'])
        assert skill is not None
        assert skill['name'] == sample_skill['name']
        assert skill['category'] == sample_skill['category']


class TestProgressiveDisclosure:
    """Test progressive disclosure mechanism"""
    
    def test_initial_skill_level(self, registry, sample_skill):
        """Test that skills start at level 1"""
        registry.register_skill(**sample_skill)
        
        skill = registry.get_skill(sample_skill['name'])
        assert skill['current_level'] == SkillLevel.METADATA
    
    def test_activate_skill(self, registry, sample_skill):
        """Test activating skill (load level 2)"""
        registry.register_skill(**sample_skill)
        
        # Activate skill
        result = registry.activate_skill(sample_skill['name'])
        assert result is True
        
        skill = registry.get_skill(sample_skill['name'])
        assert skill['current_level'] == SkillLevel.INSTRUCTIONS
        assert skill['active'] is True
    
    def test_use_skill(self, registry, sample_skill):
        """Test using skill (load level 3)"""
        registry.register_skill(**sample_skill)
        registry.activate_skill(sample_skill['name'])
        
        # Use skill
        result = registry.use_skill(sample_skill['name'])
        assert result is True
        
        skill = registry.get_skill(sample_skill['name'])
        assert skill['current_level'] == SkillLevel.RESOURCES
    
    def test_deactivate_skill(self, registry, sample_skill):
        """Test deactivating skill"""
        registry.register_skill(**sample_skill)
        registry.activate_skill(sample_skill['name'])
        
        # Deactivate
        result = registry.deactivate_skill(sample_skill['name'])
        assert result is True
        
        skill = registry.get_skill(sample_skill['name'])
        assert skill['active'] is False
        assert skill['current_level'] == SkillLevel.METADATA


class TestTriggerMatching:
    """Test trigger-based skill activation"""
    
    def test_match_triggers(self, registry):
        """Test matching skills by triggers"""
        # Register skills with different triggers
        skills = [
            {
                'name': 'backend-dev',
                'triggers': ['backend', 'api', 'server'],
                'description': 'Backend',
                'category': 'dev'
            },
            {
                'name': 'frontend-dev',
                'triggers': ['frontend', 'ui', 'react'],
                'description': 'Frontend',
                'category': 'dev'
            },
            {
                'name': 'database',
                'triggers': ['database', 'sql', 'query'],
                'description': 'Database',
                'category': 'data'
            }
        ]
        
        for skill in skills:
            registry.register_skill(
                name=skill['name'],
                description=skill['description'],
                category=skill['category'],
                triggers=skill['triggers'],
                level_1_content=f"Skill: {skill['name']}",
                level_2_content="Instructions...",
                level_3_content="Resources..."
            )
        
        # Match by trigger
        text = "I need to build a backend API"
        matched = registry.match_skills(text)
        
        assert len(matched) > 0
        assert any(s['name'] == 'backend-dev' for s in matched)
    
    def test_auto_activate_on_match(self, registry):
        """Test automatic activation when triggers match"""
        registry.register_skill(
            name='backend-dev',
            description='Backend development',
            category='dev',
            triggers=['backend', 'api'],
            level_1_content="Skill: Backend",
            level_2_content="Instructions...",
            level_3_content="Resources..."
        )
        
        # Match and auto-activate
        text = "Create a backend API"
        matched = registry.match_skills(text, auto_activate=True)
        
        assert len(matched) > 0
        skill = registry.get_skill('backend-dev')
        assert skill['active'] is True


class TestContextOptimization:
    """Test context optimization features"""
    
    def test_estimate_tokens(self, registry, sample_skill):
        """Test token estimation"""
        registry.register_skill(**sample_skill)
        
        # Level 1 (metadata only)
        tokens_l1 = registry.estimate_tokens(sample_skill['name'], SkillLevel.METADATA)
        assert tokens_l1 > 0
        assert tokens_l1 < 100  # Should be small
        
        # Level 2 (with instructions)
        tokens_l2 = registry.estimate_tokens(sample_skill['name'], SkillLevel.INSTRUCTIONS)
        assert tokens_l2 > tokens_l1
        
        # Level 3 (with resources)
        tokens_l3 = registry.estimate_tokens(sample_skill['name'], SkillLevel.RESOURCES)
        assert tokens_l3 > tokens_l2
    
    def test_context_savings(self, registry):
        """Test context savings calculation"""
        # Register multiple skills
        for i in range(10):
            registry.register_skill(
                name=f'skill-{i}',
                description=f'Skill {i}',
                category='test',
                triggers=[f'trigger{i}'],
                level_1_content=f"Skill {i} metadata",
                level_2_content=f"Skill {i} instructions" * 50,
                level_3_content=f"Skill {i} resources" * 200
            )
        
        # Activate only 2 skills
        registry.activate_skill('skill-0')
        registry.activate_skill('skill-1')
        
        stats = registry.get_statistics()
        
        # Should show significant context savings
        assert stats['context_saved_percentage'] > 50


class TestStatistics:
    """Test statistics tracking"""
    
    def test_activation_count(self, registry, sample_skill):
        """Test activation counting"""
        registry.register_skill(**sample_skill)
        
        initial_count = registry.stats['total_activations']
        
        registry.activate_skill(sample_skill['name'])
        
        assert registry.stats['total_activations'] == initial_count + 1
    
    def test_usage_count(self, registry, sample_skill):
        """Test usage counting"""
        registry.register_skill(**sample_skill)
        registry.activate_skill(sample_skill['name'])
        
        initial_count = registry.stats['total_uses']
        
        registry.use_skill(sample_skill['name'])
        
        assert registry.stats['total_uses'] == initial_count + 1
    
    def test_get_statistics(self, registry):
        """Test statistics retrieval"""
        # Register and use some skills
        for i in range(5):
            registry.register_skill(
                name=f'skill-{i}',
                description=f'Skill {i}',
                category='test',
                triggers=[f'trigger{i}'],
                level_1_content="Metadata",
                level_2_content="Instructions",
                level_3_content="Resources"
            )
        
        registry.activate_skill('skill-0')
        registry.activate_skill('skill-1')
        registry.use_skill('skill-0')
        
        stats = registry.get_statistics()
        
        assert stats['total_skills'] == 5
        assert stats['active_skills'] == 2
        assert stats['level_2_loaded'] == 2
        assert stats['level_3_loaded'] == 1


class TestSkillCategories:
    """Test skill categorization"""
    
    def test_list_by_category(self, registry):
        """Test listing skills by category"""
        categories = ['development', 'testing', 'security']
        
        for category in categories:
            for i in range(3):
                registry.register_skill(
                    name=f'{category}-skill-{i}',
                    description=f'{category} skill {i}',
                    category=category,
                    triggers=[f'{category}{i}'],
                    level_1_content="Metadata",
                    level_2_content="Instructions",
                    level_3_content="Resources"
                )
        
        # Get skills by category
        dev_skills = registry.list_skills(category='development')
        assert len(dev_skills) == 3
        assert all(s['category'] == 'development' for s in dev_skills)
    
    def test_list_active_skills(self, registry):
        """Test listing only active skills"""
        # Register skills
        for i in range(5):
            registry.register_skill(
                name=f'skill-{i}',
                description=f'Skill {i}',
                category='test',
                triggers=[f'trigger{i}'],
                level_1_content="Metadata",
                level_2_content="Instructions",
                level_3_content="Resources"
            )
        
        # Activate only 2
        registry.activate_skill('skill-0')
        registry.activate_skill('skill-2')
        
        active = registry.list_skills(active_only=True)
        assert len(active) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
