"""
Logging configuration for the change-driven-dev system.
Provides structured logging with timestamps and event types.
"""

import logging
import logging.handlers
import json
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add custom fields if present
        if hasattr(record, "project_id"):
            log_data["project_id"] = record.project_id
        if hasattr(record, "task_id"):
            log_data["task_id"] = record.task_id
        if hasattr(record, "run_id"):
            log_data["run_id"] = record.run_id
        if hasattr(record, "event_type"):
            log_data["event_type"] = record.event_type
        
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Format timestamp
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        # Build message
        message = f"{color}[{timestamp}] {record.levelname:8s}{reset} {record.name}: {record.getMessage()}"
        
        # Add exception if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"
        
        return message


def setup_logging(
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    enable_json: bool = False,
    enable_console: bool = True
) -> None:
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (None = no file logging)
        enable_json: Enable JSON formatting for file logs
        enable_console: Enable console logging
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colored output
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(ColoredFormatter())
        root_logger.addHandler(console_handler)
    
    # File handler for general logs
    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Main log file
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "app.log",
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        
        if enable_json:
            file_handler.setFormatter(JSONFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
        
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


class RunLogger:
    """Logger for individual run sessions"""
    
    def __init__(self, run_id: int, log_path: Path, project_id: Optional[int] = None, task_id: Optional[int] = None):
        self.run_id = run_id
        self.log_path = log_path
        self.project_id = project_id
        self.task_id = task_id
        
        # Create log file directory
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create file handler
        self.file_handler = logging.FileHandler(self.log_path)
        self.file_handler.setFormatter(JSONFormatter())
        
        # Create logger
        self.logger = logging.getLogger(f"run.{run_id}")
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(self.file_handler)
        self.logger.propagate = False  # Don't propagate to root logger
    
    def log(self, level: str, message: str, **kwargs) -> None:
        """
        Log a message for this run.
        
        Args:
            level: Log level (debug, info, warning, error, critical)
            message: Log message
            **kwargs: Additional context to include in log
        """
        log_func = getattr(self.logger, level.lower())
        
        # Create extra dict for custom fields
        extra = {
            "run_id": self.run_id
        }
        if self.project_id:
            extra["project_id"] = self.project_id
        if self.task_id:
            extra["task_id"] = self.task_id
        extra.update(kwargs)
        
        log_func(message, extra=extra)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message"""
        self.log("debug", message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message"""
        self.log("info", message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message"""
        self.log("warning", message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message"""
        self.log("error", message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message"""
        self.log("critical", message, **kwargs)
    
    def close(self) -> None:
        """Close the run logger"""
        self.logger.removeHandler(self.file_handler)
        self.file_handler.close()


# Initialize default logging
setup_logging(
    log_level="INFO",
    log_dir=Path("./logs"),
    enable_json=False,
    enable_console=True
)
