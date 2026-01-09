"""
Git integration service for version control operations.
Handles repository initialization, commits, status tracking, and diffs.
"""
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class GitStatus(BaseModel):
    """Git repository status."""
    is_repo: bool
    branch: str
    has_changes: bool
    staged_files: List[str]
    unstaged_files: List[str]
    untracked_files: List[str]
    ahead: int = 0
    behind: int = 0


class GitCommitInfo(BaseModel):
    """Information about a git commit."""
    sha: str
    message: str
    author: str
    timestamp: datetime
    files_changed: int


class GitService:
    """
    Service for Git operations.
    Provides safe wrappers around git commands.
    """
    
    def __init__(self, repo_path: str):
        """
        Initialize Git service.
        
        Args:
            repo_path: Path to git repository root
        """
        self.repo_path = Path(repo_path).resolve()
    
    async def _run_git_command(
        self,
        args: List[str],
        check: bool = True
    ) -> tuple[int, str, str]:
        """
        Run a git command.
        
        Args:
            args: Git command arguments (without 'git' prefix)
            check: Whether to raise exception on non-zero exit code
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
            
        Raises:
            RuntimeError: If command fails and check=True
        """
        cmd = ["git"] + args
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(self.repo_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await proc.communicate()
        exit_code = proc.returncode if proc.returncode is not None else -1
        
        stdout_str = stdout.decode() if stdout else ""
        stderr_str = stderr.decode() if stderr else ""
        
        if check and exit_code != 0:
            raise RuntimeError(
                f"Git command failed: git {' '.join(args)}\n"
                f"Exit code: {exit_code}\n"
                f"stderr: {stderr_str}"
            )
        
        return exit_code, stdout_str, stderr_str
    
    async def is_repo(self) -> bool:
        """
        Check if directory is a git repository.
        
        Returns:
            True if directory is a git repo, False otherwise
        """
        exit_code, _, _ = await self._run_git_command(
            ["rev-parse", "--git-dir"],
            check=False
        )
        return exit_code == 0
    
    async def init(self, initial_branch: str = "main") -> None:
        """
        Initialize a new git repository.
        
        Args:
            initial_branch: Name of initial branch
            
        Raises:
            RuntimeError: If initialization fails
        """
        if await self.is_repo():
            return  # Already initialized
        
        await self._run_git_command(["init", "-b", initial_branch])
    
    async def get_status(self) -> GitStatus:
        """
        Get repository status.
        
        Returns:
            GitStatus object with current repository state
        """
        if not await self.is_repo():
            return GitStatus(
                is_repo=False,
                branch="",
                has_changes=False,
                staged_files=[],
                unstaged_files=[],
                untracked_files=[]
            )
        
        # Get current branch
        _, branch, _ = await self._run_git_command(
            ["rev-parse", "--abbrev-ref", "HEAD"]
        )
        branch = branch.strip()
        
        # Get status in porcelain format
        _, status_output, _ = await self._run_git_command(
            ["status", "--porcelain"]
        )
        
        staged_files = []
        unstaged_files = []
        untracked_files = []
        
        for line in status_output.strip().split('\n'):
            if not line:
                continue
            
            status_code = line[:2]
            filename = line[3:]
            
            # Staged changes
            if status_code[0] in ('M', 'A', 'D', 'R', 'C'):
                staged_files.append(filename)
            
            # Unstaged changes
            if status_code[1] in ('M', 'D'):
                unstaged_files.append(filename)
            
            # Untracked files
            if status_code == '??':
                untracked_files.append(filename)
        
        has_changes = bool(staged_files or unstaged_files or untracked_files)
        
        # Get ahead/behind counts (if remote exists)
        ahead = 0
        behind = 0
        exit_code, upstream_output, _ = await self._run_git_command(
            ["rev-list", "--left-right", "--count", f"{branch}...@{{u}}"],
            check=False
        )
        if exit_code == 0 and upstream_output.strip():
            parts = upstream_output.strip().split()
            if len(parts) == 2:
                ahead = int(parts[0])
                behind = int(parts[1])
        
        return GitStatus(
            is_repo=True,
            branch=branch,
            has_changes=has_changes,
            staged_files=staged_files,
            unstaged_files=unstaged_files,
            untracked_files=untracked_files,
            ahead=ahead,
            behind=behind
        )
    
    async def stage_all(self) -> None:
        """
        Stage all changes (git add -A).
        """
        await self._run_git_command(["add", "-A"])
    
    async def stage_files(self, files: List[str]) -> None:
        """
        Stage specific files.
        
        Args:
            files: List of file paths to stage
        """
        if not files:
            return
        
        await self._run_git_command(["add"] + files)
    
    async def commit(
        self,
        message: str,
        author_name: Optional[str] = None,
        author_email: Optional[str] = None
    ) -> str:
        """
        Create a commit with staged changes.
        
        Args:
            message: Commit message
            author_name: Optional author name override
            author_email: Optional author email override
            
        Returns:
            Commit SHA hash
            
        Raises:
            RuntimeError: If commit fails
        """
        args = ["commit", "-m", message]
        
        if author_name and author_email:
            args.extend(["--author", f"{author_name} <{author_email}>"])
        
        await self._run_git_command(args)
        
        # Get commit SHA
        _, sha, _ = await self._run_git_command(["rev-parse", "HEAD"])
        return sha.strip()
    
    async def commit_all(
        self,
        message: str,
        author_name: Optional[str] = None,
        author_email: Optional[str] = None
    ) -> str:
        """
        Stage all changes and commit.
        
        Args:
            message: Commit message
            author_name: Optional author name override
            author_email: Optional author email override
            
        Returns:
            Commit SHA hash
        """
        await self.stage_all()
        return await self.commit(message, author_name, author_email)
    
    async def get_diff(
        self,
        cached: bool = False,
        files: Optional[List[str]] = None
    ) -> str:
        """
        Get diff of changes.
        
        Args:
            cached: If True, get staged changes; if False, get unstaged
            files: Optional list of specific files to diff
            
        Returns:
            Diff output as string
        """
        args = ["diff"]
        
        if cached:
            args.append("--cached")
        
        if files:
            args.append("--")
            args.extend(files)
        
        _, diff_output, _ = await self._run_git_command(args)
        return diff_output
    
    async def get_last_commit(self) -> Optional[GitCommitInfo]:
        """
        Get information about the last commit.
        
        Returns:
            GitCommitInfo or None if no commits exist
        """
        exit_code, output, _ = await self._run_git_command(
            ["log", "-1", "--pretty=format:%H|%s|%an|%aI|%ct"],
            check=False
        )
        
        if exit_code != 0 or not output.strip():
            return None
        
        parts = output.strip().split('|')
        if len(parts) != 5:
            return None
        
        sha, message, author, iso_date, commit_time = parts
        
        # Get number of files changed
        _, stats, _ = await self._run_git_command(
            ["show", "--stat", "--oneline", sha],
            check=False
        )
        files_changed = len([l for l in stats.split('\n') if '|' in l])
        
        return GitCommitInfo(
            sha=sha,
            message=message,
            author=author,
            timestamp=datetime.fromisoformat(iso_date),
            files_changed=files_changed
        )
    
    async def create_task_commit(
        self,
        task_id: int,
        task_title: str,
        phase: str,
        gate_results: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a structured commit for a task.
        
        Args:
            task_id: Task ID
            task_title: Task title
            phase: Current phase (e.g., "coder")
            gate_results: Optional gate execution results
            
        Returns:
            Commit SHA hash
        """
        # Format commit message
        message = self._format_task_commit_message(
            task_id=task_id,
            task_title=task_title,
            phase=phase,
            gate_results=gate_results
        )
        
        return await self.commit_all(
            message=message,
            author_name="change-driven-dev",
            author_email="cdd@automated.local"
        )
    
    def _format_task_commit_message(
        self,
        task_id: int,
        task_title: str,
        phase: str,
        gate_results: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format a structured commit message for a task.
        
        Args:
            task_id: Task ID
            task_title: Task title
            phase: Current phase
            gate_results: Optional gate execution results
            
        Returns:
            Formatted commit message
        """
        # Main commit line
        message = f"[Task {task_id}] {task_title}\n\n"
        
        # Add phase info
        message += f"Phase: {phase}\n"
        
        # Add gate results if available
        if gate_results:
            summary = gate_results.get("summary", {})
            message += f"Gates: {summary.get('passed', 0)}/{summary.get('total', 0)} passed\n"
            
            # Add failed gates if any
            failed_gates = [
                r["gate_name"]
                for r in gate_results.get("results", [])
                if not r.get("passed", False)
            ]
            if failed_gates:
                message += f"Failed: {', '.join(failed_gates)}\n"
        
        # Add automation footer
        message += "\nAutomated commit by change-driven-dev"
        
        return message
    
    async def has_uncommitted_changes(self) -> bool:
        """
        Check if there are uncommitted changes.
        
        Returns:
            True if there are uncommitted changes, False otherwise
        """
        status = await self.get_status()
        return status.has_changes
