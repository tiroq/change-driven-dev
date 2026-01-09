"""
API routes for tasks.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.db import get_db
from app.models import TaskStatus, PhaseType

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    """Task creation schema"""
    project_id: int
    title: str
    description: Optional[str] = None


class TaskResponse(BaseModel):
    """Task response schema"""
    id: int
    project_id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    current_phase: Optional[PhaseType]
    version: int
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(project_id: Optional[int] = None, db: Session = Depends(get_db)):
    """List all tasks, optionally filtered by project"""
    # Placeholder - returns empty list
    return []


@router.post("/", response_model=TaskResponse)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task"""
    # Placeholder - returns mock response
    return {
        "id": 1,
        "project_id": task.project_id,
        "title": task.title,
        "description": task.description,
        "status": TaskStatus.PENDING,
        "current_phase": None,
        "version": 1
    }


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a task by ID"""
    # Placeholder - returns mock response
    return {
        "id": task_id,
        "project_id": 1,
        "title": "Sample Task",
        "description": "Sample task description",
        "status": TaskStatus.PENDING,
        "current_phase": None,
        "version": 1
    }


@router.post("/{task_id}/advance")
async def advance_task(task_id: int, db: Session = Depends(get_db)):
    """Advance task to next phase"""
    # Placeholder - returns mock response
    return {
        "status": "advanced",
        "current_phase": PhaseType.PLANNER,
        "next_phase": PhaseType.ARCHITECT,
        "message": "Task advanced to next phase"
    }
