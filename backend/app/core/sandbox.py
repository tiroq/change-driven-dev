"""
Sandbox security layer for safe file and command execution.
Prevents directory traversal, enforces allowlists, and provides timeout controls.
"""
import os
import re
from pathlib import Path
from typing import List, Optional, Set
import fnmatch


class SafePathResolver:
    """
    Validates file paths against allowlist patterns and prevents directory traversal.
    Ensures all file operations stay within allowed boundaries.
    """
    
    def __init__(self, root_path: str, allowed_patterns: Optional[List[str]] = None):
        """
        Initialize path resolver.
        
        Args:
            root_path: Root directory for all operations (project root)
            allowed_patterns: List of glob patterns for allowed paths (e.g., ["src/**", "tests/**"])
        """
        self.root_path = Path(root_path).resolve()
        self.allowed_patterns = allowed_patterns or ["**/*"]  # Default: allow all within root
        
    def resolve(self, path: str) -> Path:
        """
        Resolve and validate a path.
        
        Args:
            path: Path to resolve (can be relative or absolute)
            
        Returns:
            Resolved absolute Path object
            
        Raises:
            SecurityError: If path escapes root or doesn't match allowlist
        """
        # Convert to Path and resolve
        try:
            resolved = Path(path).resolve()
        except Exception as e:
            raise SecurityError(f"Invalid path: {path}") from e
        
        # Check if path is within root
        try:
            resolved.relative_to(self.root_path)
        except ValueError:
            raise SecurityError(
                f"Path escape attempt: {path} is outside root {self.root_path}"
            )
        
        # Check against allowlist patterns
        if not self._matches_allowlist(resolved):
            raise SecurityError(
                f"Path {path} does not match allowed patterns: {self.allowed_patterns}"
            )
        
        return resolved
    
    def _matches_allowlist(self, path: Path) -> bool:
        """
        Check if path matches any allowed pattern.
        
        Args:
            path: Resolved path to check
            
        Returns:
            True if path matches at least one allowed pattern
        """
        # Get path relative to root
        try:
            rel_path = path.relative_to(self.root_path)
        except ValueError:
            return False
        
        # Convert to string with forward slashes for pattern matching
        path_str = str(rel_path).replace(os.sep, '/')
        
        # Check each pattern
        for pattern in self.allowed_patterns:
            if fnmatch.fnmatch(path_str, pattern):
                return True
            # Also check directory matches for patterns like "src/**"
            if pattern.endswith('/**'):
                dir_pattern = pattern[:-3]
                if path_str.startswith(dir_pattern + '/') or path_str == dir_pattern:
                    return True
        
        return False
    
    def is_safe(self, path: str) -> bool:
        """
        Check if a path is safe without raising an exception.
        
        Args:
            path: Path to check
            
        Returns:
            True if path is safe, False otherwise
        """
        try:
            self.resolve(path)
            return True
        except SecurityError:
            return False
    
    def list_allowed_files(self, pattern: str = "*") -> List[Path]:
        """
        List all files matching pattern within allowed paths.
        
        Args:
            pattern: Glob pattern for files to list
            
        Returns:
            List of resolved Path objects
        """
        matching_files = []
        
        for allowed_pattern in self.allowed_patterns:
            # Convert pattern to directory
            if allowed_pattern.endswith('/**'):
                search_dir = self.root_path / allowed_pattern[:-3]
            else:
                search_dir = self.root_path / allowed_pattern.split('/')[0]
            
            if search_dir.exists() and search_dir.is_dir():
                for file_path in search_dir.rglob(pattern):
                    if file_path.is_file() and self.is_safe(str(file_path)):
                        matching_files.append(file_path)
        
        return matching_files


class CommandRunner:
    """
    Executes commands with timeout and allowlist enforcement.
    Prevents execution of dangerous commands and enforces resource limits.
    """
    
    # Default dangerous commands to block
    DANGEROUS_COMMANDS = {
        'rm', 'rmdir', 'del', 'format', 'mkfs',
        'dd', 'fdisk', 'parted',
        'chmod', 'chown', 'chgrp',
        'sudo', 'su',
        'wget', 'curl',  # Can be dangerous without URL validation
        'nc', 'netcat',
        'ssh', 'scp', 'sftp',
        'systemctl', 'service',
        'reboot', 'shutdown', 'poweroff', 'halt'
    }
    
    def __init__(
        self,
        allowed_commands: Optional[Set[str]] = None,
        blocked_commands: Optional[Set[str]] = None,
        default_timeout: int = 300  # 5 minutes
    ):
        """
        Initialize command runner.
        
        Args:
            allowed_commands: Set of allowed command names (whitelist approach)
            blocked_commands: Additional commands to block beyond defaults
            default_timeout: Default timeout in seconds for command execution
        """
        self.allowed_commands = allowed_commands
        self.blocked_commands = (blocked_commands or set()) | self.DANGEROUS_COMMANDS
        self.default_timeout = default_timeout
    
    def validate_command(self, command: str) -> None:
        """
        Validate a command against allowlist/blocklist.
        
        Args:
            command: Command string to validate
            
        Raises:
            SecurityError: If command is not allowed
        """
        # Extract command name (first word)
        cmd_parts = command.strip().split()
        if not cmd_parts:
            raise SecurityError("Empty command")
        
        cmd_name = cmd_parts[0]
        
        # Remove path if present (e.g., /usr/bin/python -> python)
        if '/' in cmd_name:
            cmd_name = cmd_name.split('/')[-1]
        
        # Check blocklist first
        if cmd_name in self.blocked_commands:
            raise SecurityError(f"Command '{cmd_name}' is blocked for security reasons")
        
        # Check allowlist if configured
        if self.allowed_commands is not None:
            if cmd_name not in self.allowed_commands:
                raise SecurityError(
                    f"Command '{cmd_name}' is not in allowed commands: {self.allowed_commands}"
                )
    
    async def run(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
        env: Optional[dict] = None
    ) -> tuple[int, str, str]:
        """
        Run a command with security checks and timeout.
        
        Args:
            command: Command to execute
            cwd: Working directory for execution
            timeout: Timeout in seconds (uses default if not specified)
            env: Environment variables
            
        Returns:
            Tuple of (return_code, stdout, stderr)
            
        Raises:
            SecurityError: If command validation fails
            TimeoutError: If command exceeds timeout
        """
        import asyncio
        
        # Validate command
        self.validate_command(command)
        
        # Use default timeout if not specified
        exec_timeout = timeout if timeout is not None else self.default_timeout
        
        # Create subprocess
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env
        )
        
        try:
            # Wait with timeout
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=exec_timeout
            )
            
            returncode = proc.returncode if proc.returncode is not None else -1
            return returncode, stdout.decode(), stderr.decode()
            
        except asyncio.TimeoutError:
            # Kill process on timeout
            proc.kill()
            await proc.wait()
            raise TimeoutError(
                f"Command exceeded timeout of {exec_timeout} seconds: {command}"
            )
    
    def is_allowed(self, command: str) -> bool:
        """
        Check if a command is allowed without raising an exception.
        
        Args:
            command: Command to check
            
        Returns:
            True if command is allowed, False otherwise
        """
        try:
            self.validate_command(command)
            return True
        except SecurityError:
            return False


class SecurityError(Exception):
    """Raised when a security violation is detected."""
    pass
