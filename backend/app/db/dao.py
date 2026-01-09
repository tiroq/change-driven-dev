"""
Data Access Object (DAO) layer for database operations.
Provides CRUD operations for all entities.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.models.models import (
    Project, Task, ChangeRequest, Approval, Artifact,
    TaskVersion, Run, ControlState,
    TaskStatus, PhaseType, ChangeRequestStatus, ArtifactType, RunStatus
)


# ==================== PROJECT DAO ====================

def create_project(
    db: Session,
    name: str,
    description: Optional[str] = None,
    root_path: Optional[str] = None,
    default_engine: str = "copilot_cli"
) -> Project:
    """Create a new project"""
    project = Project(
        name=name,
        description=description,
        db_path="",  # Will be set by caller
        root_path=root_path,
        default_engine=default_engine
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project(db: Session, project_id: int) -> Optional[Project]:
    """Get project by ID"""
    return db.query(Project).filter(Project.id == project_id).first()


def get_project_by_name(db: Session, name: str) -> Optional[Project]:
    """Get project by name"""
    return db.query(Project).filter(Project.name == name).first()


def list_projects(db: Session, skip: int = 0, limit: int = 100) -> List[Project]:
    """List all projects"""
    return db.query(Project).offset(skip).limit(limit).all()


def update_project(db: Session, project_id: int, **kwargs) -> Optional[Project]:
    """Update project fields"""
    project = get_project(db, project_id)
    if not project:
        return None
    
    for key, value in kwargs.items():
        if hasattr(project, key):
            setattr(project, key, value)
    
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: int) -> bool:
    """Delete a project"""
    project = get_project(db, project_id)
    if not project:
        return False
    
    db.delete(project)
    db.commit()
    return True


# ==================== TASK DAO ====================

def create_task(
    db: Session,
    project_id: int,
    title: str,
    description: Optional[str] = None,
    status: TaskStatus = TaskStatus.PENDING,
    current_phase: Optional[PhaseType] = None,
    priority: int = 0
) -> Task:
    """Create a new task"""
    task = Task(
        project_id=project_id,
        title=title,
        description=description,
        status=status,
        current_phase=current_phase,
        priority=priority,
        version=1,
        attempts=0
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: int) -> Optional[Task]:
    """Get task by ID"""
    return db.query(Task).filter(Task.id == task_id).first()


def list_tasks(
    db: Session,
    project_id: Optional[int] = None,
    status: Optional[TaskStatus] = None,
    phase: Optional[PhaseType] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Task]:
    """List tasks with optional filters"""
    query = db.query(Task)
    
    if project_id is not None:
        query = query.filter(Task.project_id == project_id)
    if status is not None:
        query = query.filter(Task.status == status)
    if phase is not None:
        query = query.filter(Task.current_phase == phase)
    
    return query.order_by(desc(Task.priority), Task.created_at).offset(skip).limit(limit).all()


def update_task(db: Session, task_id: int, **kwargs) -> Optional[Task]:
    """Update task fields"""
    task = get_task(db, task_id)
    if not task:
        return None
    
    for key, value in kwargs.items():
        if hasattr(task, key):
            setattr(task, key, value)
    
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task_id: int) -> bool:
    """Delete a task"""
    task = get_task(db, task_id)
    if not task:
        return False
    
    db.delete(task)
    db.commit()
    return True


def get_next_approved_task(db: Session, project_id: int) -> Optional[Task]:
    """Get next APPROVED task with deps satisfied (for coder phase)"""
    return db.query(Task).filter(
        Task.project_id == project_id,
        Task.status == TaskStatus.APPROVED
    ).order_by(desc(Task.priority), Task.created_at).first()


# ==================== TASK VERSION DAO ====================

def create_task_version(
    db: Session,
    task_id: int,
    version_num: int,
    title: str,
    description: Optional[str] = None,
    gates_json: Optional[str] = None,
    deps_json: Optional[str] = None,
    extra_data: Optional[str] = None
) -> TaskVersion:
    """Create a new task version"""
    version = TaskVersion(
        task_id=task_id,
        version_num=version_num,
        title=title,
        description=description,
        gates_json=gates_json,
        deps_json=deps_json,
        extra_data=extra_data
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


def get_task_version(db: Session, version_id: int) -> Optional[TaskVersion]:
    """Get task version by ID"""
    return db.query(TaskVersion).filter(TaskVersion.id == version_id).first()


def list_task_versions(db: Session, task_id: int) -> List[TaskVersion]:
    """List all versions for a task"""
    return db.query(TaskVersion).filter(
        TaskVersion.task_id == task_id
    ).order_by(TaskVersion.version_num).all()


def get_latest_task_version(db: Session, task_id: int) -> Optional[TaskVersion]:
    """Get latest version for a task"""
    return db.query(TaskVersion).filter(
        TaskVersion.task_id == task_id
    ).order_by(desc(TaskVersion.version_num)).first()


# ==================== CHANGE REQUEST DAO ====================

def create_change_request(
    db: Session,
    task_id: int,
    phase: PhaseType,
    content: str,
    status: ChangeRequestStatus = ChangeRequestStatus.DRAFT,
    version: int = 1
) -> ChangeRequest:
    """Create a new change request"""
    cr = ChangeRequest(
        task_id=task_id,
        phase=phase,
        content=content,
        status=status,
        version=version
    )
    db.add(cr)
    db.commit()
    db.refresh(cr)
    return cr


def get_change_request(db: Session, cr_id: int) -> Optional[ChangeRequest]:
    """Get change request by ID"""
    return db.query(ChangeRequest).filter(ChangeRequest.id == cr_id).first()


def list_change_requests(
    db: Session,
    task_id: Optional[int] = None,
    status: Optional[ChangeRequestStatus] = None,
    skip: int = 0,
    limit: int = 100
) -> List[ChangeRequest]:
    """List change requests with optional filters"""
    query = db.query(ChangeRequest)
    
    if task_id is not None:
        query = query.filter(ChangeRequest.task_id == task_id)
    if status is not None:
        query = query.filter(ChangeRequest.status == status)
    
    return query.order_by(desc(ChangeRequest.created_at)).offset(skip).limit(limit).all()


def update_change_request(db: Session, cr_id: int, **kwargs) -> Optional[ChangeRequest]:
    """Update change request fields"""
    cr = get_change_request(db, cr_id)
    if not cr:
        return None
    
    for key, value in kwargs.items():
        if hasattr(cr, key):
            setattr(cr, key, value)
    
    db.commit()
    db.refresh(cr)
    return cr


def submit_change_request(db: Session, cr_id: int) -> Optional[ChangeRequest]:
    """Submit a change request for approval"""
    return update_change_request(db, cr_id, status=ChangeRequestStatus.SUBMITTED)


def approve_change_request(db: Session, cr_id: int) -> Optional[ChangeRequest]:
    """Approve a change request"""
    return update_change_request(db, cr_id, status=ChangeRequestStatus.APPROVED)


def reject_change_request(db: Session, cr_id: int) -> Optional[ChangeRequest]:
    """Reject a change request"""
    return update_change_request(db, cr_id, status=ChangeRequestStatus.REJECTED)


# ==================== APPROVAL DAO ====================

def create_approval(
    db: Session,
    task_id: int,
    approver: str,
    approved: bool,
    change_request_id: Optional[int] = None,
    comment: Optional[str] = None
) -> Approval:
    """Create a new approval record"""
    approval = Approval(
        task_id=task_id,
        change_request_id=change_request_id,
        approver=approver,
        approved=approved,
        comment=comment
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)
    return approval


def get_approval(db: Session, approval_id: int) -> Optional[Approval]:
    """Get approval by ID"""
    return db.query(Approval).filter(Approval.id == approval_id).first()


def list_approvals(
    db: Session,
    task_id: Optional[int] = None,
    change_request_id: Optional[int] = None
) -> List[Approval]:
    """List approvals with optional filters"""
    query = db.query(Approval)
    
    if task_id is not None:
        query = query.filter(Approval.task_id == task_id)
    if change_request_id is not None:
        query = query.filter(Approval.change_request_id == change_request_id)
    
    return query.order_by(desc(Approval.created_at)).all()


# ==================== ARTIFACT DAO ====================

def create_artifact(
    db: Session,
    project_id: int,
    artifact_type: ArtifactType,
    name: str,
    file_path: str,
    task_id: Optional[int] = None,
    run_id: Optional[int] = None,
    sha256: Optional[str] = None,
    extra_data: Optional[str] = None
) -> Artifact:
    """Create a new artifact"""
    artifact = Artifact(
        project_id=project_id,
        task_id=task_id,
        run_id=run_id,
        artifact_type=artifact_type,
        name=name,
        file_path=file_path,
        sha256=sha256,
        extra_data=extra_data
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact


def get_artifact(db: Session, artifact_id: int) -> Optional[Artifact]:
    """Get artifact by ID"""
    return db.query(Artifact).filter(Artifact.id == artifact_id).first()


def list_artifacts(
    db: Session,
    project_id: Optional[int] = None,
    task_id: Optional[int] = None,
    run_id: Optional[int] = None,
    artifact_type: Optional[ArtifactType] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Artifact]:
    """List artifacts with optional filters"""
    query = db.query(Artifact)
    
    if project_id is not None:
        query = query.filter(Artifact.project_id == project_id)
    if task_id is not None:
        query = query.filter(Artifact.task_id == task_id)
    if run_id is not None:
        query = query.filter(Artifact.run_id == run_id)
    if artifact_type is not None:
        query = query.filter(Artifact.artifact_type == artifact_type)
    
    return query.order_by(desc(Artifact.created_at)).offset(skip).limit(limit).all()


def delete_artifact(db: Session, artifact_id: int) -> bool:
    """Delete an artifact"""
    artifact = get_artifact(db, artifact_id)
    if not artifact:
        return False
    
    db.delete(artifact)
    db.commit()
    return True


# ==================== RUN DAO ====================

def create_run(
    db: Session,
    task_id: int,
    engine: str,
    log_path: Optional[str] = None,
    extra_data: Optional[str] = None
) -> Run:
    """Create a new run"""
    run = Run(
        task_id=task_id,
        engine=engine,
        status=RunStatus.RUNNING,
        log_path=log_path,
        extra_data=extra_data,
        start_time=datetime.utcnow()
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_run(db: Session, run_id: int) -> Optional[Run]:
    """Get run by ID"""
    return db.query(Run).filter(Run.id == run_id).first()


def list_runs(
    db: Session,
    task_id: Optional[int] = None,
    status: Optional[RunStatus] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Run]:
    """List runs with optional filters"""
    query = db.query(Run)
    
    if task_id is not None:
        query = query.filter(Run.task_id == task_id)
    if status is not None:
        query = query.filter(Run.status == status)
    
    return query.order_by(desc(Run.start_time)).offset(skip).limit(limit).all()


def update_run(db: Session, run_id: int, **kwargs) -> Optional[Run]:
    """Update run fields"""
    run = get_run(db, run_id)
    if not run:
        return None
    
    for key, value in kwargs.items():
        if hasattr(run, key):
            setattr(run, key, value)
    
    # Set end_time if status is final
    if 'status' in kwargs and kwargs['status'] in [RunStatus.SUCCESS, RunStatus.FAILURE, RunStatus.TIMEOUT, RunStatus.CANCELLED]:
        run.end_time = datetime.utcnow()
    
    db.commit()
    db.refresh(run)
    return run


def complete_run(db: Session, run_id: int, status: RunStatus, gate_results: Optional[str] = None) -> Optional[Run]:
    """Complete a run with final status and gate results"""
    return update_run(db, run_id, status=status, gate_results=gate_results)


# ==================== CONTROL STATE DAO ====================

def create_control_state(
    db: Session,
    project_id: int,
    max_attempts: int = 3,
    timeout_seconds: int = 300
) -> ControlState:
    """Create control state for a project"""
    control = ControlState(
        project_id=project_id,
        paused=False,
        max_attempts=max_attempts,
        timeout_seconds=timeout_seconds
    )
    db.add(control)
    db.commit()
    db.refresh(control)
    return control


def get_control_state(db: Session, project_id: int) -> Optional[ControlState]:
    """Get control state for a project"""
    return db.query(ControlState).filter(ControlState.project_id == project_id).first()


def update_control_state(db: Session, project_id: int, **kwargs) -> Optional[ControlState]:
    """Update control state fields"""
    control = get_control_state(db, project_id)
    if not control:
        # Create if doesn't exist
        control = create_control_state(db, project_id)
    
    for key, value in kwargs.items():
        if hasattr(control, key):
            setattr(control, key, value)
    
    db.commit()
    db.refresh(control)
    return control


def pause_execution(db: Session, project_id: int) -> Optional[ControlState]:
    """Pause execution for a project"""
    return update_control_state(db, project_id, paused=True)


def resume_execution(db: Session, project_id: int) -> Optional[ControlState]:
    """Resume execution for a project"""
    return update_control_state(db, project_id, paused=False)
