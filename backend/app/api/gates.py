"""
API routes for gate management and execution.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import json

from app.db import get_db, get_db_session
from app.db import dao
from app.core.gates import GateSpec, GateRunner, GateResult
from app.core.sandbox import CommandRunner
from app.core.config import ProjectConfig
from pathlib import Path

router = APIRouter(prefix="/api/gates", tags=["gates"])


class GateSpecRequest(BaseModel):
    """Request to create or update gate specification"""
    name: str
    description: Optional[str] = None
    command: str
    pass_criteria: str = "exit_code_0"
    expected_output: Optional[str] = None
    timeout: int = 60
    fail_task_on_error: bool = True
    required: bool = True


class GateExecutionRequest(BaseModel):
    """Request to execute gates for a task"""
    task_id: int
    project_id: int
    stop_on_failure: bool = False


@router.get("/task/{task_id}", response_model=List[dict])
async def get_task_gates(task_id: int, db: Session = Depends(get_db_session)):
    """
    Get gates configured for a task.
    Gates are stored in the latest TaskVersion.gates_json field.
    """
    # Get latest task version
    latest_version = dao.get_latest_task_version(db, task_id)
    
    if not latest_version or not latest_version.gates_json:
        return []
    
    try:
        gates_data = json.loads(latest_version.gates_json)
        return gates_data
    except json.JSONDecodeError:
        return []


@router.put("/task/{task_id}")
async def update_task_gates(
    task_id: int,
    project_id: int,
    gates: List[GateSpecRequest]
):
    """
    Update gates for a task.
    Creates a new TaskVersion with updated gates_json.
    """
    db = next(get_db(project_id))
    task = dao.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # Convert gates to JSON
    gates_json = json.dumps([g.dict() for g in gates])
    
    # Create new task version with gates
    new_version_num = task.version + 1
    
    task_version = dao.create_task_version(
        db=db,
        task_id=task_id,
        version_num=new_version_num,
        title=task.title,
        description=task.description,
        gates_json=gates_json,
        deps_json=None,
        extra_data=None
    )
    
    # Update task
    dao.update_task(
        db,
        task_id,
        version=new_version_num,
        active_version_id=task_version.id
    )
    
    return {
        "success": True,
        "task_id": task_id,
        "version_id": task_version.id,
        "version_num": new_version_num,
        "gates_count": len(gates)
    }


@router.post("/execute")
async def execute_gates(
    request: GateExecutionRequest
):
    """
    Execute all gates for a task.
    Returns gate execution results.
    """
    db = next(get_db(request.project_id))
    
    # Get task
    task = dao.get_task(db, request.task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {request.task_id} not found")
    
    # Get project
    project = dao.get_project(db, request.project_id)
    
    # Get gates from latest task version
    latest_version = dao.get_latest_task_version(db, request.task_id)
    
    if not latest_version or not latest_version.gates_json:
        return {
            "success": True,
            "message": "No gates configured for this task",
            "results": []
        }
    
    try:
        gates_data = json.loads(latest_version.gates_json)
        gate_specs = [GateSpec(**g) for g in gates_data]
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid gates configuration: {str(e)}"
        )
    
    # Load project config for sandbox settings
    project = dao.get_project(db, request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {request.project_id} not found")
    
    if not project.root_path:
        raise HTTPException(status_code=400, detail="Project root path not configured")
    
    try:
        config = ProjectConfig.load_from_project(Path(project.root_path))
        allowed_commands = config.get_allowed_commands()
        blocked_commands = config.get_blocked_commands()
    except Exception:
        # Use defaults if config loading fails
        allowed_commands = None
        blocked_commands = set()
    
    # Create command runner with project config
    cmd_runner = CommandRunner(
        allowed_commands=allowed_commands,
        blocked_commands=blocked_commands,
        default_timeout=300
    )
    
    # Create gate runner
    gate_runner = GateRunner(command_runner=cmd_runner)
    
    # Execute gates
    try:
        results = await gate_runner.run_gates(
            gates=gate_specs,
            cwd=project.root_path,
            stop_on_failure=request.stop_on_failure
        )
        
        # Get summary
        summary = gate_runner.get_summary(results)
        
        # Convert results to dict for JSON serialization
        results_dict = [r.dict() for r in results]
        
        return {
            "success": True,
            "task_id": request.task_id,
            "results": results_dict,
            "summary": summary,
            "all_passed": summary["all_passed"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gate execution failed: {str(e)}"
        )


@router.get("/examples", response_model=List[dict])
async def get_example_gates():
    """Get example gate configurations."""
    from app.core.gates import EXAMPLE_GATES
    return [g.dict() for g in EXAMPLE_GATES]
