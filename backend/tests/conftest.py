"""
Simplified pytest configuration using database test mode.

IMPORTANT: Test mode must be enabled before importing the app,
so that when db_manager is created, it's already in test mode.
"""

import os
# Enable test mode BEFORE any app imports
os.environ["TEST_MODE"] = "true"

import pytest
from fastapi.testclient import TestClient

# Now import app - db_manager will be created with test_mode=True
from app.main import app
from app.db.database import db_manager


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Ensure test mode is active and database is initialized.
    The TEST_MODE env var was set above, so db_manager is already in test mode.
    """
    # Force initialization of test database
    db_manager._init_test_database()
    yield


@pytest.fixture
def client():
    """Create TestClient for API testing"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def cleanup_database():
    """Clean database after each test for isolation"""
    yield
    db_manager.cleanup_test_database()
