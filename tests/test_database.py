"""
Database operations tests for HistoryDatabase
"""

from __future__ import annotations

import json

import pytest

from agents.database import HistoryDatabase


@pytest.fixture()
def history_db(tmp_path) -> HistoryDatabase:
    db_path = tmp_path / "history.db"
    return HistoryDatabase(str(db_path))


def test_create_and_fetch_user(history_db: HistoryDatabase):
    user_id = history_db.create_user("user@example.com", "hashed")
    assert user_id > 0

    user = history_db.get_user_by_email("user@example.com")
    assert user is not None
    assert user["email"] == "user@example.com"
    assert user["is_active"] == 1


def test_update_user_last_login(history_db: HistoryDatabase):
    user_id = history_db.create_user("user2@example.com", "hashed")
    updated = history_db.update_user_last_login(user_id)
    assert updated == 1

    updated_user = history_db.get_user_by_email("user2@example.com")
    assert updated_user["last_login_at"] is not None


def test_project_crud(history_db: HistoryDatabase):
    user_id = history_db.create_user("project-owner@example.com", "hashed")

    project_id = history_db.create_project(user_id=user_id, name="Test Project", description="Desc")
    assert project_id > 0

    project = history_db.get_project(project_id, user_id)
    assert project is not None
    assert project["name"] == "Test Project"

    assert history_db.update_project(project_id, user_id, name="Updated", description="New desc")
    updated = history_db.get_project(project_id, user_id)
    assert updated["name"] == "Updated"

    projects = history_db.get_projects(user_id)
    assert len(projects) == 1

    assert history_db.delete_project(project_id, user_id) is True
    assert history_db.get_project(project_id, user_id) is None


def test_workflow_storage(history_db: HistoryDatabase):
    user_id = history_db.create_user("flow@example.com", "hashed")

    trigger_config = json.dumps({"type": "manual"})
    actions = json.dumps([{"type": "notify", "config": {"channel": "ops"}}])

    workflow_id = history_db.create_workflow(
        user_id=user_id,
        name="WF",
        trigger_type="manual",
        trigger_config=trigger_config,
        actions_json=actions,
    )
    assert workflow_id > 0

    workflow = history_db.get_workflow(workflow_id, user_id)
    assert workflow is not None
    assert workflow["name"] == "WF"

    execution_id = history_db.create_execution(
        workflow_id=workflow_id,
        status="completed",
        result_json=json.dumps({"message": "ok"}),
    )
    assert execution_id > 0

    executions = history_db.get_executions(workflow_id)
    assert len(executions) == 1
    assert executions[0]["status"] == "completed"
