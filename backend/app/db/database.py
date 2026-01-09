"""
Database initialization and connection management.
Supports per-project SQLite databases.
"""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from threading import Lock

from app.models import Base


class DatabaseManager:
    """Manages database connections for projects"""
    
    def __init__(self, db_base_path: str = "./data"):
        self.db_base_path = Path(db_base_path)
        self.db_base_path.mkdir(parents=True, exist_ok=True)
        self.engines = {}
        self.session_makers = {}
        self._lock = Lock()  # Thread synchronization for dictionary access
    
    def get_db_path(self, project_id: int) -> str:
        """Get database path for a project"""
        return str(self.db_base_path / f"project_{project_id}.db")
    
    def init_project_db(self, project_id: int) -> None:
        """Initialize database for a project"""
        db_path = self.get_db_path(project_id)
        db_url = f"sqlite:///{db_path}"
        
        engine = create_engine(db_url, echo=False, connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        
        self.engines[project_id] = engine
        self.session_makers[project_id] = sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=engine
        )
    
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


# Global database manager instance
db_manager = DatabaseManager()


def get_db(project_id: int = 1) -> Generator[Session, None, None]:
    """Dependency for getting database session"""
    return db_manager.get_session(project_id)
