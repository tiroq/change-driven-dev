"""
API routes for phase execution (planner, architect, coder).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.db import get_db
from app.services.orchestration import orchestration_service

router = APIRouter(prefix="/api/phase", tags=["phase"])


class PlanRequest(BaseModel):
    """Request to run planner phase"""
    project_id: int
    spec_content: str
    engine_name: Optional[str] = None


@router.post("/plan")
async def run_planner(request: PlanRequest, db: Session = Depends(lambda: next(get_db(request.project_id)))):
    """
    Execute planner phase for a project.
    
    Creates task breakdown from specification and produces plan.json artifact.
    """
    try:
        result = await orchestration_service.run_planner_phase(
            db=db,
            project_id=request.project_id,
            spec_content=request.spec_content,
            engine_name=request.engine_name
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Planner phase failed"))
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run planner: {str(e)}")
