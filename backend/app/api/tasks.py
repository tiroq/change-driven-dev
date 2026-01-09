"""
API routes for tasks.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.db import get_db
from app.db import dao
from app.models import TaskStatus, PhaseType
from app.core.events import EventType, emit_task_event

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    """Task creation schema"""
    project_id: int
    title: str
    description: Optional[str] = None
    priority: Optional[int] = 0


class TaskUpdate(BaseModel):
    """Task update schema"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    current_phase: Optional[PhaseType] = None
    priority: Optional[int] = None


class TaskResponse(BaseModel):
    """Task response schema"""
    id: int
    project_id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    current_phase: Optional[PhaseType]
    version: int
    attempts: int
    priority: int
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    project_id: Optional[int] = None,
    status: Optional[TaskStatus] = None,
    phase: Optional[PhaseType] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(lambda: next(get_db(1)))
):
    """List all tasks, optionally filtered by project, status, or phase"""
    tasks = dao.list_tasks(db, project_id=project_id, status=status, phase=phase, skip=skip, limit=limit)
    return tasks


@router.post("/", response_model=TaskResponse)
async def create_task(task: TaskCreate, db: Session = Depends(lambda: next(get_db(task.project_id)))):
    """Create a new task"""
    new_task = dao.create_task(
        db,
        project_id=task.project_id,
        title=task.title,
        description=task.description,
        priority=task.priority or 0
    )
    
    emit_task_event(EventType.TASK_CREATED, task.project_id, new_task.id, {"title": new_task.title})
    
    return new_task


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, project_id: int, db: Session = Depends(lambda: next(get_db(1)))):
    """Get a task by ID"""
    task = dao.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    project_id: int,
    updates: TaskUpdate,
    db: Session = Depends(lambda: next(get_db(1)))
):
    """Update a task"""
    task = dao.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # Build update dict from non-None fields
    update_data = {k: v for k, v in updates.dict().items() if v is not None}
    
    if update_data:
        updated_task = dao.update_task(db, task_id, **update_data)
        
        # Emit status change event if status was updated
        if "status" in update_data:
            emit_task_event(EventType.TASK_STATUS_CHANGED, project_id, task_id, {
                "old_status": task.status.value,
                "new_status": update_data["status"].value
            })
        else:
            emit_task_event(EventType.TASK_UPDATED, project_id, task_id, update_data)
        
        return updated_task
    
    return task


@router.delete("/{task_id}")
async def delete_task(task_id: int, project_id: int, db: Session = Depends(lambda: next(get_db(1)))):
    """Delete a task"""
    success = dao.delete_task(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    emit_task_event(EventType.TASK_DELETED, project_id, task_id, {})
    
    return {"success": True, "message": f"Task {task_id} deleted"}


@router.post("/{task_id}/approve")
async def approve_task(task_id: int, project_id: int, approver: str = "system", db: Session = Depends(lambda: next(get_db(1)))):
    """Approve a task"""
    task = dao.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # Create approval record
    dao.create_approval(db, task_id=task_id, approver=approver, approved=True)
    
    # Update task status to APPROVED
    dao.update_task(db, task_id, status=TaskStatus.APPROVED)
    
    emit_task_event(EventType.TASK_STATUS_CHANGED, project_id, task_id, {
        "status": "approved",
        "approver": approver
    })
    
    return {"success": True, "message": f"Task {task_id} approved"}


@router.post("/{task_id}/advance")
async def advance_task(task_id: int, project_id: int, db: Session = Depends(lambda: next(get_db(1)))):
    """Advance task to next phase"""
    task = dao.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # Determine next phase
    phase_order = [PhaseType.PLANNER, PhaseType.ARCHITECT, PhaseType.REVIEW_APPROVAL, PhaseType.CODER]
    current_idx = phase_order.index(task.current_phase) if task.current_phase else -1
    
    if current_idx < len(phase_order) - 1:
        next_phase = phase_order[current_idx + 1]
        dao.update_task(db, task_id, current_phase=next_phase)
        
        emit_task_event(EventType.TASK_UPDATED, project_id, task_id, {
            "old_phase": task.current_phase.value if task.current_phase else None,
            "new_phase": next_phase.value
        })
        
        return {
            "status": "advanced",
            "current_phase": task.current_phase.value if task.current_phase else None,
            "next_phase": next_phase.value,
            "message": f"Task advanced to {next_phase.value}"
        }
    else:
        return {
            "status": "completed",
            "message": "Task is already in final phase"
        }

