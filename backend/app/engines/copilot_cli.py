"""
GitHub Copilot CLI engine adapter.
"""
import asyncio
import json
from datetime import datetime
from typing import Optional, Dict, Any, List, AsyncIterator
from pathlib import Path

from .engine_base import (
    EngineBase,
    EngineStatus,
    EngineMessage,
    EngineResponse,
    EngineFactory
)


class CopilotCLIEngine:
    """
    Adapter for GitHub Copilot CLI.
    
    Uses the `github-copilot-cli` command-line tool for AI assistance.
    """
    
    def __init__(
        self,
        working_directory: Optional[str] = None,
        timeout: int = 300,
        **kwargs
    ):
        """
        Initialize Copilot CLI engine.
        
        Args:
            working_directory: Directory to execute commands in
            timeout: Command timeout in seconds
            **kwargs: Additional configuration options
        """
        self._engine_name = "copilot_cli"
        self._status = EngineStatus.IDLE
        self._working_directory = Path(working_directory) if working_directory else Path.cwd()
        self._timeout = timeout
        self._transcript: List[EngineMessage] = []
        self._process: Optional[asyncio.subprocess.Process] = None
        self._session_id: Optional[str] = None
        
    @property
    def engine_name(self) -> str:
        return self._engine_name
    
    @property
    def status(self) -> EngineStatus:
        return self._status
    
    async def start_session(
        self,
        context: Optional[Dict[str, Any]] = None
    ) -> EngineResponse:
        """
        Initialize a new Copilot CLI session.
        
        Args:
            context: Optional context with initial_prompt, working_directory, etc.
            
        Returns:
            EngineResponse with session initialization result
        """
        try:
            self._session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self._transcript = []
            
            # Update working directory if provided in context
            if context and "working_directory" in context:
                self._working_directory = Path(context["working_directory"])
            
            # Add initial system message
            system_msg = EngineMessage(
                role="system",
                content=f"Session started in {self._working_directory}",
                timestamp=datetime.now().isoformat(),
                metadata={"session_id": self._session_id}
            )
            self._transcript.append(system_msg)
            
            # If initial prompt provided, execute it
            if context and "initial_prompt" in context:
                initial_response = await self.execute(context["initial_prompt"])
                if not initial_response.success:
                    self._status = EngineStatus.ERROR
                    return initial_response
            
            self._status = EngineStatus.ACTIVE
            
            return EngineResponse(
                success=True,
                content="Session initialized",
                status=self._status,
                messages=self._transcript.copy(),
                metadata={"session_id": self._session_id}
            )
            
        except Exception as e:
            self._status = EngineStatus.ERROR
            return EngineResponse(
                success=False,
                content="",
                status=self._status,
                error=f"Failed to start session: {str(e)}"
            )
    
    async def execute(
        self,
        command: str,
        stream: bool = False,
        **kwargs
    ) -> EngineResponse:
        """
        Execute a command with Copilot CLI.
        
        Args:
            command: The prompt/question for Copilot
            stream: Whether to stream response (not implemented)
            **kwargs: Additional parameters
            
        Returns:
            EngineResponse with Copilot's response
        """
        if self._status not in [EngineStatus.ACTIVE, EngineStatus.IDLE]:
            return EngineResponse(
                success=False,
                content="",
                status=self._status,
                error=f"Cannot execute in status {self._status}"
            )
        
        try:
            # Add user message to transcript
            user_msg = EngineMessage(
                role="user",
                content=command,
                timestamp=datetime.now().isoformat()
            )
            self._transcript.append(user_msg)
            
            # Execute Copilot CLI command
            # Format: github-copilot-cli "question/prompt"
            result = await self._run_copilot_command(command, **kwargs)
            
            if result["success"]:
                # Add assistant response to transcript
                assistant_msg = EngineMessage(
                    role="assistant",
                    content=result["output"],
                    timestamp=datetime.now().isoformat(),
                    metadata={"exit_code": result.get("exit_code")}
                )
                self._transcript.append(assistant_msg)
                
                return EngineResponse(
                    success=True,
                    content=result["output"],
                    status=self._status,
                    messages=[user_msg, assistant_msg],
                    metadata={"exit_code": result.get("exit_code")}
                )
            else:
                return EngineResponse(
                    success=False,
                    content=result.get("output", ""),
                    status=EngineStatus.ERROR,
                    error=result.get("error"),
                    metadata={"exit_code": result.get("exit_code")}
                )
                
        except Exception as e:
            self._status = EngineStatus.ERROR
            return EngineResponse(
                success=False,
                content="",
                status=self._status,
                error=f"Execution failed: {str(e)}"
            )
    
    async def execute_stream(
        self,
        command: str,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Execute command with streaming (reads output line by line).
        
        Args:
            command: The prompt for Copilot
            **kwargs: Additional parameters
            
        Yields:
            Lines of output as they arrive
        """
        try:
            # Add user message
            user_msg = EngineMessage(
                role="user",
                content=command,
                timestamp=datetime.now().isoformat()
            )
            self._transcript.append(user_msg)
            
            # Start process
            process = await asyncio.create_subprocess_exec(
                "copilot",
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self._working_directory)
            )
            
            self._process = process
            full_output = []
            
            # Stream stdout
            if process.stdout:
                async for line in process.stdout:
                    line_text = line.decode('utf-8')
                    full_output.append(line_text)
                    yield line_text
            
            # Wait for completion
            await process.wait()
            
            # Add complete response to transcript
            assistant_msg = EngineMessage(
                role="assistant",
                content="".join(full_output),
                timestamp=datetime.now().isoformat(),
                metadata={"exit_code": process.returncode}
            )
            self._transcript.append(assistant_msg)
            
            self._process = None
            
        except Exception as e:
            self._status = EngineStatus.ERROR
            yield f"Error: {str(e)}"
    
    async def _run_copilot_command(
        self,
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run a Copilot CLI command and capture output.
        
        Args:
            prompt: The prompt for Copilot
            **kwargs: Additional parameters
            
        Returns:
            Dict with success, output, exit_code, error
        """
        try:
            # Execute command
            process = await asyncio.create_subprocess_exec(
                "copilot",
                prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self._working_directory)
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self._timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "success": False,
                    "output": "",
                    "error": f"Command timed out after {self._timeout}s"
                }
            
            output = stdout.decode('utf-8')
            error_output = stderr.decode('utf-8')
            
            if process.returncode == 0:
                return {
                    "success": True,
                    "output": output,
                    "exit_code": process.returncode
                }
            else:
                return {
                    "success": False,
                    "output": output,
                    "error": error_output or f"Command failed with exit code {process.returncode}",
                    "exit_code": process.returncode
                }
                
        except FileNotFoundError:
            return {
                "success": False,
                "output": "",
                "error": "github-copilot-cli not found. Is it installed?"
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Command execution failed: {str(e)}"
            }
    
    async def stop_session(self) -> EngineResponse:
        """
        Terminate the Copilot session.
        
        Returns:
            EngineResponse with termination result
        """
        try:
            # Kill active process if any
            if self._process and self._process.returncode is None:
                self._process.kill()
                await self._process.wait()
            
            # Add termination message
            system_msg = EngineMessage(
                role="system",
                content="Session terminated",
                timestamp=datetime.now().isoformat(),
                metadata={"session_id": self._session_id}
            )
            self._transcript.append(system_msg)
            
            self._status = EngineStatus.STOPPED
            self._process = None
            
            return EngineResponse(
                success=True,
                content="Session stopped",
                status=self._status,
                metadata={"session_id": self._session_id}
            )
            
        except Exception as e:
            return EngineResponse(
                success=False,
                content="",
                status=self._status,
                error=f"Failed to stop session: {str(e)}"
            )
    
    async def get_transcript(self) -> List[EngineMessage]:
        """
        Get the full conversation transcript.
        
        Returns:
            List of EngineMessage objects
        """
        return self._transcript.copy()
    
    async def get_status(self) -> EngineStatus:
        """
        Get current engine status.
        
        Returns:
            Current EngineStatus
        """
        return self._status
    
    async def send_feedback(
        self,
        message_id: Optional[str],
        feedback: str,
        **kwargs
    ) -> EngineResponse:
        """
        Send feedback (adds to transcript as user message).
        
        Args:
            message_id: Ignored for Copilot CLI
            feedback: Feedback content
            **kwargs: Additional parameters
            
        Returns:
            EngineResponse
        """
        # Copilot CLI doesn't have explicit feedback mechanism
        # Just treat as another user message
        return await self.execute(feedback, **kwargs)
    
    async def health_check(self) -> bool:
        """
        Check if Copilot CLI is available.
        
        Returns:
            True if CLI is available
        """
        try:
            process = await asyncio.create_subprocess_exec(
                "copilot",
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(process.wait(), timeout=5)
            return process.returncode == 0
        except (FileNotFoundError, asyncio.TimeoutError):
            return False
        except Exception:
            return False


# Register with factory
EngineFactory.register("copilot_cli", CopilotCLIEngine)
