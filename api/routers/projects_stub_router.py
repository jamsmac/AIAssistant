from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/api/projects", tags=["projects-test"])


class Project(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


PROJECTS: List[Project] = [
    Project(id=1, name="Sample Project", description="Sample description", created_at=datetime.utcnow(), updated_at=datetime.utcnow())
]


def _ensure_authorized(request: Request) -> None:
    if request.cookies.get("auth_token") is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


@router.get("", response_model=List[Project])
async def list_projects(request: Request) -> List[Project]:
    _ensure_authorized(request)
    return PROJECTS


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate, request: Request) -> Project:
    _ensure_authorized(request)
    new_id = max((project.id for project in PROJECTS), default=0) + 1
    project = Project(
        id=new_id,
        name=payload.name,
        description=payload.description,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    PROJECTS.append(project)
    return project


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: int, request: Request) -> Project:
    _ensure_authorized(request)
    for project in PROJECTS:
        if project.id == project_id:
            return project
    raise HTTPException(status_code=404, detail="Project not found")


@router.patch("/{project_id}", response_model=Project)
async def update_project(project_id: int, payload: ProjectUpdate, request: Request) -> Project:
    _ensure_authorized(request)
    for idx, project in enumerate(PROJECTS):
        if project.id == project_id:
            updated = project.model_copy(update=payload.model_dump(exclude_unset=True))
            updated.updated_at = datetime.utcnow()
            PROJECTS[idx] = updated
            return updated
    raise HTTPException(status_code=404, detail="Project not found")


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: int, request: Request):
    _ensure_authorized(request)
    initial = len(PROJECTS)
    PROJECTS[:] = [p for p in PROJECTS if p.id != project_id]
    if len(PROJECTS) == initial:
        raise HTTPException(status_code=404, detail="Project not found")
    return None
