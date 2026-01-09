"""
Unit tests for DAO layer
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime

from app.models.models import (
    Base, PhaseType, TaskStatus, ChangeRequestStatus, ArtifactType, RunStatus
)
from app.db import dao


@pytest.fixture
def db_session() -> Session:
    """Create a test database session"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


class TestProjectDAO:
    """Test project DAO operations"""
    
    def test_create_project(self, db_session):
        """Test creating a project"""
        project = dao.create_project(
            db_session,
            name="Test Project",
            description="A test project",
            root_path="/tmp/test"
        )
        
        assert project.id is not None
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.root_path == "/tmp/test"
        assert project.default_engine == "copilot_cli"
    
    def test_get_project(self, db_session):
        """Test getting a project by ID"""
        project = dao.create_project(db_session, name="Test Project")
        retrieved = dao.get_project(db_session, project.id)
        
        assert retrieved is not None
        assert retrieved.id == project.id
        assert retrieved.name == "Test Project"
    
    def test_get_project_by_name(self, db_session):
        """Test getting a project by name"""
        project = dao.create_project(db_session, name="Unique Project")
        retrieved = dao.get_project_by_name(db_session, "Unique Project")
        
        assert retrieved is not None
        assert retrieved.id == project.id
    
    def test_list_projects(self, db_session):
        """Test listing projects"""
        dao.create_project(db_session, name="Project 1")
        dao.create_project(db_session, name="Project 2")
        
        projects = dao.list_projects(db_session)
        
        assert len(projects) == 2
        assert projects[0].name in ["Project 1", "Project 2"]
    
    def test_update_project(self, db_session):
        """Test updating a project"""
        project = dao.create_project(db_session, name="Original")
        updated = dao.update_project(
            db_session,
            project.id,
            name="Updated",
            description="New description"
        )
        
        assert updated is not None
        assert updated.name == "Updated"
        assert updated.description == "New description"
    
    def test_delete_project(self, db_session):
        """Test deleting a project"""
        project = dao.create_project(db_session, name="To Delete")
        result = dao.delete_project(db_session, project.id)
        
        assert result is True
        assert dao.get_project(db_session, project.id) is None


class TestTaskDAO:
    """Test task DAO operations"""
    
    def test_create_task(self, db_session):
        """Test creating a task"""
        project = dao.create_project(db_session, name="Test Project")
        task = dao.create_task(
            db_session,
            project_id=project.id,
            title="Test Task",
            description="A test task",
            priority=5
        )
        
        assert task.id is not None
        assert task.project_id == project.id
        assert task.title == "Test Task"
        assert task.status == TaskStatus.PENDING
        assert task.priority == 5
        assert task.attempts == 0
    
    def test_get_task(self, db_session):
        """Test getting a task by ID"""
        project = dao.create_project(db_session, name="Test Project")
        task = dao.create_task(db_session, project_id=project.id, title="Test Task")
        retrieved = dao.get_task(db_session, task.id)
        
        assert retrieved is not None
        assert retrieved.id == task.id
        assert retrieved.title == "Test Task"
    
    def test_list_tasks_by_project(self, db_session):
        """Test listing tasks for a project"""
        project1 = dao.create_project(db_session, name="Project 1")
        project2 = dao.create_project(db_session, name="Project 2")
        
        dao.create_task(db_session, project_id=project1.id, title="Task 1")
        dao.create_task(db_session, project_id=project1.id, title="Task 2")
        dao.create_task(db_session, project_id=project2.id, title="Task 3")
        
        tasks = dao.list_tasks(db_session, project_id=project1.id)
        
        assert len(tasks) == 2
        assert all(t.project_id == project1.id for t in tasks)
    
    def test_list_tasks_by_status(self, db_session):
        """Test listing tasks by status"""
        project = dao.create_project(db_session, name="Test Project")
        dao.create_task(db_session, project_id=project.id, title="Task 1", status=TaskStatus.PENDING)
        dao.create_task(db_session, project_id=project.id, title="Task 2", status=TaskStatus.APPROVED)
        
        approved_tasks = dao.list_tasks(db_session, status=TaskStatus.APPROVED)
        
        assert len(approved_tasks) == 1
        assert approved_tasks[0].title == "Task 2"
    
    def test_update_task(self, db_session):
        """Test updating a task"""
        project = dao.create_project(db_session, name="Test Project")
        task = dao.create_task(db_session, project_id=project.id, title="Original")
        updated = dao.update_task(
            db_session,
            task.id,
            title="Updated",
            status=TaskStatus.IN_PROGRESS
        )
        
        assert updated is not None
        assert updated.title == "Updated"
        assert updated.status == TaskStatus.IN_PROGRESS
    
    def test_get_next_approved_task(self, db_session):
        """Test getting next approved task"""
        project = dao.create_project(db_session, name="Test Project")
        dao.create_task(db_session, project_id=project.id, title="Task 1", priority=1, status=TaskStatus.PENDING)
        dao.create_task(db_session, project_id=project.id, title="Task 2", priority=10, status=TaskStatus.APPROVED)
        dao.create_task(db_session, project_id=project.id, title="Task 3", priority=5, status=TaskStatus.APPROVED)
        
        next_task = dao.get_next_approved_task(db_session, project.id)
        
        assert next_task is not None
        assert next_task.title == "Task 2"  # Highest priority


