#!/usr/bin/env python3
"""
PostgreSQL Migration Runner
Safely runs database migrations with rollback support
"""
import os
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime
import asyncpg
from typing import List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MigrationRunner:
    """Handles database migrations safely"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.migrations_dir = Path(__file__).parent / "migrations"

    async def create_migrations_table(self, conn: asyncpg.Connection):
        """Create migrations tracking table"""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                execution_time_ms INTEGER,
                checksum VARCHAR(64)
            )
        """)
        logger.info("Migrations table ready")

    async def get_executed_migrations(self, conn: asyncpg.Connection) -> List[str]:
        """Get list of executed migrations"""
        rows = await conn.fetch("""
            SELECT version FROM schema_migrations
            ORDER BY version
        """)
        return [row['version'] for row in rows]

    async def calculate_checksum(self, content: str) -> str:
        """Calculate SHA-256 checksum of migration content"""
        import hashlib
        return hashlib.sha256(content.encode()).hexdigest()

    async def run_migration(self, conn: asyncpg.Connection, migration_file: Path):
        """Run a single migration file"""
        version = migration_file.stem
        logger.info(f"Running migration: {version}")

        with open(migration_file, 'r') as f:
            content = f.read()

        checksum = await self.calculate_checksum(content)
        start_time = datetime.now()

        try:
            # Execute migration in transaction
            async with conn.transaction():
                # Split and execute statements
                statements = []
                current_statement = []

                for line in content.split('\n'):
                    # Skip comments
                    if line.strip().startswith('--'):
                        continue

                    current_statement.append(line)

                    # Check for statement terminator
                    if line.rstrip().endswith(';'):
                        statement = '\n'.join(current_statement).strip()
                        if statement:
                            statements.append(statement)
                        current_statement = []

                # Execute each statement
                for i, statement in enumerate(statements, 1):
                    if statement.strip():
                        try:
                            await conn.execute(statement)
                        except asyncpg.PostgresError as e:
                            # Log but continue for certain non-critical errors
                            if 'already exists' in str(e).lower():
                                logger.warning(f"Skipping (already exists): {str(e)[:100]}")
                            else:
                                raise

                    if i % 10 == 0:
                        logger.info(f"  Executed {i}/{len(statements)} statements...")

                # Record migration
                execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                await conn.execute("""
                    INSERT INTO schema_migrations (version, execution_time_ms, checksum)
                    VALUES ($1, $2, $3)
                """, version, execution_time, checksum)

            logger.info(f"✅ Migration {version} completed in {execution_time}ms")

        except Exception as e:
            logger.error(f"❌ Migration {version} failed: {e}")
            raise

    async def run_all_migrations(self):
        """Run all pending migrations"""
        logger.info("=" * 60)
        logger.info("PostgreSQL Migration Runner")
        logger.info("=" * 60)

        # Connect to database
        try:
            conn = await asyncpg.connect(self.database_url)
            logger.info("✅ Connected to PostgreSQL")
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            logger.info("Please ensure DATABASE_URL is set correctly")
            sys.exit(1)

        try:
            # Create migrations table
            await self.create_migrations_table(conn)

            # Get executed migrations
            executed = await self.get_executed_migrations(conn)
            logger.info(f"Found {len(executed)} executed migrations")

            # Find migration files
            migration_files = sorted(self.migrations_dir.glob("*.sql"))
            logger.info(f"Found {len(migration_files)} migration files")

            # Run pending migrations
            pending = []
            for migration_file in migration_files:
                version = migration_file.stem
                if version not in executed:
                    pending.append(migration_file)

            if not pending:
                logger.info("✅ Database is up to date")
                return

            logger.info(f"Running {len(pending)} pending migrations...")

            for migration_file in pending:
                await self.run_migration(conn, migration_file)

            # Verify schema
            await self.verify_schema(conn)

            logger.info("=" * 60)
            logger.info("✅ All migrations completed successfully!")
            logger.info("=" * 60)

        finally:
            await conn.close()
            logger.info("Database connection closed")

    async def verify_schema(self, conn: asyncpg.Connection):
        """Verify that all expected tables exist"""
        logger.info("\nVerifying schema...")

        expected_tables = [
            # Core tables (001_initial_schema.sql)
            'users', 'oauth_accounts', 'sessions',
            'projects', 'project_databases',
            'workflows', 'workflow_triggers', 'workflow_actions', 'workflow_executions',
            'chat_sessions', 'chat_messages',
            'model_rankings', 'audit_logs', 'rate_limits',

            # FractalAgents tables (002_fractal_agents_schema.sql)
            'fractal_agents', 'agent_connectors', 'agent_collective_memory',
            'agent_skills', 'task_routing_history',

            # Blog Platform tables (003_blog_platform_schema.sql)
            'blog_categories', 'blog_authors', 'blog_posts', 'blog_post_versions',
            'blog_comments', 'blog_subscriptions', 'blog_social_shares', 'blog_analytics'
        ]

        # Get existing tables
        rows = await conn.fetch("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)

        existing_tables = {row['tablename'] for row in rows}

        # Check for missing tables
        missing = []
        for table in expected_tables:
            if table in existing_tables:
                logger.info(f"  ✅ {table}")
            else:
                logger.error(f"  ❌ {table} - MISSING!")
                missing.append(table)

        if missing:
            raise Exception(f"Missing tables: {missing}")

        # Count records in key tables
        logger.info("\nTable statistics:")
        for table in ['users', 'projects', 'chat_sessions', 'model_rankings']:
            if table in existing_tables:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                logger.info(f"  {table}: {count} records")

    async def rollback_migration(self, version: str):
        """Rollback a specific migration (if rollback script exists)"""
        rollback_file = self.migrations_dir / f"{version}_rollback.sql"

        if not rollback_file.exists():
            logger.error(f"No rollback script found for {version}")
            return False

        logger.info(f"Rolling back migration: {version}")

        conn = await asyncpg.connect(self.database_url)
        try:
            async with conn.transaction():
                # Execute rollback script
                with open(rollback_file, 'r') as f:
                    content = f.read()

                await conn.execute(content)

                # Remove from migrations table
                await conn.execute("""
                    DELETE FROM schema_migrations
                    WHERE version = $1
                """, version)

            logger.info(f"✅ Rollback completed for {version}")
            return True

        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            return False

        finally:
            await conn.close()


async def main():
    """Main entry point"""
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        logger.error("❌ DATABASE_URL environment variable not set")
        logger.info("\nPlease set it in your .env file or export it:")
        logger.info('export DATABASE_URL="postgresql://user:password@host:port/database"')
        logger.info("\nFor Railway, it's automatically provided")
        logger.info("For local development, use:")
        logger.info('export DATABASE_URL="postgresql://localhost/aiassistant"')
        sys.exit(1)

    # Check for command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "rollback" and len(sys.argv) > 2:
            version = sys.argv[2]
            runner = MigrationRunner(database_url)
            success = await runner.rollback_migration(version)
            sys.exit(0 if success else 1)
        else:
            print("Usage:")
            print("  python run_migrations.py          # Run all pending migrations")
            print("  python run_migrations.py rollback VERSION  # Rollback specific migration")
            sys.exit(1)

    # Run all migrations
    runner = MigrationRunner(database_url)
    await runner.run_all_migrations()


if __name__ == "__main__":
    asyncio.run(main())