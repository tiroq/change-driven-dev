"""
Base interface for AI engine adapters.
"""
from typing import Protocol, Optional, Dict, Any, List, AsyncIterator
from dataclasses import dataclass
from enum import Enum


class EngineStatus(str, Enum):
    """Status of an engine session"""
    IDLE = "idle"
    ACTIVE = "active"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class EngineMessage:
    """
    Represents a message in the engine conversation.
    """
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class EngineResponse:
    """
    Response from an engine execution.
    """
    success: bool
    content: str
    status: EngineStatus
    messages: Optional[List[EngineMessage]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EngineBase(Protocol):
    """
    Protocol defining the interface for AI engine adapters.
    
    Engine adapters provide a unified interface for interacting with
    different AI assistants (GitHub Copilot CLI, Claude, GPT, etc.).
    
    Each engine must implement:
    - Session management (start/stop)
    - Command execution with streaming support
    - Transcript capture and retrieval
    """
    
    @property
    def engine_name(self) -> str:
        """
        Name/identifier of the engine.
        
        Returns:
            String identifier (e.g., 'copilot_cli', 'claude_api')
        """
        ...
    
    @property
    def status(self) -> EngineStatus:
        """
        Current status of the engine session.
        
        Returns:
            Current EngineStatus
        """
        ...
    
    async def start_session(
        self,
        context: Optional[Dict[str, Any]] = None
    ) -> EngineResponse:
        """
        Initialize a new engine session.
        
        Args:
            context: Optional context data (working directory, initial prompt, etc.)
            
        Returns:
            EngineResponse with session initialization result
            
        Raises:
            RuntimeError: If session fails to start
        """
        ...
    
    async def execute(
        self,
        command: str,
        stream: bool = False,
        **kwargs
    ) -> EngineResponse:
        """
        Execute a command/prompt with the engine.
        
        Args:
            command: The command or prompt to execute
            stream: Whether to stream the response
            **kwargs: Additional engine-specific parameters
            
        Returns:
            EngineResponse with execution result
            
        Raises:
            RuntimeError: If execution fails
        """
        ...
    
    async def execute_stream(
        self,
        command: str,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Execute a command with streaming response.
        
        Args:
            command: The command or prompt to execute
            **kwargs: Additional engine-specific parameters
            
        Yields:
            Chunks of the response as they arrive
            
        Raises:
            RuntimeError: If execution fails
        """
        ...
    
    async def stop_session(self) -> EngineResponse:
        """
        Terminate the current engine session.
        
        Returns:
            EngineResponse with session termination result
        """
        ...
    
    async def get_transcript(self) -> List[EngineMessage]:
        """
        Retrieve the full conversation transcript.
        
        Returns:
            List of EngineMessage objects representing the conversation
        """
        ...
    
    async def get_status(self) -> EngineStatus:
        """
        Get current engine status.
        
        Returns:
            Current EngineStatus
        """
        ...
    
    async def send_feedback(
        self,
        message_id: Optional[str],
        feedback: str,
        **kwargs
    ) -> EngineResponse:
        """
        Send feedback or correction to the engine.
        
        Args:
            message_id: Optional ID of message to provide feedback on
            feedback: Feedback content
            **kwargs: Additional engine-specific parameters
            
        Returns:
            EngineResponse with feedback acknowledgment
        """
        ...
    
    async def health_check(self) -> bool:
        """
        Check if engine is available and healthy.
        
        Returns:
            True if engine is available, False otherwise
        """
        ...


class EngineFactory:
    """
    Factory for creating engine instances.
    """
    
    _engines: Dict[str, type] = {}
    
    @classmethod
    def register(cls, engine_name: str, engine_class: type) -> None:
        """
        Register an engine implementation.
        
        Args:
            engine_name: Name identifier for the engine
            engine_class: Class implementing EngineBase protocol
        """
        cls._engines[engine_name] = engine_class
    
    @classmethod
    def create(cls, engine_name: str, **kwargs) -> EngineBase:
        """
        Create an engine instance.
        
        Args:
            engine_name: Name of the engine to create
            **kwargs: Configuration parameters for the engine
            
        Returns:
            Instance of the requested engine
            
        Raises:
            ValueError: If engine is not registered
        """
        if engine_name not in cls._engines:
            raise ValueError(
                f"Engine '{engine_name}' not registered. "
                f"Available engines: {list(cls._engines.keys())}"
            )
        
        return cls._engines[engine_name](**kwargs)
    
    @classmethod
    def list_engines(cls) -> List[str]:
        """
        List all registered engine names.
        
        Returns:
            List of registered engine names
        """
        return list(cls._engines.keys())
