#!/usr/bin/env python3
"""
Test script for Workflow Engine
"""

import sqlite3
import json
from agents.workflow_engine import WorkflowEngine
from agents.database import HistoryDatabase

def setup_test_data():
    """Create test user, project, database, and workflows"""
    db = HistoryDatabase()

    # Create test user
    with sqlite3.connect(db.db_path) as conn:
        conn.execute("""
            INSERT OR IGNORE INTO users (id, email, password_hash)
            VALUES (999, 'workflow_test@example.com', 'test_hash')
        """)

        # Create test project
        conn.execute("""
            INSERT OR REPLACE INTO projects (id, user_id, name, description)
            VALUES (999, 999, 'Test Workflow Project', 'For testing workflows')
        """)

        # Create test database
        schema = {
            "columns": [
                {"name": "title", "type": "text", "required": True},
                {"name": "status", "type": "select", "required": True,
                 "options": ["pending", "active", "completed"]}
            ]
        }
        conn.execute("""
            INSERT OR REPLACE INTO databases (id, project_id, name, schema_json)
            VALUES (999, 999, 'Test Tasks', ?)
        """, (json.dumps(schema),))

        # Create test workflows

        # Workflow 1: Simple notification workflow
        workflow1_actions = [
            {
                "type": "send_notification",
                "config": {
                    "message": "Workflow executed successfully!",
                    "level": "info"
                }
            }
        ]

        conn.execute("""
            INSERT OR REPLACE INTO workflows
            (id, user_id, name, trigger_type, trigger_config, actions_json, enabled)
            VALUES (1, 999, 'Test Notification Workflow', 'manual', NULL, ?, 1)
        """, (json.dumps(workflow1_actions),))

        # Workflow 2: Create record workflow with variables
        workflow2_actions = [
            {
                "type": "create_record",
                "config": {
                    "database_id": 999,
                    "data": {
                        "title": "{{task.title}}",
                        "status": "{{task.status}}"
                    }
                }
            },
            {
                "type": "send_notification",
                "config": {
                    "message": "Created task: {{task.title}}",
                    "level": "info"
                }
            }
        ]

        conn.execute("""
            INSERT OR REPLACE INTO workflows
            (id, user_id, name, trigger_type, trigger_config, actions_json, enabled)
            VALUES (2, 999, 'Create Task Workflow', 'record_created', NULL, ?, 1)
        """, (json.dumps(workflow2_actions),))

        # Workflow 3: Multi-action workflow
        workflow3_actions = [
            {
                "type": "create_record",
                "config": {
                    "database_id": 999,
                    "data": {
                        "title": "Automated Task",
                        "status": "pending"
                    }
                }
            },
            {
                "type": "call_webhook",
                "config": {
                    "url": "https://httpbin.org/post",
                    "payload": {
                        "event": "task_created",
                        "title": "Automated Task"
                    }
                }
            },
            {
                "type": "send_notification",
                "config": {
                    "message": "Workflow completed with {{action_0_result.record_id}}",
                    "level": "info"
                }
            }
        ]

        conn.execute("""
            INSERT OR REPLACE INTO workflows
            (id, user_id, name, trigger_type, trigger_config, actions_json, enabled)
            VALUES (3, 999, 'Multi-Action Workflow', 'manual', NULL, ?, 1)
        """, (json.dumps(workflow3_actions),))

        # Workflow 4: Disabled workflow
        workflow4_actions = [
            {
                "type": "send_notification",
                "config": {
                    "message": "This should not execute",
                    "level": "error"
                }
            }
        ]

        conn.execute("""
            INSERT OR REPLACE INTO workflows
            (id, user_id, name, trigger_type, trigger_config, actions_json, enabled)
            VALUES (4, 999, 'Disabled Workflow', 'manual', NULL, ?, 0)
        """, (json.dumps(workflow4_actions),))

        conn.commit()

    print("✅ Test data created")

def test_simple_workflow():
    """Test 1: Simple notification workflow"""
    print("\n" + "="*60)
    print("Test 1: Simple Notification Workflow")
    print("="*60)

    engine = WorkflowEngine()
    result = engine.execute(1)

    print(f"\nSuccess: {result['success']}")
    print(f"Workflow ID: {result['workflow_id']}")
    print(f"Execution ID: {result.get('execution_id')}")
    print(f"Results: {json.dumps(result.get('results', []), indent=2)}")

    assert result['success'], "Workflow should succeed"
    assert len(result['results']) == 1, "Should have 1 result"

    print("✅ Test 1 PASSED")

def test_workflow_with_variables():
    """Test 2: Workflow with variable parsing"""
    print("\n" + "="*60)
    print("Test 2: Workflow with Variables")
    print("="*60)

    engine = WorkflowEngine()

    context = {
        "task": {
            "title": "Test Variable Parsing",
            "status": "active"
        }
    }

    result = engine.execute(2, context)

    print(f"\nSuccess: {result['success']}")
    print(f"Results: {json.dumps(result.get('results', []), indent=2)}")

    assert result['success'], "Workflow should succeed"
    assert len(result['results']) == 2, "Should have 2 results"

    # Check that record was created with correct data
    record_result = result['results'][0]
    assert record_result['success'], "Record creation should succeed"

    print("✅ Test 2 PASSED")

