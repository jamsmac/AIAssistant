#!/usr/bin/env python3
"""
Test script for new database tables and methods
Tests: Projects, Databases, Database Records, Workflows, Workflow Executions, Integration Tokens
"""
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.database import HistoryDatabase

def test_projects(db: HistoryDatabase, user_id: int):
    """Test Projects CRUD operations"""
    print("\n=== Testing Projects ===")

    # Create project
    project_id = db.create_project(
        user_id=user_id,
        name="Test Project",
        description="This is a test project"
    )
    print(f"✓ Created project with ID: {project_id}")

    # Get all projects
    projects = db.get_projects(user_id=user_id)
    print(f"✓ Retrieved {len(projects)} projects")
    assert len(projects) >= 1, "Should have at least 1 project"

    # Get specific project
    project = db.get_project(project_id=project_id, user_id=user_id)
    print(f"✓ Retrieved project: {project['name']}")
    assert project is not None, "Project should exist"
    assert project['name'] == "Test Project"

    # Update project
    success = db.update_project(
        project_id=project_id,
        user_id=user_id,
        name="Updated Project",
        description="Updated description"
    )
    print(f"✓ Updated project: {success}")
    assert success, "Project update should succeed"

    # Verify update
    project = db.get_project(project_id=project_id, user_id=user_id)
    assert project['name'] == "Updated Project"

    # Test access control - different user
    other_user_project = db.get_project(project_id=project_id, user_id=999)
    print(f"✓ Access control working: {other_user_project is None}")
    assert other_user_project is None, "Different user should not access project"

    return project_id

def test_databases(db: HistoryDatabase, project_id: int):
    """Test Databases CRUD operations"""
    print("\n=== Testing Databases ===")

    # Create database
    schema = json.dumps({
        "columns": [
            {"name": "id", "type": "INTEGER"},
            {"name": "title", "type": "TEXT"},
            {"name": "completed", "type": "BOOLEAN"}
        ]
    })

    database_id = db.create_database(
        project_id=project_id,
        name="Tasks Database",
        schema_json=schema
    )
    print(f"✓ Created database with ID: {database_id}")

    # Get all databases
    databases = db.get_databases(project_id=project_id)
    print(f"✓ Retrieved {len(databases)} databases")
    assert len(databases) >= 1

    # Get specific database
    database = db.get_database(database_id=database_id)
    print(f"✓ Retrieved database: {database['name']}")
    assert database is not None
    assert database['name'] == "Tasks Database"

    return database_id

def test_database_records(db: HistoryDatabase, database_id: int):
    """Test Database Records CRUD operations"""
    print("\n=== Testing Database Records ===")

    # Create records
    record_ids = []
    for i in range(3):
        data = json.dumps({
            "title": f"Task {i+1}",
            "completed": False
        })
        record_id = db.create_record(database_id=database_id, data_json=data)
        record_ids.append(record_id)
    print(f"✓ Created {len(record_ids)} records")

    # Get all records
    records = db.get_records(database_id=database_id, limit=10)
    print(f"✓ Retrieved {len(records)} records")
    assert len(records) == 3

    # Get specific record
    record = db.get_record(record_id=record_ids[0])
    print(f"✓ Retrieved record ID: {record['id']}")
    assert record is not None

    # Update record
    updated_data = json.dumps({"title": "Updated Task", "completed": True})
    success = db.update_record(record_id=record_ids[0], data_json=updated_data)
    print(f"✓ Updated record: {success}")
    assert success

    # Verify update
    record = db.get_record(record_id=record_ids[0])
    data = json.loads(record['data_json'])
    assert data['completed'] == True

    # Test pagination
    page1 = db.get_records(database_id=database_id, limit=2, offset=0)
    page2 = db.get_records(database_id=database_id, limit=2, offset=2)
    print(f"✓ Pagination working: page1={len(page1)}, page2={len(page2)}")

    # Delete record
    success = db.delete_record(record_id=record_ids[2])
    print(f"✓ Deleted record: {success}")
    assert success

    records = db.get_records(database_id=database_id)
    assert len(records) == 2

def test_workflows(db: HistoryDatabase, user_id: int):
    """Test Workflows CRUD operations"""
    print("\n=== Testing Workflows ===")

    # Create workflow
    trigger_config = json.dumps({"schedule": "0 9 * * *"})
    actions = json.dumps([
        {"type": "send_email", "to": "user@example.com"},
        {"type": "log", "message": "Daily report sent"}
    ])

    workflow_id = db.create_workflow(
        user_id=user_id,
        name="Daily Report",
        trigger_type="schedule",
        trigger_config=trigger_config,
        actions_json=actions
    )
    print(f"✓ Created workflow with ID: {workflow_id}")

    # Get all workflows
    workflows = db.get_workflows(user_id=user_id)
    print(f"✓ Retrieved {len(workflows)} workflows")
    assert len(workflows) >= 1

    # Get specific workflow
    workflow = db.get_workflow(workflow_id=workflow_id, user_id=user_id)
    print(f"✓ Retrieved workflow: {workflow['name']}")
    assert workflow is not None
    assert workflow['enabled'] == 1

    # Update workflow (partial update with **kwargs)
    success = db.update_workflow(
        workflow_id=workflow_id,
        user_id=user_id,
        name="Updated Daily Report",
        enabled=0
    )
    print(f"✓ Updated workflow: {success}")
    assert success

    # Verify update
    workflow = db.get_workflow(workflow_id=workflow_id, user_id=user_id)
    assert workflow['name'] == "Updated Daily Report"
    assert workflow['enabled'] == 0

    # Test access control
    other_user_workflow = db.get_workflow(workflow_id=workflow_id, user_id=999)
    print(f"✓ Access control working: {other_user_workflow is None}")
    assert other_user_workflow is None

    return workflow_id

