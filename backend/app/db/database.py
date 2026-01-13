"""
Database initialization and connection management.
Supports per-project SQLite databases and PostgreSQL with schema-based multi-tenancy.
Also supports a unified test mode for easier testing.
"""

from pathlib import Path
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool, StaticPool
from typing import Generator, Optional
from threading import Lock
import os
import subprocess
import sys

from app.models import Base
from app.core.config import DatabaseConfig


def run_migrations(db_url: str, project_id: int) -> None:
    """
    Run alembic migrations for a database.
    For PostgreSQL, temporarily sets the schema before running migrations.
    """
    alembic_dir = Path(__file__).parent.parent.parent / "alembic"
    alembic_ini = Path(__file__).parent.parent.parent / "alembic.ini"
    
    if not alembic_ini.exists():
        raise FileNotFoundError(f"Alembic config not found: {alembic_ini}")
    
    # Use subprocess to run alembic upgrade head
    env = os.environ.copy()
    env["ALEMBIC_DB_URL"] = db_url
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "-c", str(alembic_ini), "upgrade", "head"],
            cwd=alembic_dir.parent,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Migration failed: {e.stderr}") from e


class DatabaseManager:
    """Manages database connections for projects"""
    
    def __init__(self, db_config: Optional[DatabaseConfig] = None, test_mode: bool = False):
        self.db_config = db_config or DatabaseConfig()
        self.test_mode = test_mode or os.getenv("TEST_MODE", "").lower() == "true"
        self.engines = {}
        self.session_makers = {}
        self._lock = Lock()  # Thread synchronization for dictionary access
        
        # In test mode, use a single shared engine
        if self.test_mode:
            self._test_engine = None
            self._test_session_maker = None
        else:
            # For SQLite, ensure base path exists
            if self.db_config.type == "sqlite":
                self.db_base_path = Path(self.db_config.path)
                self.db_base_path.mkdir(parents=True, exist_ok=True)
    
    def _init_test_database(self):
        """Initialize a single shared database for all projects in test mode"""
        if self._test_engine is None:
            # Use in-memory SQLite for tests with StaticPool
            # StaticPool maintains a single connection, which is required for
            # in-memory SQLite (otherwise the database is lost when connection closes)
            self._test_engine = create_engine(
                "sqlite:///:memory:",
                echo=False,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool
            )
            # In test mode, use create_all for speed (migrations not needed for tests)
            Base.metadata.create_all(bind=self._test_engine)
            self._test_session_maker = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self._test_engine
            )
    
    def _build_database_url(self, project_id: int) -> str:
        """Build database URL based on configuration type"""
        if self.db_config.type == "sqlite":
            db_path = self.db_base_path / f"project_{project_id}.db"
            return f"sqlite:///{db_path}"
        elif self.db_config.type == "postgresql":
            # PostgreSQL uses schemas for project isolation
            return (
                f"postgresql://{self.db_config.username}:{self.db_config.password}"
                f"@{self.db_config.host}:{self.db_config.port}/{self.db_config.database}"
            )
        else:
            raise ValueError(f"Unsupported database type: {self.db_config.type}")
    
    def _get_engine_kwargs(self) -> dict:
        """Get engine-specific connection arguments"""
        if self.db_config.type == "sqlite":
            return {
                "connect_args": {"check_same_thread": False},
                "poolclass": NullPool,  # SQLite doesn't need connection pooling
            }
        elif self.db_config.type == "postgresql":
            return {
                "poolclass": QueuePool,
                "pool_size": self.db_config.pool_size,
                "max_overflow": self.db_config.max_overflow,
                "pool_timeout": self.db_config.pool_timeout,
                "pool_pre_ping": True,  # Verify connections before use
            }
        else:
            return {}
    
    def _get_schema_name(self, project_id: int) -> str:
        """Get PostgreSQL schema name for a project"""
        return f"project_{project_id}"
    
    def get_db_path(self, project_id: int) -> str:
        """Get database path/identifier for a project"""
        if self.test_mode:
            return ":memory:"
        
        if self.db_config.type == "sqlite":
            return str(self.db_base_path / f"project_{project_id}.db")
        else:
            return self._get_schema_name(project_id)
    
    def init_project_db(self, project_id: int) -> None:
        """Initialize database for a project"""
        # In test mode, skip per-project initialization
        if self.test_mode:
            self._init_test_database()
            return
        
        db_url = self._build_database_url(project_id)
        engine_kwargs = self._get_engine_kwargs()
        
        engine = create_engine(db_url, echo=False, **engine_kwargs)
        
        # For PostgreSQL, create schema if it doesn't exist
        if self.db_config.type == "postgresql":
            schema_name = self._get_schema_name(project_id)
            with engine.connect() as conn:
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
                conn.commit()
            
            # Run migrations in the project schema
            # Note: Alembic will handle setting the schema via search_path
            run_migrations(db_url, project_id)
        else:
            # SQLite: run migrations to create/update schema
            run_migrations(db_url, project_id)
        
        self.engines[project_id] = engine
        self.session_makers[project_id] = sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=engine
        )
        
        # For PostgreSQL, set search_path for sessions
        if self.db_config.type == "postgresql":
            schema_name = self._get_schema_name(project_id)
            session_maker = self.session_makers[project_id]
            
            @event.listens_for(session_maker, "before_cursor_execute", retval=True)
            def set_search_path(conn, cursor, statement, parameters, context, executemany):
                if not hasattr(conn, "_search_path_set"):
                    cursor.execute(f"SET search_path TO {schema_name}")
                    conn._search_path_set = True
                return statement, parameters
    
    def get_session(self, project_id: int) -> Generator[Session, None, None]:
        """Get database session for a project"""
        # In test mode, use shared test database
        if self.test_mode:
            if self._test_session_maker is None:
                self._init_test_database()
            db = self._test_session_maker()
            try:
                yield db
            finally:
                db.close()
            return
        
        # Normal mode: per-project databases
        if project_id not in self.session_makers:
            with self._lock:
                # Double-check after acquiring lock to prevent race conditions
                if project_id not in self.session_makers:
                    self.init_project_db(project_id)
        
        SessionLocal = self.session_makers[project_id]
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def configure(self, db_config: DatabaseConfig) -> None:
        """Update database configuration (for runtime reconfiguration)"""
        self.db_config = db_config
        if db_config.type == "sqlite" and not self.test_mode:
            self.db_base_path = Path(db_config.path)
            self.db_base_path.mkdir(parents=True, exist_ok=True)
    
    def enable_test_mode(self):
        """Enable test mode (uses single shared in-memory database)"""
        self.test_mode = True
        self._test_engine = None
        self._test_session_maker = None
    
    def disable_test_mode(self):
        """Disable test mode (back to per-project databases)"""
        self.test_mode = False
        if hasattr(self, '_test_engine') and self._test_engine:
            self._test_engine.dispose()
        self._test_engine = None
        self._test_session_maker = None
    
    def cleanup_test_database(self):
        """Clear all data from test database (for test isolation between tests)"""
        if self.test_mode and self._test_session_maker:
            session = self._test_session_maker()
            try:
                # Delete in reverse order to handle foreign key constraints
                for table in reversed(Base.metadata.sorted_tables):
                    session.execute(table.delete())
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
    
    def reset_test_database(self):
        """Drop and recreate all tables in test database (full reset)"""
        if self.test_mode and self._test_engine:
            Base.metadata.drop_all(bind=self._test_engine)
            # In test mode, use create_all for speed
            Base.metadata.create_all(bind=self._test_engine)
    
    def close_project_db(self, project_id: int) -> None:
        """Close and dispose of a project's database connection"""
        with self._lock:
            if project_id in self.engines:
                try:
                    self.engines[project_id].dispose()
                except Exception:
                    pass  # Ignore errors during disposal
                del self.engines[project_id]
                del self.session_makers[project_id]


# Global database manager instance
db_manager = DatabaseManager()


def get_db(project_id: int = 1) -> Generator[Session, None, None]:
    """Dependency for getting database session"""
    return db_manager.get_session(project_id)


def get_db_for_project(project_id: int) -> Generator[Session, None, None]:
    """Get database session for a specific project ID"""
    yield from db_manager.get_session(project_id)


def get_db_session() -> Generator[Session, None, None]:
    """FastAPI dependency for database session (default project 1).
    
    This is designed to be easily overridden in tests using
    app.dependency_overrides[get_db_session] = override_function
    """
    yield from db_manager.get_session(1)


def configure_database(db_config: DatabaseConfig) -> None:
    """Configure database manager with custom settings"""
    db_manager.configure(db_config)


def enable_test_mode():
    """Enable test mode globally"""
    db_manager.enable_test_mode()


def disable_test_mode():
    """Disable test mode globally"""
    db_manager.disable_test_mode()
