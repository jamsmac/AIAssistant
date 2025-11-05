#!/usr/bin/env python3
"""
Initialize FractalAgents System
Creates default agents and connectors for a new organization
"""
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.postgres_db import init_db, close_db
from agents.fractal import FractalAgentOrchestrator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_blog_agents(orchestrator: FractalAgentOrchestrator, org_id: str, root_id: str):
    """Initialize blog-specific agents"""
    logger.info("Creating blog agents...")

    # 1. Writer Agent
    writer_id = await orchestrator.create_agent(
        organization_id=org_id,
        name='BlogWriter',
        skills=['blog_writing', 'content_creation', 'storytelling', 'copywriting'],
        agent_type='specialist',
        parent_agent_id=root_id,
        description='Specialized in writing compelling blog posts',
        system_prompt="""You are a professional blog content writer. Your role is to create engaging, well-structured blog posts that provide value to readers. Focus on clarity, engagement, and actionable insights."""
    )

    # 2. Editor Agent
    editor_id = await orchestrator.create_agent(
        organization_id=org_id,
        name='BlogEditor',
        skills=['editing', 'proofreading', 'readability_improvement', 'grammar'],
        agent_type='specialist',
        parent_agent_id=root_id,
        description='Specialized in editing and improving content quality',
        system_prompt="""You are a professional editor. Your role is to improve content quality by fixing grammar, enhancing readability, and ensuring consistency. Focus on clarity and flow."""
    )

    # 3. SEO Agent
    seo_id = await orchestrator.create_agent(
        organization_id=org_id,
        name='BlogSEO',
        skills=['seo_optimization', 'keyword_research', 'meta_tags', 'content_structure'],
        agent_type='specialist',
        parent_agent_id=root_id,
        description='Specialized in SEO optimization',
        system_prompt="""You are an SEO specialist. Your role is to optimize content for search engines while maintaining readability. Focus on keywords, meta tags, and structure."""
    )

    # 4. Image Agent
    image_id = await orchestrator.create_agent(
        organization_id=org_id,
        name='BlogImage',
        skills=['image_generation', 'visual_content', 'alt_text', 'design'],
        agent_type='specialist',
        parent_agent_id=root_id,
        description='Specialized in image generation and visual content',
        system_prompt="""You are a visual content specialist. Your role is to create compelling image concepts and alt text for blog posts. Focus on relevance and accessibility."""
    )

    # 5. Social Agent
    social_id = await orchestrator.create_agent(
        organization_id=org_id,
        name='BlogSocial',
        skills=['social_media', 'content_distribution', 'engagement', 'hashtags'],
        agent_type='specialist',
        parent_agent_id=root_id,
        description='Specialized in social media content creation',
        system_prompt="""You are a social media specialist. Your role is to create engaging social media posts that drive traffic to blog content. Focus on platform-specific optimization."""
    )

    # Create peer connections between blog agents (collaboration network)
    await orchestrator.create_connector(writer_id, editor_id, 'peer', 0.9, 0.9)
    await orchestrator.create_connector(editor_id, seo_id, 'peer', 0.8, 0.8)
    await orchestrator.create_connector(seo_id, image_id, 'peer', 0.7, 0.7)
    await orchestrator.create_connector(writer_id, social_id, 'peer', 0.8, 0.8)

    logger.info(f"✓ Created 5 blog agents")

    return {
        'writer': writer_id,
        'editor': editor_id,
        'seo': seo_id,
        'image': image_id,
        'social': social_id
    }


async def init_general_agents(orchestrator: FractalAgentOrchestrator, org_id: str, root_id: str):
    """Initialize general-purpose agents"""
    logger.info("Creating general agents...")

    # 1. Analyst Agent
    analyst_id = await orchestrator.create_agent(
        organization_id=org_id,
        name='DataAnalyst',
        skills=['data_analysis', 'research', 'insights', 'reporting'],
        agent_type='specialist',
        parent_agent_id=root_id,
        description='Specialized in data analysis and research'
    )

    # 2. Code Assistant Agent
    coder_id = await orchestrator.create_agent(
        organization_id=org_id,
        name='CodeAssistant',
        skills=['code_generation', 'code_review', 'debugging', 'refactoring'],
        agent_type='specialist',
        parent_agent_id=root_id,
        description='Specialized in code-related tasks'
    )

    logger.info(f"✓ Created 2 general agents")

    return {
        'analyst': analyst_id,
        'coder': coder_id
    }


async def main():
    """Main initialization function"""
    logger.info("="*60)
    logger.info("FractalAgents System Initialization")
    logger.info("="*60 + "\n")

    # Check DATABASE_URL
    if not os.getenv('DATABASE_URL'):
        logger.error("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    try:
        # Initialize database
        db = await init_db()
        logger.info("✓ Connected to PostgreSQL\n")

        # Check if tables exist
        tables = await db.get_tables()
        required_tables = ['fractal_agents', 'agent_connectors', 'blog_posts']

        missing = [t for t in required_tables if t not in tables]
        if missing:
            logger.error(f"Missing tables: {missing}")
            logger.error("Please run migration script first: python scripts/migrate_to_postgres.py")
            sys.exit(1)

        # Organization ID (you can customize this)
        org_id = input("Enter organization ID (default: default): ").strip() or "default"

        logger.info(f"\nInitializing agents for organization: {org_id}\n")

        # Initialize orchestrator
        orchestrator = FractalAgentOrchestrator(db)

        # Check if root agent already exists
        existing_root = await db.fetchrow("""
            SELECT * FROM fractal_agents
            WHERE organization_id = $1 AND type = 'root'
        """, org_id)

        if existing_root:
            logger.info(f"Root agent already exists: {existing_root['name']}")
            root_id = str(existing_root['id'])
        else:
            # Create root agent
            root_id = await orchestrator.create_root_agent(org_id)
            logger.info(f"✓ Created root agent\n")

        # Initialize blog agents
        blog_agents = await init_blog_agents(orchestrator, org_id, root_id)

        # Initialize general agents
        general_agents = await init_general_agents(orchestrator, org_id, root_id)

        # Show summary
        logger.info("\n" + "="*60)
        logger.info("INITIALIZATION COMPLETE!")
        logger.info("="*60)

        # Get system status
        await orchestrator.initialize(org_id)
        status = await orchestrator.get_system_status(org_id)

        logger.info(f"\nSystem Status:")
        logger.info(f"  Total Agents: {status['agents']['total']}")
        logger.info(f"  Total Connectors: {status['connectors']['total']}")
        logger.info(f"  Status: {status['status']}")

        logger.info(f"\nBlog Agents Created:")
        for name, agent_id in blog_agents.items():
            logger.info(f"  - {name}: {agent_id}")

        logger.info(f"\nGeneral Agents Created:")
        for name, agent_id in general_agents.items():
            logger.info(f"  - {name}: {agent_id}")

        logger.info(f"\nYou can now:")
        logger.info(f"  1. Use the API to process tasks: POST /api/fractal/task")
        logger.info(f"  2. Generate blog posts: POST /api/blog/ai/generate")
        logger.info(f"  3. View system status: GET /api/fractal/system-status")

        logger.info("\n" + "="*60 + "\n")

    except Exception as e:
        logger.error(f"\n✗ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