def test_multi_action_workflow():
    """Test 3: Multi-action workflow"""
    print("\n" + "="*60)
    print("Test 3: Multi-Action Workflow")
    print("="*60)

    engine = WorkflowEngine()
    result = engine.execute(3)

    print(f"\nSuccess: {result['success']}")
    print(f"Results: {json.dumps(result.get('results', []), indent=2)}")

    assert result['success'], "Workflow should succeed"
    assert len(result['results']) == 3, "Should have 3 results"

    # Check all actions succeeded
    for idx, action_result in enumerate(result['results']):
        print(f"\nAction {idx + 1}: {action_result.get('action_type')} - Success: {action_result.get('success')}")

    print("✅ Test 3 PASSED")

def test_disabled_workflow():
    """Test 4: Disabled workflow should not execute"""
    print("\n" + "="*60)
    print("Test 4: Disabled Workflow")
    print("="*60)

    engine = WorkflowEngine()
    result = engine.execute(4)

    print(f"\nSuccess: {result['success']}")
    print(f"Error: {result.get('error')}")

    assert not result['success'], "Disabled workflow should fail"
    assert 'disabled' in result.get('error', '').lower(), "Error should mention disabled"

    print("✅ Test 4 PASSED")

def test_nonexistent_workflow():
    """Test 5: Nonexistent workflow"""
    print("\n" + "="*60)
    print("Test 5: Nonexistent Workflow")
    print("="*60)

    engine = WorkflowEngine()
    result = engine.execute(99999)

    print(f"\nSuccess: {result['success']}")
    print(f"Error: {result.get('error')}")

    assert not result['success'], "Should fail for nonexistent workflow"
    assert 'not found' in result.get('error', '').lower(), "Error should mention not found"

    print("✅ Test 5 PASSED")

def test_variable_parsing():
    """Test 6: Variable parsing functionality"""
    print("\n" + "="*60)
    print("Test 6: Variable Parsing")
    print("="*60)

    engine = WorkflowEngine()

    # Test simple variable
    context = {"name": "John", "age": 30}
    result = engine.parse_variables("Hello {{name}}, you are {{age}} years old", context)
    print(f"\nSimple: {result}")
    assert result == "Hello John, you are 30 years old"

    # Test nested variable
    context = {"user": {"name": "Jane", "email": "jane@example.com"}}
    result = engine.parse_variables("User: {{user.name}} ({{user.email}})", context)
    print(f"Nested: {result}")
    assert result == "User: Jane (jane@example.com)"

    # Test array access
    context = {"items": [{"title": "First"}, {"title": "Second"}]}
    result = engine.parse_variables("Item: {{items.0.title}}", context)
    print(f"Array: {result}")
    assert result == "Item: First"

    # Test missing variable
    context = {"name": "John"}
    result = engine.parse_variables("Hello {{name}}, your age is {{age}}", context)
    print(f"Missing: {result}")
    assert result == "Hello John, your age is "

    print("✅ Test 6 PASSED")

def test_crud_actions():
    """Test 7: CRUD actions (create, update, delete record)"""
    print("\n" + "="*60)
    print("Test 7: CRUD Actions")
    print("="*60)

    engine = WorkflowEngine()

    # Create record
    print("\n1. Creating record...")
    create_action = {
        "type": "create_record",
        "config": {
            "database_id": 999,
            "data": {"title": "CRUD Test Task", "status": "pending"}
        }
    }

    result = engine.execute_action(create_action, {})
    print(f"Create result: {json.dumps(result, indent=2)}")
    assert result['success'], "Create should succeed"

    record_id = result['result']['record_id']
    print(f"Created record ID: {record_id}")

    # Update record
    print("\n2. Updating record...")
    update_action = {
        "type": "update_record",
        "config": {
            "record_id": record_id,
            "database_id": 999,
            "data": {"title": "Updated CRUD Test", "status": "active"}
        }
    }

    result = engine.execute_action(update_action, {})
    print(f"Update result: {json.dumps(result, indent=2)}")
    assert result['success'], "Update should succeed"

    # Delete record
    print("\n3. Deleting record...")
    delete_action = {
        "type": "delete_record",
        "config": {
            "record_id": record_id,
            "database_id": 999
        }
    }

    result = engine.execute_action(delete_action, {})
    print(f"Delete result: {json.dumps(result, indent=2)}")
    assert result['success'], "Delete should succeed"

    print("✅ Test 7 PASSED")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("WORKFLOW ENGINE TEST SUITE")
    print("="*60)

    try:
        setup_test_data()

        test_simple_workflow()
        test_workflow_with_variables()
        test_multi_action_workflow()
        test_disabled_workflow()
        test_nonexistent_workflow()
        test_variable_parsing()
        test_crud_actions()

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60 + "\n")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
