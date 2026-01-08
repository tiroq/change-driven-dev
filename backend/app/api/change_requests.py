"""
API routes for change requests.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.db import get_db
from app.models import ChangeRequest, ChangeRequestStatus, PhaseType

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
async def list_change_requests(task_id: Optional[int] = None, db: Session = Depends(get_db)):
    """List all change requests, optionally filtered by task"""
    # Placeholder - returns empty list
    return []


@router.post("/", response_model=ChangeRequestResponse)
async def create_change_request(cr: ChangeRequestCreate, db: Session = Depends(get_db)):
    """Create a new change request"""
    # Placeholder - returns mock response
    return {
        "id": 1,
        "task_id": cr.task_id,
        "phase": cr.phase,
        "content": cr.content,
        "status": ChangeRequestStatus.DRAFT,
        "version": 1
    }


@router.get("/{cr_id}", response_model=ChangeRequestResponse)
async def get_change_request(cr_id: int, db: Session = Depends(get_db)):
    """Get a change request by ID"""
    # Placeholder - returns mock response
    return {
        "id": cr_id,
        "task_id": 1,
        "phase": PhaseType.PLANNER,
        "content": "Sample change request content",
        "status": ChangeRequestStatus.DRAFT,
        "version": 1
    }


@router.post("/{cr_id}/submit")
async def submit_change_request(cr_id: int, db: Session = Depends(get_db)):
    """Submit a change request for approval"""
    # Placeholder - returns mock response
    return {
        "id": cr_id,
        "status": ChangeRequestStatus.SUBMITTED,
        "message": "Change request submitted for approval"
    }


@router.post("/{cr_id}/approve")
async def approve_change_request(cr_id: int, db: Session = Depends(get_db)):
    """Approve a change request"""
    # Placeholder - returns mock response
    return {
        "id": cr_id,
        "status": ChangeRequestStatus.APPROVED,
        "message": "Change request approved"
    }


@router.post("/{cr_id}/reject")
async def reject_change_request(cr_id: int, db: Session = Depends(get_db)):
    """Reject a change request"""
    # Placeholder - returns mock response
    return {
        "id": cr_id,
        "status": ChangeRequestStatus.REJECTED,
        "message": "Change request rejected"
    }
