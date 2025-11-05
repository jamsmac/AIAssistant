"""
Projects Router - Handles DataParse Layer (Projects, Databases, Records)
"""

from fastapi import APIRouter, Depends, HTTPException, status
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

router = APIRouter(prefix="/api", tags=["projects", "databases"])

# Initialize database
db = get_db()

# Pydantic models
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class ProjectDetail(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str]
    settings: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str
    database_count: int = 0

class DatabaseSchema(BaseModel):
    fields: List[Dict[str, Any]]

class DatabaseCreate(BaseModel):
    project_id: int
    name: str
    schema: DatabaseSchema

class DatabaseResponse(BaseModel):
    id: int
    project_id: int
    name: str
    schema: Dict[str, Any]
    created_at: str
    updated_at: str
    record_count: int = 0

class RecordCreate(BaseModel):
    database_id: int
    data: Dict[str, Any]

class RecordUpdate(BaseModel):
    data: Dict[str, Any]

class RecordResponse(BaseModel):
    id: int
    database_id: int
    data: Dict[str, Any]
    created_at: str
    updated_at: str

# Project endpoints
@router.get("/projects", response_model=List[ProjectDetail])
async def get_projects(current_user: dict = Depends(get_current_user)):
    """Get all projects for current user"""
    projects = db.get_user_projects(current_user['id'])

    result = []
    for project in projects:
        # Get database count for each project
        databases = db.get_project_databases(project['id'])

        result.append(ProjectDetail(
            id=project['id'],
            user_id=project['user_id'],
            name=project['name'],
            description=project.get('description'),
            settings=json.loads(project['settings']) if project.get('settings') else None,
            created_at=project['created_at'],
            updated_at=project.get('updated_at', project['created_at']),
            database_count=len(databases)
        ))

    return result

