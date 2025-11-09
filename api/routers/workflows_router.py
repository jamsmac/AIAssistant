"""
Workflows Router - Handles Automation Desk functionality
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.database import HistoryDatabase, get_db
from agents.auth import get_current_user
from agents.workflow_engine import WorkflowEngine

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

# Initialize services
db = get_db()
workflow_engine = WorkflowEngine(db)

# Pydantic models
class TriggerConfig(BaseModel):
    type: str  # schedule, webhook, database, file, manual
    config: Dict[str, Any]

class ActionConfig(BaseModel):
    type: str  # ai, email, http, database, webhook, slack, telegram, file, transform, delay
    config: Dict[str, Any]
    next_action: Optional[str] = None

class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    trigger: TriggerConfig
    actions: List[ActionConfig]
    is_active: bool = True

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger: Optional[TriggerConfig] = None
    actions: Optional[List[ActionConfig]] = None
    is_active: Optional[bool] = None

class WorkflowResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str]
    trigger: Dict[str, Any]
    actions: List[Dict[str, Any]]
    is_active: bool
    created_at: str
    updated_at: str
    last_run: Optional[str]
    run_count: int

class ExecutionResponse(BaseModel):
    id: int
    workflow_id: int
    status: str  # pending, running, completed, failed
    started_at: str
    completed_at: Optional[str]
    result: Optional[Dict[str, Any]]
    error: Optional[str]

class ExecutionRequest(BaseModel):
    input_data: Optional[Dict[str, Any]] = None

# Workflow CRUD endpoints
@router.get("/", response_model=List[WorkflowResponse])
async def get_workflows(current_user: dict = Depends(get_current_user)):
    """Get all workflows for current user"""
    workflows = db.get_user_workflows(current_user['id'])

    result = []
    for workflow in workflows:
        executions = db.get_workflow_executions(workflow['id'])

        result.append(WorkflowResponse(
            id=workflow['id'],
            user_id=workflow['user_id'],
            name=workflow['name'],
            description=workflow.get('description'),
            trigger=json.loads(workflow['trigger_json']),
            actions=json.loads(workflow['actions_json']),
            is_active=workflow['is_active'],
            created_at=workflow['created_at'],
            updated_at=workflow.get('updated_at', workflow['created_at']),
            last_run=executions[0]['started_at'] if executions else None,
            run_count=len(executions)
        ))

    return result

@router.post("/", response_model=WorkflowResponse)
async def create_workflow(
    workflow: WorkflowCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new workflow"""
    try:
        workflow_id = db.create_workflow(
            user_id=current_user['id'],
            name=workflow.name,
            description=workflow.description,
            trigger_json=json.dumps(workflow.trigger.dict()),
            actions_json=json.dumps([action.dict() for action in workflow.actions]),
            is_active=workflow.is_active
        )

        # Register with workflow engine if active
        if workflow.is_active:
            await workflow_engine.register_workflow(workflow_id)

        # Get created workflow
        created = db.get_workflow(workflow_id, current_user['id'])

        return WorkflowResponse(
            id=created['id'],
            user_id=created['user_id'],
            name=created['name'],
            description=created.get('description'),
            trigger=json.loads(created['trigger_json']),
            actions=json.loads(created['actions_json']),
            is_active=created['is_active'],
            created_at=created['created_at'],
            updated_at=created.get('updated_at', created['created_at']),
            last_run=None,
            run_count=0
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific workflow"""
    workflow = db.get_workflow(workflow_id, current_user['id'])

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    executions = db.get_workflow_executions(workflow_id)

    return WorkflowResponse(
        id=workflow['id'],
        user_id=workflow['user_id'],
        name=workflow['name'],
        description=workflow.get('description'),
        trigger=json.loads(workflow['trigger_json']),
        actions=json.loads(workflow['actions_json']),
        is_active=workflow['is_active'],
        created_at=workflow['created_at'],
        updated_at=workflow.get('updated_at', workflow['created_at']),
        last_run=executions[0]['started_at'] if executions else None,
        run_count=len(executions)
    )

@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int,
    update: WorkflowUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a workflow"""
    # Verify ownership
    existing = db.get_workflow(workflow_id, current_user['id'])
    if not existing:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Prepare update data
    update_data = {}
    if update.name is not None:
        update_data['name'] = update.name
    if update.description is not None:
        update_data['description'] = update.description
    if update.trigger is not None:
        update_data['trigger_json'] = json.dumps(update.trigger.dict())
    if update.actions is not None:
        update_data['actions_json'] = json.dumps([action.dict() for action in update.actions])
    if update.is_active is not None:
        update_data['is_active'] = update.is_active

        # Update workflow engine registration
        if update.is_active:
            await workflow_engine.register_workflow(workflow_id)
        else:
            await workflow_engine.unregister_workflow(workflow_id)

    # Update in database
    db.update_workflow(workflow_id, current_user['id'], **update_data)

    # Return updated workflow
    return await get_workflow(workflow_id, current_user)

@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete a workflow"""
    # Verify ownership
    workflow = db.get_workflow(workflow_id, current_user['id'])
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Unregister from workflow engine
    await workflow_engine.unregister_workflow(workflow_id)

    # Delete from database
    db.delete_workflow(workflow_id, current_user['id'])

    return {"message": "Workflow deleted successfully"}

# Execution endpoints
@router.post("/{workflow_id}/execute", response_model=ExecutionResponse)
async def execute_workflow(
    workflow_id: int,
    request: ExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Execute a workflow manually"""
    # Verify ownership
    workflow = db.get_workflow(workflow_id, current_user['id'])
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Create execution record
    execution_id = db.create_workflow_execution(
        workflow_id=workflow_id,
        status="pending",
        input_data=json.dumps(request.input_data) if request.input_data else None
    )

    # Execute in background
    background_tasks.add_task(
        workflow_engine.execute_workflow,
        workflow_id,
        execution_id,
        request.input_data
    )

    return ExecutionResponse(
        id=execution_id,
        workflow_id=workflow_id,
        status="pending",
        started_at=datetime.now().isoformat(),
        completed_at=None,
        result=None,
        error=None
    )

@router.get("/{workflow_id}/executions", response_model=List[ExecutionResponse])
async def get_workflow_executions(
    workflow_id: int,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get execution history for a workflow"""
    # Verify ownership
    workflow = db.get_workflow(workflow_id, current_user['id'])
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    executions = db.get_workflow_executions(workflow_id, limit)

    return [
        ExecutionResponse(
            id=execution['id'],
            workflow_id=execution['workflow_id'],
            status=execution['status'],
            started_at=execution['started_at'],
            completed_at=execution.get('completed_at'),
            result=json.loads(execution['result_json']) if execution.get('result_json') else None,
            error=execution.get('error')
        )
        for execution in executions
    ]

@router.get("/executions/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get details of a specific execution"""
    execution = db.get_execution(execution_id)

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    # Verify ownership through workflow
    workflow = db.get_workflow(execution['workflow_id'], current_user['id'])
    if not workflow:
        raise HTTPException(status_code=403, detail="Access denied")

    return ExecutionResponse(
        id=execution['id'],
        workflow_id=execution['workflow_id'],
        status=execution['status'],
        started_at=execution['started_at'],
        completed_at=execution.get('completed_at'),
        result=json.loads(execution['result_json']) if execution.get('result_json') else None,
        error=execution.get('error')
    )

# Trigger types endpoint
@router.get("/triggers/types")
async def get_trigger_types():
    """Get available trigger types and their configurations"""
    return {
        "triggers": [
            {
                "type": "schedule",
                "name": "Schedule",
                "description": "Trigger workflow on a schedule",
                "config_schema": {
                    "cron": "string",
                    "timezone": "string"
                }
            },
            {
                "type": "webhook",
                "name": "Webhook",
                "description": "Trigger workflow via webhook",
                "config_schema": {
                    "webhook_url": "string",
                    "secret": "string"
                }
            },
            {
                "type": "database",
                "name": "Database Change",
                "description": "Trigger on database changes",
                "config_schema": {
                    "database_id": "integer",
                    "event": "string"  # insert, update, delete
                }
            },
            {
                "type": "file",
                "name": "File Change",
                "description": "Trigger on file changes",
                "config_schema": {
                    "path": "string",
                    "event": "string"  # created, modified, deleted
                }
            },
            {
                "type": "manual",
                "name": "Manual",
                "description": "Trigger manually via API or UI",
                "config_schema": {}
            }
        ]
    }

# Action types endpoint
@router.get("/actions/types")
async def get_action_types():
    """Get available action types and their configurations"""
    return {
        "actions": [
            {
                "type": "ai",
                "name": "AI Processing",
                "description": "Process data with AI models",
                "config_schema": {
                    "model": "string",
                    "prompt": "string",
                    "task_type": "string"
                }
            },
            {
                "type": "email",
                "name": "Send Email",
                "description": "Send an email notification",
                "config_schema": {
                    "to": "string",
                    "subject": "string",
                    "body": "string"
                }
            },
            {
                "type": "http",
                "name": "HTTP Request",
                "description": "Make an HTTP request",
                "config_schema": {
                    "url": "string",
                    "method": "string",
                    "headers": "object",
                    "body": "object"
                }
            },
            {
                "type": "database",
                "name": "Database Operation",
                "description": "Perform database operations",
                "config_schema": {
                    "database_id": "integer",
                    "operation": "string",
                    "data": "object"
                }
            },
            {
                "type": "transform",
                "name": "Transform Data",
                "description": "Transform data with JavaScript",
                "config_schema": {
                    "script": "string"
                }
            }
        ]
    }


# ============================================
# Scheduler Management Endpoints
# ============================================

@router.get("/{workflow_id}/schedule/next-run")
async def get_next_run_time(
    workflow_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get next scheduled run time for a workflow"""
    try:
        from api.scheduler import get_scheduler
        scheduler = get_scheduler()
        next_run = scheduler.get_next_run_time(workflow_id)

        if next_run:
            return {
                "workflow_id": workflow_id,
                "next_run_time": next_run.isoformat(),
                "scheduled": True
            }
        else:
            return {
                "workflow_id": workflow_id,
                "next_run_time": None,
                "scheduled": False
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/schedule/pause")
async def pause_workflow_schedule(
    workflow_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Pause scheduled workflow"""
    try:
        from api.scheduler import get_scheduler
        scheduler = get_scheduler()
        scheduler.pause_workflow(workflow_id)

        return {
            "workflow_id": workflow_id,
            "status": "paused",
            "message": "Workflow schedule paused successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/schedule/resume")
async def resume_workflow_schedule(
    workflow_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Resume paused workflow schedule"""
    try:
        from api.scheduler import get_scheduler
        scheduler = get_scheduler()
        scheduler.resume_workflow(workflow_id)

        return {
            "workflow_id": workflow_id,
            "status": "active",
            "message": "Workflow schedule resumed successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedule/jobs")
async def get_all_scheduled_jobs(current_user: dict = Depends(get_current_user)):
    """Get all scheduled workflow jobs"""
    try:
        from api.scheduler import get_scheduler
        scheduler = get_scheduler()
        jobs = scheduler.get_all_jobs()

        return {
            "jobs": jobs,
            "total_count": len(jobs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule/reload")
async def reload_scheduled_workflows(current_user: dict = Depends(get_current_user)):
    """Reload all scheduled workflows from database"""
    try:
        from api.scheduler import get_scheduler
        scheduler = get_scheduler()
        count = scheduler.load_scheduled_workflows()

        return {
            "message": "Scheduled workflows reloaded successfully",
            "workflows_loaded": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))