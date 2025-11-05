#!/usr/bin/env python3
"""
Example: Process task through FractalAgents system
Demonstrates dynamic task routing and multi-agent collaboration
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.postgres_db import init_db, close_db
from agents.fractal import FractalAgentOrchestrator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Process task example"""
    print("=" * 60)
    print("FractalAgents Task Processing Example")
    print("=" * 60 + "\n")

    try:
        # Initialize database
        db = await init_db()
        logger.info("✓ Connected to database")

        # Initialize orchestrator
        print("Initializing FractalAgents system...")
        orchestrator = FractalAgentOrchestrator(db)
        await orchestrator.initialize('demo')

        print("✓ System initialized\n")

        # Show system status
        status = await orchestrator.get_system_status('demo')
        print(f"System Status:")
        print(f"  Total Agents: {status['agents']['total']}")
        print(f"  Memory Entries: {status['collective_memory']['total_entries']}")
        print(f"  Success Rate: {status['collective_memory']['success_rate']:.1%}")
        print(f"  Status: {status['status']}")
        print()

        # Example tasks
        tasks = [
            {
                'description': 'Write a blog post about machine learning basics',
                'required_skills': ['blog_writing', 'technical_knowledge'],
                'type': 'content_creation'
            },
            {
                'description': 'Analyze user engagement data and provide insights',
                'required_skills': ['data_analysis', 'reporting'],
                'type': 'analysis'
            },
            {
                'description': 'Optimize this blog post for SEO',
                'required_skills': ['seo_optimization'],
                'type': 'seo'
            }
        ]

        # Process each task
        for i, task in enumerate(tasks, 1):
            print(f"\n{'='*60}")
            print(f"Task {i}: {task['description']}")
            print(f"Required skills: {', '.join(task['required_skills'])}")
            print('=' * 60)

            task['organization_id'] = 'demo'

            print("\nProcessing...")
            result = await orchestrator.process_task(task)

            if result.get('success'):
                print(f"\n✓ Task completed successfully!")
                print(f"  Agent: {result.get('agent_name', 'Unknown')}")
                print(f"  Execution time: {result.get('execution_time', 0)}ms")
                print(f"  Tokens used: {result.get('tokens_used', 0)}")

                # Show response preview
                response = result.get('response', '')
                if response:
                    print(f"\n  Response preview:")
                    print(f"  {response[:200]}...")
            else:
                print(f"\n✗ Task failed: {result.get('error', 'Unknown error')}")

        # Show final system status
        print(f"\n{'='*60}")
        print("Final System Status")
        print('=' * 60)

        final_status = await orchestrator.get_system_status('demo')
        print(f"  Tasks processed: {final_status['recent_activity']['tasks_24h']}")
        print(f"  Success rate: {final_status['recent_activity']['success_rate_24h']:.1%}")
        print(f"  Memory entries: {final_status['collective_memory']['total_entries']}")

        # Show routing history
        print(f"\nRecent Routing History:")
        history = await orchestrator.get_routing_history('demo', limit=5)

        for entry in history[:3]:
            print(f"  • {entry['task_description'][:50]}...")
            print(f"    Assigned to: {entry.get('assigned_agent_name', 'Unknown')}")
            print(f"    Success: {'✓' if entry.get('was_successful') else '✗'}")
            print()

        print("=" * 60)
        print("Example completed!")
        print("=" * 60 + "\n")

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await close_db()


if __name__ == '__main__':
    asyncio.run(main())
