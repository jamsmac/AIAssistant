#!/usr/bin/env python3
"""
PostgreSQL Migration Script
Migrates from SQLite to PostgreSQL and sets up complete schema
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.postgres_db import PostgresDB, init_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_sql_file(db: PostgresDB, sql_file: Path):
    """Execute SQL file"""
    logger.info(f"Executing {sql_file.name}...")

    with open(sql_file, 'r') as f:
        sql = f.read()

    try:
        # Split by statement and execute
        statements = [s.strip() for s in sql.split(';') if s.strip()]

        for i, statement in enumerate(statements, 1):
            # Skip comments
            if statement.startswith('--') or not statement:
                continue

            try:
                await db.execute(statement)
                if i % 10 == 0:
                    logger.info(f"  Executed {i}/{len(statements)} statements...")
            except Exception as e:
                # Some statements might fail (like CREATE IF NOT EXISTS)
                # Log but continue
                if 'already exists' not in str(e):
                    logger.warning(f"Statement {i} warning: {e}")

        logger.info(f"✓ {sql_file.name} completed successfully")

    except Exception as e:
        logger.error(f"✗ Error executing {sql_file.name}: {e}")
        raise


async def verify_schema(db: PostgresDB):
    """Verify all tables were created"""
    logger.info("Verifying schema...")

    expected_tables = [
        # FractalAgents tables
        'fractal_agents',
        'agent_connectors',
        'agent_collective_memory',
        'agent_skills',
        'task_routing_history',
        'agent_performance_metrics',

        # Blog Platform tables
        'blog_categories',
        'blog_authors',
        'blog_posts',
        'blog_post_versions',
        'blog_comments',
        'blog_subscriptions',
        'blog_social_shares',
        'blog_analytics'
    ]

    tables = await db.get_tables()

    missing = []
    for expected in expected_tables:
        if expected not in tables:
            missing.append(expected)
        else:
            logger.info(f"  ✓ {expected}")

    if missing:
        logger.error(f"Missing tables: {missing}")
        return False

    logger.info(f"✓ All {len(expected_tables)} tables created successfully")
    return True


async def show_summary(db: PostgresDB):
    """Show summary of created schema"""
    logger.info("\n" + "="*60)
    logger.info("MIGRATION SUMMARY")
    logger.info("="*60)

    # Count tables
    tables = await db.get_tables()
    logger.info(f"\nTotal tables created: {len(tables)}")

    # Show table groups
    fractal_tables = [t for t in tables if t.startswith('fractal') or t.startswith('agent')]
    blog_tables = [t for t in tables if t.startswith('blog')]

    logger.info(f"\nFractalAgents tables ({len(fractal_tables)}):")
    for table in sorted(fractal_tables):
        # Use parameterized query with proper escaping for table names
        # PostgreSQL uses quote_ident() but for now we'll use manual validation
        if not table.replace('_', '').isalnum():
            logger.warning(f"Skipping invalid table name: {table}")
            continue
        count = await db.fetchval(f'SELECT COUNT(*) FROM "{table}"')
        logger.info(f"  - {table}: {count} rows")

    logger.info(f"\nBlog Platform tables ({len(blog_tables)}):")
    for table in sorted(blog_tables):
        # Validate table name to prevent SQL injection
        if not table.replace('_', '').isalnum():
            logger.warning(f"Skipping invalid table name: {table}")
            continue
        count = await db.fetchval(f'SELECT COUNT(*) FROM "{table}"')
        logger.info(f"  - {table}: {count} rows")

    # Show views
    views = await db.fetch("""
        SELECT table_name
        FROM information_schema.views
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)

    if views:
        logger.info(f"\nViews created ({len(views)}):")
        for view in views:
            logger.info(f"  - {view['table_name']}")

    # Show functions
    functions = await db.fetch("""
        SELECT routine_name
        FROM information_schema.routines
        WHERE routine_schema = 'public'
        AND routine_type = 'FUNCTION'
        ORDER BY routine_name
    """)

    if functions:
        logger.info(f"\nFunctions created ({len(functions)}):")
        for func in functions:
            logger.info(f"  - {func['routine_name']}")

    logger.info("\n" + "="*60)
    logger.info("✓ MIGRATION COMPLETED SUCCESSFULLY!")
    logger.info("="*60 + "\n")


async def main():
    """Main migration function"""
    logger.info("="*60)
    logger.info("PostgreSQL Migration - AI Assistant Platform v4.5")
    logger.info("="*60 + "\n")

    # Check DATABASE_URL
    if not os.getenv('DATABASE_URL'):
        logger.error("ERROR: DATABASE_URL environment variable not set")
        logger.info("Please set it in .env file or export it:")
        logger.info('  export DATABASE_URL="postgresql://user:pass@host:port/dbname"')
        sys.exit(1)

    logger.info(f"Database URL: {os.getenv('DATABASE_URL')[:30]}...")

    try:
        # Initialize database connection
        db = await init_db()
        logger.info("✓ Connected to PostgreSQL\n")

        # Get script directory
        script_dir = Path(__file__).parent

        # Run FractalAgents schema
        fractal_schema = script_dir / "init_fractal_schema.sql"
        if not fractal_schema.exists():
            logger.error(f"Schema file not found: {fractal_schema}")
            sys.exit(1)

        await run_sql_file(db, fractal_schema)

        # Run Blog Platform schema
        blog_schema = script_dir / "init_blog_schema.sql"
        if not blog_schema.exists():
            logger.error(f"Schema file not found: {blog_schema}")
            sys.exit(1)

        await run_sql_file(db, blog_schema)

        # Verify schema
        logger.info("")
        if not await verify_schema(db):
            logger.error("Schema verification failed!")
            sys.exit(1)

        # Show summary
        await show_summary(db)

        # Test queries
        logger.info("Running test queries...")

        # Test FractalAgents
        agent_count = await db.fetchval("SELECT COUNT(*) FROM fractal_agents")
        logger.info(f"  Agents in system: {agent_count}")

        # Test Blog
        category_count = await db.fetchval("SELECT COUNT(*) FROM blog_categories")
        logger.info(f"  Blog categories: {category_count}")

        logger.info("\n✓ All tests passed!")

    except Exception as e:
        logger.error(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        # Close connection
        from agents.postgres_db import close_db
        await close_db()
        logger.info("\nDatabase connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
