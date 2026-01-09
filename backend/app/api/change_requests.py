"""
API routes for change requests.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.db import get_db
from app.db import dao
from app.models import ChangeRequestStatus, PhaseType
from app.core.events import EventType, Event, event_bus

router = APIRouter(prefix="/api/change-requests", tags=["change-requests"])


class ChangeRequestCreate(BaseModel):
    """Change request creation schema"""
    task_id: int
    phase: PhaseType
    content: str


class ChangeRequestResponse(BaseModel):
    """Change request response schema"""
    id: int
    task_id: int
    phase: PhaseType
    content: str
    status: ChangeRequestStatus
    version: int
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[ChangeRequestResponse])
async def list_change_requests(
    task_id: Optional[int] = None,
    status: Optional[ChangeRequestStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(lambda: next(get_db(1)))
):
    """List all change requests, optionally filtered by task"""
    crs = dao.list_change_requests(db, task_id=task_id, status=status, skip=skip, limit=limit)
    return crs


@router.post("/", response_model=ChangeRequestResponse)
async def create_change_request(cr: ChangeRequestCreate, db: Session = Depends(lambda: next(get_db(1)))):
    """Create a new change request"""
    # Get task to retrieve project_id
    task = dao.get_task(db, cr.task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {cr.task_id} not found")
    
    new_cr = dao.create_change_request(
        db,
        task_id=cr.task_id,
        phase=cr.phase,
        content=cr.content
    )
    
    event = Event(
        event_type=EventType.CHANGE_REQUEST_CREATED,
        project_id=task.project_id,
        task_id=cr.task_id,
        data={"cr_id": new_cr.id, "phase": cr.phase.value}
    )
    event_bus.publish(event)
    
    return new_cr


@router.get("/{cr_id}", response_model=ChangeRequestResponse)
async def get_change_request(cr_id: int, db: Session = Depends(lambda: next(get_db(1)))):
    """Get a change request by ID"""
    cr = dao.get_change_request(db, cr_id)
    if not cr:
        raise HTTPException(status_code=404, detail=f"Change request {cr_id} not found")
    return cr


@router.post("/{cr_id}/submit")
async def submit_change_request(cr_id: int, db: Session = Depends(lambda: next(get_db(1)))):
    """Submit a change request for approval"""
    cr = dao.get_change_request(db, cr_id)
    if not cr:
        raise HTTPException(status_code=404, detail=f"Change request {cr_id} not found")
    
    updated_cr = dao.submit_change_request(db, cr_id)
    
    task = dao.get_task(db, cr.task_id)
    event = Event(
        event_type=EventType.CHANGE_REQUEST_SUBMITTED,
        project_id=task.project_id if task else None,
        task_id=cr.task_id,
        data={"cr_id": cr_id}
    )
    event_bus.publish(event)
    
    return {
        "id": cr_id,
        "status": updated_cr.status.value,
        "message": "Change request submitted for approval"
    }


@router.post("/{cr_id}/approve")
async def approve_change_request(cr_id: int, approver: str = "system", db: Session = Depends(lambda: next(get_db(1)))):
    """Approve a change request"""
    cr = dao.get_change_request(db, cr_id)
    if not cr:
        raise HTTPException(status_code=404, detail=f"Change request {cr_id} not found")
    
    updated_cr = dao.approve_change_request(db, cr_id)
    
    # Create approval record
    dao.create_approval(db, task_id=cr.task_id, change_request_id=cr_id, approver=approver, approved=True)
    
    task = dao.get_task(db, cr.task_id)
    event = Event(
        event_type=EventType.CHANGE_REQUEST_APPROVED,
        project_id=task.project_id if task else None,
        task_id=cr.task_id,
        data={"cr_id": cr_id, "approver": approver}
    )
    event_bus.publish(event)
    
    return {
        "id": cr_id,
        "status": updated_cr.status.value,
        "message": "Change request approved"
    }


@router.post("/{cr_id}/reject")
async def reject_change_request(cr_id: int, approver: str = "system", reason: Optional[str] = None, db: Session = Depends(lambda: next(get_db(1)))):
    """Reject a change request"""
    cr = dao.get_change_request(db, cr_id)
    if not cr:
        raise HTTPException(status_code=404, detail=f"Change request {cr_id} not found")
    
    updated_cr = dao.reject_change_request(db, cr_id)
    
    # Create rejection record
    dao.create_approval(
        db,
        task_id=cr.task_id,
        change_request_id=cr_id,
        approver=approver,
        approved=False,
        comment=reason
    )
    
    task = dao.get_task(db, cr.task_id)
    event = Event(
        event_type=EventType.CHANGE_REQUEST_REJECTED,
        project_id=task.project_id if task else None,
        task_id=cr.task_id,
        data={"cr_id": cr_id, "approver": approver, "reason": reason}
    )
    event_bus.publish(event)
    
    return {
        "id": cr_id,
        "status": updated_cr.status.value,
        "message": "Change request rejected"
    }
