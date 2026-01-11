"""
Shared pytest configuration and fixtures for API tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.models.models import Base
from app.db.database import get_db


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
def reset_db():
    """Reset database between tests to ensure isolation"""
    yield
    # Rollback any uncommitted changes
    if _SessionLocal:
        session = _SessionLocal()
        try:
            session.rollback()
        finally:
            session.close()