class TestChangeRequestDAO:
    """Test change request DAO operations"""
    
    def test_create_change_request(self, db_session):
        """Test creating a change request"""
        project = dao.create_project(db_session, name="Test Project")
        task = dao.create_task(db_session, project_id=project.id, title="Test Task")
        cr = dao.create_change_request(
            db_session,
            task_id=task.id,
            phase=PhaseType.PLANNER,
            content="Test change request"
        )
        
        assert cr.id is not None
        assert cr.task_id == task.id
        assert cr.phase == PhaseType.PLANNER
        assert cr.status == ChangeRequestStatus.DRAFT
    
    def test_submit_change_request(self, db_session):
        """Test submitting a change request"""
        project = dao.create_project(db_session, name="Test Project")
        task = dao.create_task(db_session, project_id=project.id, title="Test Task")
        cr = dao.create_change_request(db_session, task_id=task.id, phase=PhaseType.PLANNER, content="Test")
        
        submitted = dao.submit_change_request(db_session, cr.id)
        
        assert submitted is not None
        assert submitted.status == ChangeRequestStatus.SUBMITTED
    
    def test_approve_change_request(self, db_session):
        """Test approving a change request"""
        project = dao.create_project(db_session, name="Test Project")
        task = dao.create_task(db_session, project_id=project.id, title="Test Task")
        cr = dao.create_change_request(db_session, task_id=task.id, phase=PhaseType.PLANNER, content="Test")
        
        approved = dao.approve_change_request(db_session, cr.id)
        
        assert approved is not None
        assert approved.status == ChangeRequestStatus.APPROVED


class TestArtifactDAO:
    """Test artifact DAO operations"""
    
    def test_create_artifact(self, db_session):
        """Test creating an artifact"""
        project = dao.create_project(db_session, name="Test Project")
        artifact = dao.create_artifact(
            db_session,
            project_id=project.id,
            artifact_type=ArtifactType.PLAN,
            name="plan.json",
            file_path="/tmp/plan.json",
            sha256="abc123"
        )
        
        assert artifact.id is not None
        assert artifact.project_id == project.id
        assert artifact.artifact_type == ArtifactType.PLAN
        assert artifact.sha256 == "abc123"
    
    def test_list_artifacts_by_type(self, db_session):
        """Test listing artifacts by type"""
        project = dao.create_project(db_session, name="Test Project")
        dao.create_artifact(db_session, project_id=project.id, artifact_type=ArtifactType.PLAN, name="plan.json", file_path="/tmp/plan.json")
        dao.create_artifact(db_session, project_id=project.id, artifact_type=ArtifactType.ADR, name="adr.md", file_path="/tmp/adr.md")
        
        plan_artifacts = dao.list_artifacts(db_session, artifact_type=ArtifactType.PLAN)
        
        assert len(plan_artifacts) == 1
        assert plan_artifacts[0].artifact_type == ArtifactType.PLAN


class TestRunDAO:
    """Test run DAO operations"""
    
    def test_create_run(self, db_session):
        """Test creating a run"""
        project = dao.create_project(db_session, name="Test Project")
        task = dao.create_task(db_session, project_id=project.id, title="Test Task")
        run = dao.create_run(
            db_session,
            task_id=task.id,
            engine="copilot_cli",
            log_path="/tmp/run.log"
        )
        
        assert run.id is not None
        assert run.task_id == task.id
        assert run.engine == "copilot_cli"
        assert run.status == RunStatus.RUNNING
    
    def test_complete_run(self, db_session):
        """Test completing a run"""
        project = dao.create_project(db_session, name="Test Project")
        task = dao.create_task(db_session, project_id=project.id, title="Test Task")
        run = dao.create_run(db_session, task_id=task.id, engine="copilot_cli")
        
        completed = dao.complete_run(db_session, run.id, RunStatus.SUCCESS, gate_results='{"passed": true}')
        
        assert completed is not None
        assert completed.status == RunStatus.SUCCESS
        assert completed.end_time is not None
        assert completed.gate_results == '{"passed": true}'


class TestControlStateDAO:
    """Test control state DAO operations"""
    
    def test_create_control_state(self, db_session):
        """Test creating control state"""
        project = dao.create_project(db_session, name="Test Project")
        control = dao.create_control_state(db_session, project_id=project.id)
        
        assert control.id is not None
        assert control.project_id == project.id
        assert control.paused is False
        assert control.max_attempts == 3
    
    def test_pause_resume_execution(self, db_session):
        """Test pause and resume execution"""
        project = dao.create_project(db_session, name="Test Project")
        dao.create_control_state(db_session, project_id=project.id)
        
        paused = dao.pause_execution(db_session, project.id)
        assert paused.paused is True
        
        resumed = dao.resume_execution(db_session, project.id)
        assert resumed.paused is False
