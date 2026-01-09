"""
Artifact storage service for managing files and their metadata.
"""
import hashlib
import os
from pathlib import Path
from typing import Optional, BinaryIO

from ..db.dao import create_artifact, get_artifact, delete_artifact
from ..models.models import ArtifactType


class ArtifactStorageService:
    """
    Service for managing artifact file storage and retrieval.
    Stores artifacts in a project-specific directory structure.
    """

    def __init__(self, base_storage_path: str = "./artifacts"):
        """
        Initialize artifact storage service.
        
        Args:
            base_storage_path: Base directory for all artifact storage
        """
        self.base_storage_path = Path(base_storage_path)
        self.base_storage_path.mkdir(parents=True, exist_ok=True)

    def get_project_storage_path(self, project_id: int) -> Path:
        """
        Get storage directory for a specific project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Path to project's artifact directory
        """
        project_path = self.base_storage_path / f"project_{project_id}"
        project_path.mkdir(parents=True, exist_ok=True)
        return project_path

    def get_artifact_path(self, project_id: int, artifact_id: int, filename: str) -> Path:
        """
        Get full path for an artifact file.
        
        Args:
            project_id: ID of the project
            artifact_id: ID of the artifact
            filename: Name of the file
            
        Returns:
            Full path to artifact file
        """
        project_path = self.get_project_storage_path(project_id)
        # Use artifact_id as subdirectory to avoid filename conflicts
        artifact_path = project_path / f"artifact_{artifact_id}"
        artifact_path.mkdir(parents=True, exist_ok=True)
        return artifact_path / filename

    def compute_sha256(self, file_obj: BinaryIO) -> str:
        """
        Compute SHA256 hash of file contents.
        
        Args:
            file_obj: File object to hash
            
        Returns:
            Hexadecimal SHA256 hash string
        """
        sha256_hash = hashlib.sha256()
        # Read in chunks to handle large files
        for chunk in iter(lambda: file_obj.read(4096), b""):
            sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def store_artifact(
        self,
        session,
        project_id: int,
        task_id: Optional[int],
        run_id: Optional[int],
        artifact_type: str,
        file_path: str,
        file_obj: BinaryIO,
        extra_data: Optional[dict] = None
    ) -> dict:
        """
        Store an artifact file and create database record.
        
        Args:
            session: Database session
            project_id: ID of the project
            task_id: Optional ID of associated task
            run_id: Optional ID of associated run
            artifact_type: Type of artifact (e.g., 'plan', 'code', 'diff')
            file_path: Original file path/name
            file_obj: File object containing artifact data
            extra_data: Optional metadata dictionary
            
        Returns:
            Created artifact record as dict
        """
        # Compute hash first
        file_obj.seek(0)
        sha256_hash = self.compute_sha256(file_obj)
        
        # Get filename for storage
        filename = Path(file_path).name
        
        # Create initial artifact record with placeholder ID
        # We'll use a temporary approach: create with file_path, then update storage_path
        temp_artifact = create_artifact(
            db=session,
            project_id=project_id,
            artifact_type=ArtifactType(artifact_type),
            name=filename,
            file_path=file_path,
            task_id=task_id,
            run_id=run_id,
            sha256=sha256_hash,
            extra_data=str(extra_data or {})
        )
        
        try:
            # Store file using the artifact ID
            file_obj.seek(0)
            storage_path = self.get_artifact_path(project_id, temp_artifact.id, filename)
            
            with open(storage_path, 'wb') as f:
                for chunk in iter(lambda: file_obj.read(4096), b""):
                    f.write(chunk)
            
            file_size = storage_path.stat().st_size
            
            # Update the artifact record with storage info
            # Direct update since no update_artifact function exists
            temp_artifact.storage_path = str(storage_path)
            temp_artifact.file_size = file_size
            session.commit()
            session.refresh(temp_artifact)
            
            return {
                "id": temp_artifact.id,
                "project_id": temp_artifact.project_id,
                "task_id": temp_artifact.task_id,
                "run_id": temp_artifact.run_id,
                "artifact_type": temp_artifact.artifact_type.value,
                "file_path": temp_artifact.file_path,
                "storage_path": temp_artifact.storage_path,
                "sha256": temp_artifact.sha256,
                "file_size": temp_artifact.file_size,
                "extra_data": temp_artifact.extra_data,
                "created_at": temp_artifact.created_at.isoformat()
            }
            
        except Exception as e:
            # Clean up artifact record if file storage fails
            delete_artifact(session, temp_artifact.id)
            raise RuntimeError(f"Failed to store artifact file: {str(e)}") from e

    def retrieve_artifact(self, session, artifact_id: int) -> tuple[dict, Path]:
        """
        Retrieve artifact metadata and file path.
        
        Args:
            session: Database session
            artifact_id: ID of the artifact
            
        Returns:
            Tuple of (artifact dict, file path)
            
        Raises:
            FileNotFoundError: If artifact file doesn't exist
        """
        artifact = get_artifact(session, artifact_id)
        if not artifact:
            raise ValueError(f"Artifact {artifact_id} not found")
        
        if not artifact.storage_path:
            raise ValueError(f"Artifact {artifact_id} has no storage path")
        
        storage_path = Path(artifact.storage_path)
        if not storage_path.exists():
            raise FileNotFoundError(f"Artifact file not found: {storage_path}")
        
        artifact_dict = {
            "id": artifact.id,
            "project_id": artifact.project_id,
            "task_id": artifact.task_id,
            "run_id": artifact.run_id,
            "artifact_type": artifact.artifact_type.value,
            "file_path": artifact.file_path,
            "storage_path": artifact.storage_path,
            "sha256": artifact.sha256,
            "file_size": artifact.file_size,
            "extra_data": artifact.extra_data,
            "created_at": artifact.created_at.isoformat()
        }
        
        return artifact_dict, storage_path

    def verify_artifact(self, file_path: Path, expected_sha256: str) -> bool:
        """
        Verify artifact file integrity by comparing SHA256 hash.
        
        Args:
            file_path: Path to artifact file
            expected_sha256: Expected SHA256 hash
            
        Returns:
            True if hash matches, False otherwise
        """
        if not file_path.exists():
            return False
        
        with open(file_path, 'rb') as f:
            actual_sha256 = self.compute_sha256(f)
        
        return actual_sha256 == expected_sha256

    def delete_artifact_file(self, project_id: int, artifact_id: int, filename: str) -> bool:
        """
        Delete artifact file from storage.
        
        Args:
            project_id: ID of the project
            artifact_id: ID of the artifact
            filename: Name of the file
            
        Returns:
            True if file was deleted, False if file didn't exist
        """
        artifact_path = self.get_artifact_path(project_id, artifact_id, filename)
        
        if artifact_path.exists():
            artifact_path.unlink()
            # Try to remove parent directory if empty
            try:
                artifact_path.parent.rmdir()
            except OSError:
                pass  # Directory not empty or other error
            return True
        
        return False

    def cleanup_project_artifacts(self, project_id: int) -> int:
        """
        Delete all artifact files for a project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Number of files deleted
        """
        project_path = self.get_project_storage_path(project_id)
        deleted_count = 0
        
        if project_path.exists():
            for item in project_path.rglob('*'):
                if item.is_file():
                    item.unlink()
                    deleted_count += 1
            
            # Remove the project directory
            try:
                import shutil
                shutil.rmtree(project_path)
            except OSError:
                pass  # Directory not empty or other error
        
        return deleted_count


# Global instance
artifact_storage = ArtifactStorageService()
