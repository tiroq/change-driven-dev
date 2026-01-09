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


class TaskVersionResponse(BaseModel):
    """Task version response schema"""
    id: int
    task_id: int
    version_num: int
    title: str
    description: Optional[str]
    gates_json: Optional[str]
    deps_json: Optional[str]
    extra_data: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True


class TaskSplitRequest(BaseModel):
    """Request to split a task into two"""
    task1_title: str
    task1_description: Optional[str] = None
    task2_title: str
    task2_description: Optional[str] = None


class TaskMergeRequest(BaseModel):
    """Request to merge multiple tasks into one"""
    task_ids: List[int]
    merged_title: str
    merged_description: Optional[str] = None


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
    """
    Update a task and create a new version in the history.
    Significant edits (title, description) create a new TaskVersion record.
    """
    task = dao.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # Build update dict from non-None fields
    update_data = {k: v for k, v in updates.dict().items() if v is not None}
    
    if not update_data:
        return task
    
    # Check if this is a significant edit (title or description change)
    significant_edit = any(key in update_data for key in ['title', 'description'])
    
    if significant_edit:
        # Create a new TaskVersion with current state before updating
        new_version_num = task.version + 1
        
        # Create version record
        task_version = dao.create_task_version(
            db=db,
            task_id=task_id,
            version_num=new_version_num,
            title=update_data.get('title', task.title),
            description=update_data.get('description', task.description),
            gates_json=None,  # TODO: Add gates support
            deps_json=None,   # TODO: Add deps support
            extra_data=None
        )
        
        # Update task version number and active_version_id
        update_data['version'] = new_version_num
        update_data['active_version_id'] = task_version.id
    
    # Apply updates
    updated_task = dao.update_task(db, task_id, **update_data)
    
    # Emit appropriate event
    if "status" in update_data:
        emit_task_event(EventType.TASK_STATUS_CHANGED, project_id, task_id, {
            "old_status": task.status.value,
            "new_status": update_data["status"].value
        })
    else:
        event_data = update_data.copy()
        if significant_edit:
            event_data['new_version'] = new_version_num
            event_data['version_id'] = task_version.id
        emit_task_event(EventType.TASK_UPDATED, project_id, task_id, event_data)
    
    return updated_task


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


@router.get("/{task_id}/versions", response_model=List[TaskVersionResponse])
async def get_task_versions(task_id: int, db: Session = Depends(lambda: next(get_db(1)))):
    """Get all versions of a task"""
    task = dao.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    versions = dao.list_task_versions(db, task_id)
    return versions


@router.post("/{task_id}/split")
async def split_task(
    task_id: int, 
    project_id: int,
    split_request: TaskSplitRequest,
    db: Session = Depends(lambda: next(get_db(1)))
):
    """Split a task into two new tasks"""
    # Get the original task
    task = dao.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # Create two new tasks
    task1 = dao.create_task(
        db=db,
        project_id=project_id,
        title=split_request.task1_title,
        description=split_request.task1_description,
        priority=task.priority
    )
    
    task2 = dao.create_task(
        db=db,
        project_id=project_id,
        title=split_request.task2_title,
        description=split_request.task2_description,
        priority=task.priority
    )
    
    # Mark original task as superseded
    import json
    extra_data = json.loads(task.extra_data) if task.extra_data else {}
    extra_data['superseded_by'] = [task1.id, task2.id]
    extra_data['split_reason'] = 'Task split into multiple tasks'
    
    dao.update_task(db, task_id, 
        status=TaskStatus.CANCELLED,
        extra_data=json.dumps(extra_data)
    )
    
    emit_task_event(EventType.TASK_UPDATED, project_id, task_id, {
        "action": "split",
        "new_tasks": [task1.id, task2.id]
    })
    
    return {
        "success": True,
        "original_task_id": task_id,
        "new_tasks": [
            {"id": task1.id, "title": task1.title},
            {"id": task2.id, "title": task2.title}
        ]
    }


@router.post("/merge")
async def merge_tasks(
    project_id: int,
    merge_request: TaskMergeRequest,
    db: Session = Depends(lambda: next(get_db(1)))
):
    """Merge multiple tasks into a single task"""
    import json
    
    if len(merge_request.task_ids) < 2:
        raise HTTPException(status_code=400, detail="Must provide at least 2 tasks to merge")
    
    # Validate all tasks exist
    tasks = []
    for task_id in merge_request.task_ids:
        task = dao.get_task(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        tasks.append(task)
    
    # Create merged task
    merged_task = dao.create_task(
        db=db,
        project_id=project_id,
        title=merge_request.merged_title,
        description=merge_request.merged_description,
        priority=max(t.priority for t in tasks)  # Use highest priority
    )
    
    # Mark source tasks as superseded
    for task in tasks:
        extra_data = json.loads(task.extra_data) if task.extra_data else {}
        extra_data['superseded_by'] = merged_task.id
        extra_data['merge_reason'] = 'Task merged with others'
        extra_data['merged_with'] = [t.id for t in tasks if t.id != task.id]
        
        dao.update_task(db, task.id,
            status=TaskStatus.CANCELLED,
            extra_data=json.dumps(extra_data)
        )
    
    emit_task_event(EventType.TASK_UPDATED, project_id, merged_task.id, {
        "action": "merge",
        "source_tasks": merge_request.task_ids
    })
    
    return {
        "success": True,
        "merged_task_id": merged_task.id,
        "merged_task_title": merged_task.title,
        "source_task_ids": merge_request.task_ids
    }

