"""
Database initialization and connection management.
Supports per-project SQLite databases and PostgreSQL with schema-based multi-tenancy.
"""

from pathlib import Path
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool
from typing import Generator, Optional
from threading import Lock

from app.models import Base
from app.core.config import DatabaseConfig


class DatabaseManager:
    """Manages database connections for projects"""
    
    def __init__(self, db_config: Optional[DatabaseConfig] = None):
        self.db_config = db_config or DatabaseConfig()
        self.engines = {}
        self.session_makers = {}
        self._lock = Lock()  # Thread synchronization for dictionary access
        
        # For SQLite, ensure base path exists
        if self.db_config.type == "sqlite":
            self.db_base_path = Path(self.db_config.path)
            self.db_base_path.mkdir(parents=True, exist_ok=True)
    
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
        if self.db_config.type == "sqlite":
            return str(self.db_base_path / f"project_{project_id}.db")
        else:
            return self._get_schema_name(project_id)
    
    def init_project_db(self, project_id: int) -> None:
        """Initialize database for a project"""
        db_url = self._build_database_url(project_id)
        engine_kwargs = self._get_engine_kwargs()
        
        engine = create_engine(db_url, echo=False, **engine_kwargs)
        
        # For PostgreSQL, create schema if it doesn't exist
        if self.db_config.type == "postgresql":
            schema_name = self._get_schema_name(project_id)
            with engine.connect() as conn:
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
                conn.commit()
            
            # Create tables in the project schema
            Base.metadata.schema = schema_name
            Base.metadata.create_all(bind=engine)
            Base.metadata.schema = None  # Reset to avoid side effects
        else:
            # SQLite: create all tables normally
            Base.metadata.create_all(bind=engine)
        
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
        if db_config.type == "sqlite":
            self.db_base_path = Path(db_config.path)
            self.db_base_path.mkdir(parents=True, exist_ok=True)


# Global database manager instance
db_manager = DatabaseManager()


def get_db(project_id: int = 1) -> Generator[Session, None, None]:
    """Dependency for getting database session"""
    return db_manager.get_session(project_id)


def get_db_for_project(project_id: int) -> Generator[Session, None, None]:
    """Get database session for a specific project ID"""
    yield from db_manager.get_session(project_id)


def configure_database(db_config: DatabaseConfig) -> None:
    """Configure database manager with custom settings"""
    db_manager.configure(db_config)
