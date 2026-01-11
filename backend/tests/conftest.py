"""
Shared pytest configuration and fixtures for API tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from unittest.mock import Mock, patch

from app.main import app
from app.models.models import Base
from app.db.database import get_db, db_manager


# Global engine for all tests
_test_engine = None
_SessionLocal = None


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create a single test database for the entire test session"""
    global _test_engine, _SessionLocal
    _test_engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=_test_engine)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


@pytest.fixture(autouse=True)
def mock_db_manager():
    """Mock the db_manager to avoid file system operations"""
    # Create patches for both db_manager and get_db calls
    with patch('app.db.database.db_manager') as mock_manager, \
         patch('app.api.projects.get_db') as mock_get_db_in_projects:
        
        # Mock db_manager methods to return test values
        mock_manager.get_db_path.return_value = "test_project.db"
        mock_manager.init_project_db.return_value = None
        
        # Mock get_db() calls inside project creation to return test session
        def get_test_session(project_id: int = 1):
            session = _SessionLocal()
            try:
                yield session
            finally:
                session.close()
        
        mock_get_db_in_projects.return_value = get_test_session(1)
        
        yield mock_manager


@pytest.fixture
def client():
    """Create a TestClient with overridden database dependency"""
    def override_get_db(project_id: int = 1):
        """Override to use single test database for all project IDs"""
        session = _SessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    # Override the get_db dependency
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def cleanup_db():
    """Clean up database between tests to ensure isolation"""
    yield
    # Clear all tables after each test
    if _SessionLocal:
        session = _SessionLocal()
        try:
            # Delete all records from all tables
            for table in reversed(Base.metadata.sorted_tables):
                session.execute(table.delete())
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()
