"""Test database migrations"""
import pytest
import os
from pathlib import Path
import sqlite3


# These tests need to run with TEST_MODE disabled to test actual migrations
@pytest.fixture(scope="module", autouse=True)
def disable_test_mode():
    """Temporarily disable test mode for migration tests"""
    old_test_mode = os.environ.get("TEST_MODE")
    os.environ.pop("TEST_MODE", None)
    
    # Import fresh db_manager without test mode
    from importlib import reload
    from app.db import database
    reload(database)
    
    yield
    
    # Restore test mode
    if old_test_mode:
        os.environ["TEST_MODE"] = old_test_mode


def test_new_project_uses_migrations(tmp_path):
    """Test that new projects are created with migrations, not create_all"""
    # Import here to get fresh instance without test mode
    from app.db.database import DatabaseManager
    from app.core.config import DatabaseConfig
    
    db_manager = DatabaseManager(db_config=DatabaseConfig(type="sqlite", path=str(tmp_path)))
    
    # Create a new project database
    project_id = 999
    db_manager.init_project_db(project_id)
    
    # Verify database file exists
    db_path = tmp_path / f"project_{project_id}.db"
    assert db_path.exists(), "Database file should be created"
    
    # Check that alembic_version table exists
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'"
    )
    result = cursor.fetchone()
    assert result is not None, "alembic_version table should exist"
    
    # Check that migration version is set
    cursor.execute("SELECT version_num FROM alembic_version")
    version = cursor.fetchone()
    assert version is not None, "Migration version should be set"
    assert version[0] == "e6e5369fb4d1", "Should be at head revision"
    
    # Verify all expected tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = [
        'alembic_version',
        'approvals',
        'artifacts',
        'change_requests',
        'control_state',
        'projects',
        'runs',
        'task_versions',
        'tasks'
    ]
    
    assert set(expected_tables).issubset(set(tables)), \
        f"Missing tables. Expected: {expected_tables}, Got: {tables}"
    
    conn.close()
    
    # Clean up
    db_manager.engines.pop(project_id, None)
    db_manager.session_makers.pop(project_id, None)


def test_migration_creates_foreign_keys(tmp_path):
    """Test that migrations create proper foreign key constraints"""
    from app.db.database import DatabaseManager
    from app.core.config import DatabaseConfig
    
    db_manager = DatabaseManager(db_config=DatabaseConfig(type="sqlite", path=str(tmp_path)))
    
    project_id = 998
    db_manager.init_project_db(project_id)
    
    db_path = tmp_path / f"project_{project_id}.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check foreign keys on tasks table
    cursor.execute("PRAGMA foreign_key_list(tasks)")
    fks = cursor.fetchall()
    
    # Should have FK to projects
    project_fk = [fk for fk in fks if fk[2] == 'projects']
    assert len(project_fk) > 0, "tasks should have FK to projects"
    
    # Check foreign keys on control_state table
    cursor.execute("PRAGMA foreign_key_list(control_state)")
    fks = cursor.fetchall()
    
    # Should have FK to projects
    project_fk = [fk for fk in fks if fk[2] == 'projects']
    assert len(project_fk) > 0, "control_state should have FK to projects"
    
    conn.close()
    
    # Clean up
    db_manager.engines.pop(project_id, None)
    db_manager.session_makers.pop(project_id, None)


def test_migration_creates_unique_constraint(tmp_path):
    """Test that control_state.project_id has unique constraint"""
    from app.db.database import DatabaseManager
    from app.core.config import DatabaseConfig
    
    db_manager = DatabaseManager(db_config=DatabaseConfig(type="sqlite", path=str(tmp_path)))
    
    project_id = 997
    db_manager.init_project_db(project_id)
    
    db_path = tmp_path / f"project_{project_id}.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check indexes on control_state (SQLite stores UNIQUE as index)
    cursor.execute("PRAGMA index_list(control_state)")
    indexes = cursor.fetchall()
    
    # Should have unique index on project_id
    unique_indexes = [idx for idx in indexes if idx[2] == 1]  # unique flag
    assert len(unique_indexes) > 0, "control_state should have unique constraint"
    
    conn.close()
    
    # Clean up
    db_manager.engines.pop(project_id, None)
    db_manager.session_makers.pop(project_id, None)
