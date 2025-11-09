"""
Global test fixtures and configuration
"""
import pytest
import asyncio
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime

from httpx import AsyncClient

# Set test environment before app import
os.environ["TESTING"] = "true"
os.environ["ENVIRONMENT"] = "test"

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import anthropic


class DummyAnthropicResponse:
    def __init__(self, text: str = "Test response"):
        self.content = [SimpleNamespace(text=text)]
        self.usage = SimpleNamespace(total_tokens=128, output_tokens=128, input_tokens=64)


class DummyAnthropicMessages:
    def create(self, **kwargs):  # type: ignore[override]
        return DummyAnthropicResponse()


class DummyAnthropicClient:
    def __init__(self, *args, **kwargs):
        self.messages = DummyAnthropicMessages()


anthropic.Anthropic = DummyAnthropicClient  # type: ignore[attr-defined]

from api.server_refactored import app
from agents.auth import get_current_user, get_current_user_from_token
from agents.database import get_db
from agents.csrf_protection import get_csrf_protection
from agents import postgres_db


class DummyFractalDB:
    def __init__(self):
        self.agents = {}
        self.connectors = []
        self.next_agent_id = 1
        self.memory_entries = []

    async def connect(self):
        return None

    async def disconnect(self):
        return None

    async def fetchrow(self, query: str, *args):
        if "FROM fractal_agents" in query and "type = 'root'" in query:
            for agent in self.agents.values():
                if agent['organization_id'] == args[0] and agent['type'] == 'root' and agent['enabled']:
                    return agent
            return None
        if "FROM fractal_agents WHERE id" in query:
            agent = self.agents.get(str(args[0]))
            return agent
        if "FROM agent_collective_memory" in query:
            successes = [entry for entry in self.memory_entries if entry.get('success')]
            total_entries = len(self.memory_entries)
            successful_entries = len(successes)
            avg_confidence = sum(entry.get('confidence_score', 0) for entry in self.memory_entries) / total_entries if total_entries else 0
            avg_execution_time = sum(entry.get('execution_time', 0) for entry in self.memory_entries) / total_entries if total_entries else 0
            return {
                'total_entries': total_entries,
                'successful_entries': successful_entries,
                'avg_confidence': avg_confidence,
                'avg_execution_time': avg_execution_time,
            }
        return None

    async def fetch(self, query: str, *args):
        if "FROM agent_connectors" in query:
            result = []
            for connector in self.connectors:
                if connector['from_agent_id'] == args[0] and connector['enabled']:
                    target = self.agents.get(connector['to_agent_id'])
                    if target and target['enabled']:
                        entry = dict(connector)
                        entry['to_agent_name'] = target['name']
                        entry['to_agent_skills'] = target['skills']
                        entry['to_agent_success_rate'] = target.get('success_rate', 0.5)
                        result.append(entry)
            return result
        if "GROUP BY type" in query and "FROM fractal_agents" in query:
            stats = {}
            for agent in self.agents.values():
                if agent['organization_id'] == args[0] and agent['enabled']:
                    entry = stats.setdefault(agent['type'], {'type': agent['type'], 'count': 0, 'avg_success_rate': 0.0, 'avg_tasks_completed': 0.0})
                    entry['count'] += 1
            return list(stats.values())
        if "parent_agent_id" in query and "FROM fractal_agents" in query:
            return [agent for agent in self.agents.values() if agent.get('parent_agent_id') == args[0] and agent['enabled']]
        if "ORDER BY total_tasks_completed" in query and "FROM fractal_agents" in query:
            agents = [agent for agent in self.agents.values() if agent['organization_id'] == args[0] and agent['enabled']]
            for agent in agents:
                agent.setdefault('total_tasks_completed', 0)
                agent.setdefault('success_rate', 0.5)
                agent.setdefault('last_active_at', datetime.utcnow().isoformat())
            agents.sort(key=lambda a: a.get('total_tasks_completed', 0), reverse=True)
            return agents[:5]
        if "FROM agent_collective_memory" in query:
            if "LEFT JOIN fractal_agents" in query:
                organization_id = args[0]
                min_confidence = args[1] if len(args) > 1 else 0
                limit = args[-1] if args else 10
                filters = list(args[2:-1]) if len(args) > 2 else []
                task_type = filters[0] if len(filters) >= 1 else None
                task_category = filters[1] if len(filters) >= 2 else None
                results = [
                    {
                        **entry,
                        'primary_agent_name': self.agents.get(entry['primary_agent_id'], {}).get('name', 'Primary Agent'),
                    }
                    for entry in self.memory_entries
                    if entry['organization_id'] == organization_id
                    and entry.get('confidence_score', 0) >= min_confidence
                    and (task_type is None or entry.get('task_type') == task_type)
                    and (task_category is None or entry.get('task_category') == task_category)
                ]
                results.sort(key=lambda e: e.get('confidence_score', 0), reverse=True)
                return results[:limit]

            # Base agent memory query (task_type, organization_id)
            task_type = args[0] if len(args) > 0 else None
            organization_id = args[1] if len(args) > 1 else None
            return [
                entry
                for entry in self.memory_entries
                if (task_type is None or entry.get('task_type') == task_type)
                and (organization_id is None or entry.get('organization_id') == organization_id)
                and entry.get('success', False)
            ]
        if "FROM task_routing_history" in query:
            return []
        return []

    async def fetchval(self, query: str, *args):
        if "INSERT INTO fractal_agents" in query:
            agent_id = str(self.next_agent_id)
            self.next_agent_id += 1
            agent = {
                'id': agent_id,
                'organization_id': args[0],
                'name': args[1],
                'type': args[2],
                'description': args[3],
                'skills': args[4],
                'parent_agent_id': args[5],
                'level': args[6],
                'model': args[7],
                'system_prompt': args[8],
                'trust_level': args[9],
                'enabled': args[10],
                'created_at': datetime.utcnow().isoformat(),
                'success_rate': 0.5,
                'total_tasks_completed': 0,
                'last_active_at': datetime.utcnow().isoformat(),
            }
            self.agents[agent_id] = agent
            return agent_id
        if "SELECT organization_id FROM fractal_agents" in query:
            agent = self.agents.get(str(args[0]))
            return agent['organization_id'] if agent else None
        if "SELECT level FROM fractal_agents" in query:
            agent = self.agents.get(str(args[0]))
            return agent['level'] if agent else 0
        if "SELECT COUNT(*) FROM agent_connectors" in query:
            return len([c for c in self.connectors if c['organization_id'] == args[0] and c['enabled']])
        if "SELECT COUNT(*) FROM task_routing_history" in query:
            return 0
        if "COALESCE(" in query and "task_routing_history" in query:
            return 0.8
        return None

    async def execute(self, query: str, *args):
        if "INSERT INTO agent_collective_memory" in query:
            entry = {
                'organization_id': args[0],
                'task_type': args[1],
                'task_category': args[2],
                'input_context': args[3],
                'solution_approach': args[4],
                'solution_summary': args[5],
                'participating_agents': args[6],
                'primary_agent_id': args[7],
                'success': args[8],
                'execution_time': args[9],
                'confidence_score': args[10],
                'created_at': datetime.utcnow().isoformat(),
            }
            self.memory_entries.append(entry)
        elif "INSERT INTO agent_connectors" in query:
            connector = {
                'organization_id': args[0],
                'from_agent_id': args[1],
                'to_agent_id': args[2],
                'connector_type': args[3],
                'strength': args[4],
                'trust': args[5],
                'routing_rules': args[6],
                'enabled': args[7],
            }
            self.connectors = [c for c in self.connectors if not (c['from_agent_id'] == connector['from_agent_id'] and c['to_agent_id'] == connector['to_agent_id'])]
            self.connectors.append(connector)
        elif "UPDATE fractal_agents" in query and "SET enabled = FALSE" in query:
            agent = self.agents.get(str(args[0]))
            if agent:
                agent['enabled'] = False
        elif "DELETE FROM fractal_agents" in query:
            self.agents.pop(str(args[0]), None)
        return None


