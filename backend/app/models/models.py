"""
Database models for change-driven-dev system.
Core concepts: Tasks, ChangeRequests, Approvals, Phases
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Enum as SQLEnum, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


class PhaseType(str, enum.Enum):
    """Phase types in the development workflow"""
    PLANNER = "planner"
    ARCHITECT = "architect"
    REVIEW_APPROVAL = "review_approval"
    CODER = "coder"


class TaskStatus(str, enum.Enum):
    """Task status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ChangeRequestStatus(str, enum.Enum):
    """Change request status enumeration"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


class ArtifactType(str, enum.Enum):
    """Artifact type enumeration"""
    SPEC = "spec"
    PLAN = "plan"
    ARCHITECTURE = "architecture"
    ADR = "adr"
    TRANSCRIPT = "transcript"
    DIFF = "diff"
    LOG = "log"
    OTHER = "other"


class RunStatus(str, enum.Enum):
    """Run status enumeration"""
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class Project(Base):
    """Project model - each project has its own SQLite database"""
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    db_path: Mapped[str] = mapped_column(String(512), nullable=False)
    root_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    current_phase: Mapped[Optional[PhaseType]] = mapped_column(SQLEnum(PhaseType), nullable=True)
    default_engine: Mapped[Optional[str]] = mapped_column(String(255), default="copilot_cli", nullable=True)
    spec_artifact_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    selected_arch_option_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    artifacts: Mapped[list["Artifact"]] = relationship("Artifact", back_populates="project", cascade="all, delete-orphan")
    control_state: Mapped[Optional["ControlState"]] = relationship("ControlState", back_populates="project", uselist=False, cascade="all, delete-orphan")


class Task(Base):
    """Task model - versioned objects that flow through phases"""
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)
    current_phase: Mapped[Optional[PhaseType]] = mapped_column(SQLEnum(PhaseType), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    active_version_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    engine_override: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    extra_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    change_requests: Mapped[list["ChangeRequest"]] = relationship("ChangeRequest", back_populates="task", cascade="all, delete-orphan")
    approvals: Mapped[list["Approval"]] = relationship("Approval", back_populates="task", cascade="all, delete-orphan")
    task_versions: Mapped[list["TaskVersion"]] = relationship("TaskVersion", back_populates="task", cascade="all, delete-orphan")
    runs: Mapped[list["Run"]] = relationship("Run", back_populates="task", cascade="all, delete-orphan")


class ChangeRequest(Base):
    """Change request model - versioned changes proposed for tasks"""
    __tablename__ = "change_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("tasks.id"), nullable=False)
    phase: Mapped[PhaseType] = mapped_column(SQLEnum(PhaseType), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ChangeRequestStatus] = mapped_column(SQLEnum(ChangeRequestStatus), default=ChangeRequestStatus.DRAFT)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="change_requests")
    approvals: Mapped[list["Approval"]] = relationship("Approval", back_populates="change_request", cascade="all, delete-orphan")


class Approval(Base):
    """Approval model - tracks approvals/rejections for tasks and change requests"""
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("tasks.id"), nullable=False)
    change_request_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("change_requests.id"), nullable=True)
    approver: Mapped[str] = mapped_column(String(255), nullable=False)
    approved: Mapped[bool] = mapped_column(nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="approvals")
    change_request: Mapped[Optional["ChangeRequest"]] = relationship("ChangeRequest", back_populates="approvals")


class Artifact(Base):
    """Artifact model - stores artifacts produced during development phases"""
    __tablename__ = "artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    task_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tasks.id"), nullable=True)
    run_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("runs.id"), nullable=True)
    artifact_type: Mapped[ArtifactType] = mapped_column(SQLEnum(ArtifactType), nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    storage_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)  # Actual file location
    sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # File size in bytes
    extra_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="artifacts")
    task: Mapped[Optional["Task"]] = relationship("Task")
    run: Mapped[Optional["Run"]] = relationship("Run", back_populates="artifacts")



class TaskVersion(Base):
    """TaskVersion model - versioned history of task changes"""
    __tablename__ = "task_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("tasks.id"), nullable=False)
    version_num: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gates_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    deps_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array of task IDs
    extra_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="task_versions")


class Run(Base):
    """Run model - tracks execution runs for tasks"""
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("tasks.id"), nullable=False)
    engine: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[RunStatus] = mapped_column(SQLEnum(RunStatus), default=RunStatus.RUNNING)
    log_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    gate_results: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    extra_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    start_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="runs")
    artifacts: Mapped[list["Artifact"]] = relationship("Artifact", back_populates="run", cascade="all, delete-orphan")


class ControlState(Base):
    """ControlState model - tracks execution control state per project"""
    __tablename__ = "control_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False, unique=True)
    paused: Mapped[bool] = mapped_column(default=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=300)
    current_task_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extra_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="control_state")