@router.post("/projects", response_model=ProjectDetail)
async def create_project(
    project: ProjectCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new project"""
    try:
        project_id = db.create_project(
            user_id=current_user['id'],
            name=project.name,
            description=project.description,
            settings=json.dumps(project.settings) if project.settings else None
        )

        # Get created project
        created_project = db.get_project(project_id, current_user['id'])

        return ProjectDetail(
            id=created_project['id'],
            user_id=created_project['user_id'],
            name=created_project['name'],
            description=created_project.get('description'),
            settings=json.loads(created_project['settings']) if created_project.get('settings') else None,
            created_at=created_project['created_at'],
            updated_at=created_project.get('updated_at', created_project['created_at']),
            database_count=0
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/projects/{project_id}", response_model=ProjectDetail)
async def get_project(
    project_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific project"""
    project = db.get_project(project_id, current_user['id'])

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    databases = db.get_project_databases(project_id)

    return ProjectDetail(
        id=project['id'],
        user_id=project['user_id'],
        name=project['name'],
        description=project.get('description'),
        settings=json.loads(project['settings']) if project.get('settings') else None,
        created_at=project['created_at'],
        updated_at=project.get('updated_at', project['created_at']),
        database_count=len(databases)
    )

@router.put("/projects/{project_id}", response_model=ProjectDetail)
async def update_project(
    project_id: int,
    update: ProjectUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a project"""
    # Verify ownership
    existing = db.get_project(project_id, current_user['id'])
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found")

    # Update project
    db.update_project(
        project_id=project_id,
        user_id=current_user['id'],
        name=update.name,
        description=update.description,
        settings=json.dumps(update.settings) if update.settings else None
    )

    # Return updated project
    return await get_project(project_id, current_user)

@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete a project and all its data"""
    # Verify ownership
    project = db.get_project(project_id, current_user['id'])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Delete project (cascades to databases and records)
    db.delete_project(project_id, current_user['id'])

    return {"message": "Project deleted successfully"}

# Database endpoints
@router.get("/databases", response_model=List[DatabaseResponse])
async def get_databases(
    project_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get databases (optionally filtered by project)"""
    if project_id:
        # Verify project ownership
        project = db.get_project(project_id, current_user['id'])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        databases = db.get_project_databases(project_id)
    else:
        # Get all databases for user's projects
        projects = db.get_user_projects(current_user['id'])
        databases = []
        for project in projects:
            databases.extend(db.get_project_databases(project['id']))

    result = []
    for database in databases:
        records = db.get_database_records(database['id'])

        result.append(DatabaseResponse(
            id=database['id'],
            project_id=database['project_id'],
            name=database['name'],
            schema=json.loads(database['schema_json']),
            created_at=database['created_at'],
            updated_at=database.get('updated_at', database['created_at']),
            record_count=len(records)
        ))

    return result

@router.post("/databases", response_model=DatabaseResponse)
async def create_database(
    database: DatabaseCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new database in a project"""
    # Verify project ownership
    project = db.get_project(database.project_id, current_user['id'])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Create database
    db_id = db.create_database(
        project_id=database.project_id,
        name=database.name,
        schema_json=json.dumps(database.schema.dict())
    )

    # Get created database
    created_db = db.get_database(db_id)

    return DatabaseResponse(
        id=created_db['id'],
        project_id=created_db['project_id'],
        name=created_db['name'],
        schema=json.loads(created_db['schema_json']),
        created_at=created_db['created_at'],
        updated_at=created_db.get('updated_at', created_db['created_at']),
        record_count=0
    )

@router.get("/databases/{database_id}", response_model=DatabaseResponse)
async def get_database(
    database_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific database"""
    database = db.get_database(database_id)

    if not database:
        raise HTTPException(status_code=404, detail="Database not found")

    # Verify ownership through project
    project = db.get_project(database['project_id'], current_user['id'])
    if not project:
        raise HTTPException(status_code=403, detail="Access denied")

    records = db.get_database_records(database_id)

    return DatabaseResponse(
        id=database['id'],
        project_id=database['project_id'],
        name=database['name'],
        schema=json.loads(database['schema_json']),
        created_at=database['created_at'],
        updated_at=database.get('updated_at', database['created_at']),
        record_count=len(records)
    )

@router.delete("/databases/{database_id}")
async def delete_database(
    database_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete a database and all its records"""
    database = db.get_database(database_id)

    if not database:
        raise HTTPException(status_code=404, detail="Database not found")

    # Verify ownership through project
    project = db.get_project(database['project_id'], current_user['id'])
    if not project:
        raise HTTPException(status_code=403, detail="Access denied")

    db.delete_database(database_id)

    return {"message": "Database deleted successfully"}

# Record endpoints
@router.get("/databases/{database_id}/records", response_model=List[RecordResponse])
async def get_records(
    database_id: int,
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Get records from a database"""
    database = db.get_database(database_id)

    if not database:
        raise HTTPException(status_code=404, detail="Database not found")

    # Verify ownership through project
    project = db.get_project(database['project_id'], current_user['id'])
    if not project:
        raise HTTPException(status_code=403, detail="Access denied")

    records = db.get_database_records(database_id, limit, offset)

    return [
        RecordResponse(
            id=record['id'],
            database_id=record['database_id'],
            data=json.loads(record['data_json']),
            created_at=record['created_at'],
            updated_at=record.get('updated_at', record['created_at'])
        )
        for record in records
    ]

@router.post("/databases/{database_id}/records", response_model=RecordResponse)
async def create_record(
    database_id: int,
    record: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Create a new record in a database"""
    database = db.get_database(database_id)

    if not database:
        raise HTTPException(status_code=404, detail="Database not found")

    # Verify ownership through project
    project = db.get_project(database['project_id'], current_user['id'])
    if not project:
        raise HTTPException(status_code=403, detail="Access denied")

    # Validate against schema
    schema = json.loads(database['schema_json'])
    # TODO: Implement schema validation

    # Create record
    record_id = db.create_record(
        database_id=database_id,
        data_json=json.dumps(record)
    )

    # Get created record
    created_record = db.get_record(record_id)

    return RecordResponse(
        id=created_record['id'],
        database_id=created_record['database_id'],
        data=json.loads(created_record['data_json']),
        created_at=created_record['created_at'],
        updated_at=created_record.get('updated_at', created_record['created_at'])
    )

@router.put("/records/{record_id}", response_model=RecordResponse)
async def update_record(
    record_id: int,
    update: RecordUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a record"""
    record = db.get_record(record_id)

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    # Verify ownership through database and project
    database = db.get_database(record['database_id'])
    project = db.get_project(database['project_id'], current_user['id'])
    if not project:
        raise HTTPException(status_code=403, detail="Access denied")

    # Update record
    db.update_record(
        record_id=record_id,
        data_json=json.dumps(update.data)
    )

    # Get updated record
    updated_record = db.get_record(record_id)

    return RecordResponse(
        id=updated_record['id'],
        database_id=updated_record['database_id'],
        data=json.loads(updated_record['data_json']),
        created_at=updated_record['created_at'],
        updated_at=updated_record['updated_at']
    )

@router.delete("/records/{record_id}")
async def delete_record(
    record_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete a record"""
    record = db.get_record(record_id)

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    # Verify ownership through database and project
    database = db.get_database(record['database_id'])
    project = db.get_project(database['project_id'], current_user['id'])
    if not project:
        raise HTTPException(status_code=403, detail="Access denied")

    db.delete_record(record_id)

    return {"message": "Record deleted successfully"}