"""
API routes for projects.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.db import get_db
from app.models import Project

router = APIRouter(prefix="/api/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    """Project creation schema"""
    name: str
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    """Project response schema"""
    id: int
    name: str
    description: Optional[str]
    db_path: str
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(db: Session = Depends(get_db)):
    """List all projects"""
    # Placeholder - returns empty list
    return []


@router.post("/", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project"""
    # Placeholder - returns mock response
    return {
        "id": 1,
        "name": project.name,
        "description": project.description,
        "db_path": "./data/project_1.db"
    }


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, db: Session = Depends(get_db)):
    """Get a project by ID"""
    # Placeholder - returns mock response
    return {
        "id": project_id,
        "name": "Sample Project",
        "description": "Sample project description",
        "db_path": f"./data/project_{project_id}.db"
    }
