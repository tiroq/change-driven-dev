"""
API routes for artifacts.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from pathlib import Path

from app.db import get_db
from app.db import dao
from app.models import ArtifactType
from app.core.events import EventType, Event, event_bus
from app.services.artifacts import artifact_storage

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])


class ArtifactCreate(BaseModel):
    """Artifact creation schema"""
    project_id: int
    artifact_type: ArtifactType
    name: str
    file_path: str
    task_id: Optional[int] = None
    run_id: Optional[int] = None
    sha256: Optional[str] = None
    extra_data: Optional[str] = None


class ArtifactResponse(BaseModel):
    """Artifact response schema"""
    id: int
    project_id: int
    task_id: Optional[int]
    run_id: Optional[int]
    artifact_type: ArtifactType
    name: str
    file_path: str
    sha256: Optional[str]
    extra_data: Optional[str]
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[ArtifactResponse])
async def list_artifacts(
    project_id: Optional[int] = None,
    task_id: Optional[int] = None,
    run_id: Optional[int] = None,
    artifact_type: Optional[ArtifactType] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(lambda: next(get_db(1)))
):
    """List artifacts with optional filters"""
    artifacts = dao.list_artifacts(
        db,
        project_id=project_id,
        task_id=task_id,
        run_id=run_id,
        artifact_type=artifact_type,
        skip=skip,
        limit=limit
    )
    return artifacts


@router.post("/", response_model=ArtifactResponse)
async def create_artifact(artifact: ArtifactCreate, db: Session = Depends(lambda: next(get_db(1)))):
    """Create a new artifact (metadata only)"""
    new_artifact = dao.create_artifact(
        db,
        project_id=artifact.project_id,
        artifact_type=artifact.artifact_type,
        name=artifact.name,
        file_path=artifact.file_path,
        task_id=artifact.task_id,
        run_id=artifact.run_id,
        sha256=artifact.sha256,
        extra_data=artifact.extra_data
    )
    
    # Emit event
    event = Event(
        event_type=EventType.ARTIFACT_CREATED,
        project_id=artifact.project_id,
        task_id=artifact.task_id,
        data={
            "artifact_id": new_artifact.id,
            "name": new_artifact.name,
            "type": new_artifact.artifact_type.value
        }
    )
    event_bus.publish(event)
    
    return new_artifact


@router.post("/upload")
async def upload_artifact(
    file: UploadFile = File(...),
    project_id: int = Form(...),
    artifact_type: str = Form(...),
    task_id: Optional[int] = Form(None),
    run_id: Optional[int] = Form(None),
    db: Session = Depends(lambda: next(get_db(1)))
):
    """Upload an artifact file"""
    try:
        # Store artifact using storage service
        artifact_dict = await artifact_storage.store_artifact(
            session=db,
            project_id=project_id,
            task_id=task_id,
            run_id=run_id,
            artifact_type=artifact_type,
            file_path=file.filename,
            file_obj=file.file,
            extra_data={"original_filename": file.filename, "content_type": file.content_type}
        )
        
        # Emit event
        event = Event(
            event_type=EventType.ARTIFACT_CREATED,
            project_id=project_id,
            task_id=task_id,
            data={
                "artifact_id": artifact_dict["id"],
                "file_path": artifact_dict["file_path"],
                "type": artifact_type,
                "size": artifact_dict["file_size"]
            }
        )
        event_bus.publish(event)
        
        return artifact_dict
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload artifact: {str(e)}")


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(artifact_id: int, db: Session = Depends(lambda: next(get_db(1)))):
    """Get an artifact by ID"""
    artifact = dao.get_artifact(db, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail=f"Artifact {artifact_id} not found")
    return artifact


@router.get("/{artifact_id}/download")
async def download_artifact(artifact_id: int, db: Session = Depends(lambda: next(get_db(1)))):
    """Download an artifact file"""
    try:
        artifact_dict, file_path = await artifact_storage.retrieve_artifact(db, artifact_id)
        
        # Verify file integrity
        if artifact_dict.get("sha256"):
            if not artifact_storage.verify_artifact(file_path, artifact_dict["sha256"]):
                raise HTTPException(status_code=500, detail="Artifact file integrity check failed")
        
        return FileResponse(
            path=file_path,
            filename=Path(artifact_dict["file_path"]).name,
            media_type="application/octet-stream"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{artifact_id}/content")
async def get_artifact_content(artifact_id: int, db: Session = Depends(lambda: next(get_db(1)))):
    """Get artifact content (text files only)"""
    try:
        artifact_dict, file_path = await artifact_storage.retrieve_artifact(db, artifact_id)
        
        # Check file size (limit to 1MB for text content)
        if artifact_dict["file_size"] > 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large for text content display")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {
                "content": content,
                "file_path": artifact_dict["file_path"],
                "type": artifact_dict["artifact_type"]
            }
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File is not a text file")
            
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{artifact_id}")
async def delete_artifact(artifact_id: int, db: Session = Depends(lambda: next(get_db(1)))):
    """Delete an artifact"""
    artifact = dao.get_artifact(db, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail=f"Artifact {artifact_id} not found")
    
    project_id = artifact.project_id
    
    # Delete physical file if it exists
    if artifact.storage_path:
        storage_path = Path(artifact.storage_path)
        if storage_path.exists():
            # Use storage service for cleanup
            filename = storage_path.name
            artifact_storage.delete_artifact_file(project_id, artifact_id, filename)
    
    # Delete database record
    success = dao.delete_artifact(db, artifact_id)
    
    if success:
        # Emit event
        event = Event(
            event_type=EventType.ARTIFACT_DELETED,
            project_id=project_id,
            data={"artifact_id": artifact_id}
        )
        event_bus.publish(event)
    
    return {"success": True, "message": f"Artifact {artifact_id} deleted"}
