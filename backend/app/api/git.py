"""
API routes for Git integration.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.db import get_db
from app.db import dao
from app.services.git_service import GitService, GitStatus

router = APIRouter(prefix="/api/git", tags=["git"])


class CommitRequest(BaseModel):
    """Request to create a commit"""
    project_id: int
    message: str
    author_name: Optional[str] = None
    author_email: Optional[str] = None


@router.get("/status/{project_id}")
async def get_git_status(
    project_id: int,
    db: Session = Depends(lambda: next(get_db(project_id)))
):
    """
    Get git status for a project.
    
    Returns repository status including staged/unstaged files and branch info.
    """
    project = dao.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    
    git_service = GitService(project.root_path)
    
    try:
        status = await git_service.get_status()
        return status.dict()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get git status: {str(e)}"
        )


@router.post("/init/{project_id}")
async def init_repository(
    project_id: int,
    initial_branch: str = "main",
    db: Session = Depends(lambda: next(get_db(project_id)))
):
    """
    Initialize a git repository for a project.
    
    Creates a new git repository in the project's root directory.
    """
    project = dao.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    
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
async def create_commit(
    request: CommitRequest,
    db: Session = Depends(lambda: next(get_db(request.project_id)))
):
    """
    Create a git commit with all staged changes.
    
    Commits currently staged changes with the provided message.
    """
    project = dao.get_project(db, request.project_id)
    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"Project {request.project_id} not found"
        )
    
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


@router.get("/diff/{project_id}")
async def get_diff(
    project_id: int,
    cached: bool = False,
    db: Session = Depends(lambda: next(get_db(project_id)))
):
    """
    Get diff of changes in the repository.
    
    Args:
        cached: If true, shows staged changes; if false, shows unstaged changes
    """
    project = dao.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    
    git_service = GitService(project.root_path)
    
    try:
        if not await git_service.is_repo():
            raise HTTPException(
                status_code=400,
                detail="Project is not a git repository"
            )
        
        diff = await git_service.get_diff(cached=cached)
        
        return {
            "success": True,
            "diff": diff,
            "cached": cached
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get diff: {str(e)}"
        )


@router.get("/last-commit/{project_id}")
async def get_last_commit(
    project_id: int,
    db: Session = Depends(lambda: next(get_db(project_id)))
):
    """
    Get information about the last commit.
    """
    project = dao.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    
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
                "message": "No commits found"
            }
        
        return {
            "success": True,
            "commit": commit_info.dict()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get last commit: {str(e)}"
        )