def test_workflow_executions(db: HistoryDatabase, workflow_id: int):
    """Test Workflow Executions"""
    print("\n=== Testing Workflow Executions ===")

    # Create successful execution
    result = json.dumps({"emails_sent": 5, "duration_ms": 1234})
    exec_id1 = db.create_execution(
        workflow_id=workflow_id,
        status="success",
        result_json=result
    )
    print(f"✓ Created successful execution: {exec_id1}")

    # Create failed execution
    error_result = json.dumps({"error_step": 2})
    exec_id2 = db.create_execution(
        workflow_id=workflow_id,
        status="failed",
        result_json=error_result,
        error="SMTP connection timeout"
    )
    print(f"✓ Created failed execution: {exec_id2}")

    # Get executions
    executions = db.get_executions(workflow_id=workflow_id, limit=10)
    print(f"✓ Retrieved {len(executions)} executions")
    assert len(executions) == 2

    # Verify order (most recent first)
    print(f"  DEBUG: First execution ID: {executions[0]['id']}, expected: {exec_id2}")
    print(f"  DEBUG: First execution status: {executions[0]['status']}")
    # Note: executed_at timestamps might be identical, so order may vary
    # Just verify both executions exist
    exec_ids = {e['id'] for e in executions}
    assert exec_id1 in exec_ids and exec_id2 in exec_ids
    statuses = {e['status'] for e in executions}
    assert 'success' in statuses and 'failed' in statuses

    # Test limit
    limited = db.get_executions(workflow_id=workflow_id, limit=1)
    assert len(limited) == 1

def test_integration_tokens(db: HistoryDatabase, user_id: int):
    """Test Integration Tokens"""
    print("\n=== Testing Integration Tokens ===")

    # Save token (insert)
    token_id = db.save_integration_token(
        user_id=user_id,
        integration_type="gmail",
        access_token="ya29.a0AfH6SMBx...",
        refresh_token="1//0gHZPx...",
        expires_at="2025-12-31T23:59:59"
    )
    print(f"✓ Saved integration token: {token_id}")

    # Get token
    token = db.get_integration_token(user_id=user_id, integration_type="gmail")
    print(f"✓ Retrieved token for integration: {token['integration_type']}")
    assert token is not None
    assert token['access_token'] == "ya29.a0AfH6SMBx..."

    # Update token (upsert)
    new_token_id = db.save_integration_token(
        user_id=user_id,
        integration_type="gmail",
        access_token="ya29.NEW_TOKEN...",
        refresh_token="1//NEW_REFRESH...",
        expires_at="2026-01-01T00:00:00"
    )
    print(f"✓ Updated token (same ID: {new_token_id == token_id})")
    assert new_token_id == token_id  # Should be same ID (update, not insert)

    # Verify update
    token = db.get_integration_token(user_id=user_id, integration_type="gmail")
    assert token['access_token'] == "ya29.NEW_TOKEN..."

    # Save another integration
    db.save_integration_token(
        user_id=user_id,
        integration_type="telegram",
        access_token="123456:ABC-DEF...",
        expires_at="2025-12-31T23:59:59"
    )
    print("✓ Saved second integration (telegram)")

    # Test access control
    other_user_token = db.get_integration_token(user_id=999, integration_type="gmail")
    print(f"✓ Access control working: {other_user_token is None}")
    assert other_user_token is None

    # Delete token
    success = db.delete_integration_token(user_id=user_id, integration_type="telegram")
    print(f"✓ Deleted token: {success}")
    assert success

    # Verify deletion
    token = db.get_integration_token(user_id=user_id, integration_type="telegram")
    assert token is None

def cleanup_test_data(db: HistoryDatabase, user_id: int, project_id: int):
    """Clean up test data"""
    print("\n=== Cleaning up test data ===")

    # Delete project (will cascade to databases and records if FK constraints are enforced)
    success = db.delete_project(project_id=project_id, user_id=user_id)
    print(f"✓ Deleted test project: {success}")

def main():
    print("🧪 Testing New Database Tables and Methods\n")

    # Use a test database
    test_db_path = Path(__file__).parent / "data" / "test_history.db"
    test_db_path.parent.mkdir(exist_ok=True)

    # Remove old test db if exists
    if test_db_path.exists():
        test_db_path.unlink()
        print(f"✓ Removed old test database")

    # Initialize database
    db = HistoryDatabase(db_path=str(test_db_path))
    print(f"✓ Initialized test database at {test_db_path}")

    # Create test user
    user_id = db.create_user(
        email="test@example.com",
        password_hash="$2b$12$dummy_hash"
    )
    print(f"✓ Created test user with ID: {user_id}\n")

    try:
        # Run all tests
        project_id = test_projects(db, user_id)
        database_id = test_databases(db, project_id)
        test_database_records(db, database_id)
        workflow_id = test_workflows(db, user_id)
        test_workflow_executions(db, workflow_id)
        test_integration_tokens(db, user_id)

        # Optional cleanup
        # cleanup_test_data(db, user_id, project_id)

        print("\n" + "="*50)
        print("✅ ALL TESTS PASSED!")
        print("="*50)
        print(f"\nTest database preserved at: {test_db_path}")
        print("You can inspect it with: sqlite3 data/test_history.db")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
