"""
API routes for Git integration.
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel

from app.db import get_db
from app.db import dao
from app.services.git_service import GitService

router = APIRouter(prefix="/api/git", tags=["git"])


class GitCommitRequest(BaseModel):
    """Request to create a git commit"""
    project_id: int
    message: str
    author_name: Optional[str] = None
    author_email: Optional[str] = None


@router.get("/status")
async def get_git_status(project_id: int):
    """
    Get git status for a project.
    
    Returns repository status including staged/unstaged files and branch info.
    """
    db = next(get_db(project_id))
    project = dao.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    
    if not project.root_path:
        raise HTTPException(status_code=400, detail="Project root path not configured")
    
    git_service = GitService(project.root_path)
    
    try:
        status = await git_service.get_status()
        return status.dict()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get git status: {str(e)}"
        )


@router.post("/init")
async def init_repository(project_id: int, initial_branch: str = "main"):
    """
    Initialize a git repository for a project.
    
    Creates a new git repository in the project's root directory.
    """
    db = next(get_db(project_id))
    project = dao.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    
    if not project.root_path:
        raise HTTPException(status_code=400, detail="Project root path not configured")
    
    git_service = GitService(project.root_path)
    
    try:
        await git_service.init(initial_branch=initial_branch)
        status = await git_service.get_status()
        
        return {
            "success": True,
            "message": f"Repository initialized with branch '{initial_branch}'",
            "status": status.dict()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize repository: {str(e)}"
        )


@router.post("/commit")
async def create_commit(request: GitCommitRequest):
    """
    Create a git commit with all staged changes.
    
    Commits currently staged changes with the provided message.
    """
    db = next(get_db(request.project_id))
    project = dao.get_project(db, request.project_id)
    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"Project {request.project_id} not found"
        )
    
    if not project.root_path:
        raise HTTPException(status_code=400, detail="Project root path not configured")
    
    git_service = GitService(project.root_path)
    
    try:
        # Check if repo exists
        if not await git_service.is_repo():
            raise HTTPException(
                status_code=400,
                detail="Project is not a git repository. Initialize it first."
            )
        
        # Stage all changes and commit
        sha = await git_service.commit_all(
            message=request.message,
            author_name=request.author_name,
            author_email=request.author_email
        )
        
        # Get updated status
        status = await git_service.get_status()
        
        return {
            "success": True,
            "commit_sha": sha,
            "message": request.message,
            "status": status.dict()
        }
        
    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create commit: {str(e)}"
        )


@router.get("/diff")
async def get_diff(project_id: int, staged: bool = False):
    """
    Get diff of changes in the repository.
    
    Args:
        staged: If true, shows staged changes; if false, shows unstaged changes
    """
    db = next(get_db(project_id))
    project = dao.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    
    if not project.root_path:
        raise HTTPException(status_code=400, detail="Project root path not configured")
    
    git_service = GitService(project.root_path)
    
    try:
        if not await git_service.is_repo():
            raise HTTPException(
                status_code=400,
                detail="Project is not a git repository"
            )
        
        diff = await git_service.get_diff(cached=staged)
        
        return {
            "success": True,
            "diff": diff,
            "staged": staged
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get diff: {str(e)}"
        )


@router.get("/log")
async def get_git_log(project_id: int, max_count: int = 10):
    """
    Get git commit log.
    """
    db = next(get_db(project_id))
    project = dao.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    
    if not project.root_path:
        raise HTTPException(status_code=400, detail="Project root path not configured")
    
    git_service = GitService(project.root_path)
    
    try:
        if not await git_service.is_repo():
            return {
                "success": False,
                "message": "Project is not a git repository"
            }
        
        commit_info = await git_service.get_last_commit()
        
        if not commit_info:
            return {
                "success": False,
                "message": "No commits found",
                "commits": []
            }
        
        return {
            "success": True,
            "commits": [commit_info.dict()]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get commit log: {str(e)}"
        )