# Patch global PostgresDB before tests import modules
postgres_db.PostgresDB = DummyFractalDB
try:
    import tests.test_fractal_system as fractal_tests
    fractal_tests.PostgresDB = DummyFractalDB
except ImportError:
    fractal_tests = None


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables after each test"""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(autouse=True)
def override_dependencies():
    class DummyDB:
        def __init__(self):
            self.projects = [
                {
                    "id": 1,
                    "user_id": 1,
                    "name": "Sample Project",
                    "description": "Sample description",
                    "settings": None,
                    "created_at": "2024-01-01T00:00:00",
                }
            ]
            self.next_id = 2

        def get_user_projects(self, user_id: int):
            return list(self.projects)

        def create_project(self, user_id: int, name: str, description: str = None, settings: str = None):
            project = {
                "id": self.next_id,
                "user_id": user_id,
                "name": name,
                "description": description,
                "settings": settings,
                "created_at": "2024-01-01T00:00:00",
            }
            self.projects.append(project)
            self.next_id += 1
            return project["id"]

        def get_project(self, project_id: int, user_id: int):
            for project in self.projects:
                if project["id"] == project_id:
                    return project
            return None

        def update_project(self, project_id: int, user_id: int, name: str = None, description: str = None, settings: str = None):
            project = self.get_project(project_id, user_id)
            if not project:
                return False
            if name is not None:
                project["name"] = name
            if description is not None:
                project["description"] = description
            if settings is not None:
                project["settings"] = settings
            project["updated_at"] = "2024-01-02T00:00:00"
            return True

        def delete_project(self, project_id: int, user_id: int):
            self.projects = [p for p in self.projects if p["id"] != project_id]

        def get_project_databases(self, project_id: int):
            return []

    dummy_db = DummyDB()

    class DummyMetrics:
        async def collect(self):
            return [{"name": "app_requests_total", "value": 1, "type": "counter", "help": "Requests"}]

        def get_uptime(self):
            return 1.0

        def get_memory_usage(self):
            return 10.5

        def get_cpu_usage(self):
            return 5.0

        def get_active_connections(self):
            return 2

        def get_cache_hit_rate(self):
            return 0.95

    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "email": "user@example.com"}
    app.dependency_overrides[get_current_user_from_token] = lambda: {"id": 1, "email": "user@example.com"}
    app.dependency_overrides[get_db] = lambda: dummy_db

    from api.routers import projects_router, dashboard_router

    postgres_db.PostgresDB = DummyFractalDB
    if fractal_tests is not None:
        fractal_tests.PostgresDB = DummyFractalDB

    projects_router.db = dummy_db
    dashboard_router.metrics = DummyMetrics()

    from agents.fractal.orchestrator import FractalAgentOrchestrator

    original_create_connector = FractalAgentOrchestrator.create_connector

    async def patched_create_connector(self, *args, **kwargs):
        await original_create_connector(self, *args, **kwargs)
        if self.root_agent:
            self.root_agent._initialized = False

    FractalAgentOrchestrator.create_connector = patched_create_connector
    yield
    app.dependency_overrides.clear()
    FractalAgentOrchestrator.create_connector = original_create_connector


@pytest.fixture
async def client():
    """Async test client for FastAPI app."""
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
async def authenticated_client(client):
    """Authenticated client stub with auth cookie."""
    client.cookies.set("auth_token", "test-token")
    csrf_token = get_csrf_protection().generate_token("1")
    client.headers["X-CSRF-Token"] = csrf_token
    client.headers["Origin"] = "http://testserver"
    client.headers["Referer"] = "http://testserver"
    return client


@pytest.fixture
def test_user():
    return SimpleNamespace(id=1, email="user@example.com")


@pytest.fixture
def test_project():
    return SimpleNamespace(id=1, name="Test Project", description="Project description")


@pytest.fixture
def mock_openai():
    yield None


@pytest.fixture
async def test_session():
    class DummyResult:
        def __init__(self, users):
            self._users = users

        def scalar_one(self):
            return self._users[0]

        class _ScalarResult:
            def __init__(self, users):
                self._users = users

            def all(self):
                return self._users

        def scalars(self):
            return self._ScalarResult(self._users)

    class DummySession:
        async def execute(self, _query):
            users = [
                SimpleNamespace(id=i, email=f"user{i}@example.com", hashed_password="hash")
                for i in range(100)
            ]
            return DummyResult(users)

        def add_all(self, _users):
            return None

        async def commit(self):
            return None

    yield DummySession()
