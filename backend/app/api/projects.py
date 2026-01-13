"""
API routes for projects.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.db import get_db, get_db_session, db_manager
from app.db import dao
from app.core.events import event_bus, EventType, emit_project_event

router = APIRouter(prefix="/api/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    """Project creation schema"""
    name: str
    description: Optional[str] = None
    root_path: Optional[str] = None
    default_engine: Optional[str] = "copilot_cli"


class ProjectUpdate(BaseModel):
    """Project update schema"""
    description: Optional[str] = None
    root_path: Optional[str] = None
    default_engine: Optional[str] = None
    current_phase: Optional[str] = None


class ProjectResponse(BaseModel):
    """Project response schema"""
    id: int
    name: str
    description: Optional[str]
    db_path: str
    root_path: Optional[str]
    current_phase: Optional[str]
    default_engine: Optional[str]
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db_session)):
    """List all projects"""
    projects = dao.list_projects(db, skip=skip, limit=limit)
    return projects


@router.post("/", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db_session)):
    """Create a new project"""
    # Check if project name already exists
    existing = dao.get_project_by_name(db, project.name)
    if existing:
        raise HTTPException(status_code=400, detail=f"Project with name '{project.name}' already exists")
    
    # Create project
    new_project = dao.create_project(
        db,
        name=project.name,
        description=project.description,
        root_path=project.root_path,
        default_engine=project.default_engine
    )
    
    # Set database path
    db_path = db_manager.get_db_path(new_project.id)
    new_project = dao.update_project(db, new_project.id, db_path=db_path)
    
    # Initialize project database
    db_manager.init_project_db(new_project.id)
    
    # Create default control state
    project_db = next(get_db(new_project.id))
    dao.create_control_state(project_db, project_id=new_project.id)
    
    # Emit event
    emit_project_event(EventType.PROJECT_CREATED, new_project.id, {"name": new_project.name})
    
    return new_project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, db: Session = Depends(get_db_session)):
    """Get a project by ID"""
    project = dao.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    updates: ProjectUpdate,
    db: Session = Depends(get_db_session)
):
    """Update a project"""
    project = dao.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    
    # Build update dict from non-None fields
    update_data = {k: v for k, v in updates.dict().items() if v is not None}
    
    if update_data:
        updated_project = dao.update_project(db, project_id, **update_data)
        emit_project_event(EventType.PROJECT_UPDATED, project_id, update_data)
        return updated_project
    
    return project


@router.delete("/{project_id}")
async def delete_project(project_id: int, db: Session = Depends(get_db_session)):
    """Delete a project"""
    # Close project database connection first
    db_manager.close_project_db(project_id)
    
    success = dao.delete_project(db, project_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    
    emit_project_event(EventType.PROJECT_DELETED, project_id, {})
    
    return {"success": True, "message": f"Project {project_id} deleted"}

