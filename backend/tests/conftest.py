"""
Shared pytest configuration and fixtures for API tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

from app.main import app
from app.models.models import Base
from app.db.database import get_db as app_get_db, DatabaseManager
from app.core.config import DatabaseConfig


# Shared test database
_test_engine = None
_TestSessionLocal = None


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create a shared test database for all tests"""
    global _test_engine, _TestSessionLocal
    
    # Create in-memory database with thread safety disabled
    _test_engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    Base.metadata.create_all(bind=_test_engine)
    
    # Create session factory
    _TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


@pytest.fixture(autouse=True)
def mock_project_db_operations():
    """Mock db_manager and project-specific get_db calls"""
    # Create a mock db_manager with correct behavior
    mock_mgr = MagicMock(spec=DatabaseManager)
    mock_mgr.get_db_path.return_value = "data/test.db"
    mock_mgr.init_project_db.return_value = None
    mock_mgr.db_config = DatabaseConfig()  # Add config attribute
    
    # Patch db_manager and get_db in all API modules
    with patch('app.db.database.db_manager', mock_mgr), \
         patch('app.api.projects.get_db') as mock_proj_get_db, \
         patch('app.api.tasks.get_db') as mock_tasks_get_db, \
         patch('app.api.change_requests.get_db') as mock_cr_get_db, \
         patch('app.api.artifacts.get_db') as mock_art_get_db:
        
        # Configure all get_db mocks to return a session from our test database
        def get_session_gen(*args, **kwargs):
            session = _TestSessionLocal()
            try:
                yield session
            finally:
                session.close()
        
        # Apply the generator correctly - return generator, don't call it
        for mock in [mock_proj_get_db, mock_tasks_get_db, mock_cr_get_db, mock_art_get_db]:
            mock.side_effect = get_session_gen
        
        yield


@pytest.fixture
def client():
    """Create TestClient with dependency override for route-level get_db"""
    def override_get_db(project_id: int = 1):
        """Use test database for all dependency-injected sessions"""
        session = _TestSessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    # Override FastAPI dependency
    app.dependency_overrides[app_get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def cleanup_database():
    """Clean database after each test for isolation"""
    yield
    
    # Delete all data from tables
    if _TestSessionLocal:
        session = _TestSessionLocal()
        try:
            # Reverse order to handle foreign key constraints
            for table in reversed(Base.metadata.sorted_tables):
                session.execute(table.delete())
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()
