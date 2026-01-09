"""
Tests for sandbox security layer.
"""
import pytest
import tempfile
import asyncio
from pathlib import Path

from app.core.sandbox import SafePathResolver, CommandRunner, SecurityError


class TestSafePathResolver:
    """Test SafePathResolver path validation."""
    
    def test_resolve_safe_path(self, tmp_path):
        """Test resolving a safe path within root."""
        resolver = SafePathResolver(str(tmp_path))
        
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        # Should resolve successfully
        resolved = resolver.resolve(str(test_file))
        assert resolved == test_file
    
    def test_reject_path_escape(self, tmp_path):
        """Test rejection of path traversal attempts."""
        resolver = SafePathResolver(str(tmp_path))
        
        # Try to escape root
        with pytest.raises(SecurityError, match="Path escape attempt"):
            resolver.resolve("../../../etc/passwd")
    
    def test_reject_absolute_path_outside_root(self, tmp_path):
        """Test rejection of absolute paths outside root."""
        resolver = SafePathResolver(str(tmp_path))
        
        with pytest.raises(SecurityError, match="outside root"):
            resolver.resolve("/etc/passwd")
    
    def test_allowlist_patterns(self, tmp_path):
        """Test path allowlist pattern matching."""
        # Only allow src/** and tests/**
        resolver = SafePathResolver(
            str(tmp_path),
            allowed_patterns=["src/**", "tests/**"]
        )
        
        # Create directories
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "docs").mkdir()
        
        # Should allow src files
        src_file = tmp_path / "src" / "main.py"
        src_file.touch()
        assert resolver.is_safe(str(src_file))
        
        # Should allow tests files
        test_file = tmp_path / "tests" / "test_main.py"
        test_file.touch()
        assert resolver.is_safe(str(test_file))
        
        # Should reject docs files
        doc_file = tmp_path / "docs" / "readme.md"
        doc_file.touch()
        assert not resolver.is_safe(str(doc_file))
    
    def test_is_safe_method(self, tmp_path):
        """Test is_safe method returns bool without exception."""
        resolver = SafePathResolver(str(tmp_path))
        
        # Safe path
        assert resolver.is_safe(str(tmp_path / "file.txt"))
        
        # Unsafe path
        assert not resolver.is_safe("../../../etc/passwd")
    
    def test_nested_paths(self, tmp_path):
        """Test resolution of nested paths."""
        resolver = SafePathResolver(
            str(tmp_path),
            allowed_patterns=["src/**"]
        )
        
        # Create nested structure
        nested = tmp_path / "src" / "components" / "ui" / "button.tsx"
        nested.parent.mkdir(parents=True)
        nested.touch()
        
        # Should resolve nested path
        resolved = resolver.resolve(str(nested))
        assert resolved == nested


class TestCommandRunner:
    """Test CommandRunner security and execution."""
    
    def test_validate_allowed_command(self):
        """Test validation of allowed commands."""
        runner = CommandRunner(allowed_commands={"python", "pytest", "git"})
        
        # Should allow listed commands
        runner.validate_command("python --version")
        runner.validate_command("pytest tests/")
        runner.validate_command("git status")
    
    def test_reject_blocked_command(self):
        """Test rejection of blocked commands."""
        runner = CommandRunner()
        
        # Should block dangerous commands
        with pytest.raises(SecurityError, match="is blocked"):
            runner.validate_command("rm -rf /")
        
        with pytest.raises(SecurityError, match="is blocked"):
            runner.validate_command("sudo apt-get install")
    
    def test_reject_command_not_in_allowlist(self):
        """Test rejection when allowlist is configured."""
        runner = CommandRunner(allowed_commands={"python", "pytest"})
        
        # Should reject command not in allowlist
        with pytest.raises(SecurityError, match="not in allowed commands"):
            runner.validate_command("git status")
    
    def test_additional_blocked_commands(self):
        """Test custom blocked commands."""
        runner = CommandRunner(blocked_commands={"custom-dangerous-cmd"})
        
        with pytest.raises(SecurityError, match="is blocked"):
            runner.validate_command("custom-dangerous-cmd --flag")
    
    def test_is_allowed_method(self):
        """Test is_allowed method returns bool without exception."""
        runner = CommandRunner(allowed_commands={"python"})
        
        # Allowed
        assert runner.is_allowed("python script.py")
        
        # Not allowed
        assert not runner.is_allowed("git status")
        assert not runner.is_allowed("rm file.txt")
    
    @pytest.mark.asyncio
    async def test_run_command_success(self):
        """Test successful command execution."""
        runner = CommandRunner(allowed_commands={"echo"})
        
        returncode, stdout, stderr = await runner.run("echo 'Hello, World!'")
        
        assert returncode == 0
        assert "Hello, World!" in stdout
        assert stderr == ""
    
    @pytest.mark.asyncio
    async def test_run_command_timeout(self):
        """Test command timeout enforcement."""
        runner = CommandRunner(allowed_commands={"sleep"})
        
        # Should timeout after 1 second
        with pytest.raises(TimeoutError, match="exceeded timeout"):
            await runner.run("sleep 10", timeout=1)
    
    @pytest.mark.asyncio
    async def test_run_command_blocked(self):
        """Test running blocked command raises error."""
        runner = CommandRunner()
        
        with pytest.raises(SecurityError, match="is blocked"):
            await runner.run("rm file.txt")
    
    @pytest.mark.asyncio
    async def test_run_command_with_cwd(self, tmp_path):
        """Test command execution with working directory."""
        runner = CommandRunner(allowed_commands={"pwd"})
        
        returncode, stdout, stderr = await runner.run("pwd", cwd=str(tmp_path))
        
        assert returncode == 0
        assert str(tmp_path) in stdout
    
    def test_empty_command(self):
        """Test validation of empty command."""
        runner = CommandRunner()
        
        with pytest.raises(SecurityError, match="Empty command"):
            runner.validate_command("")
        
        with pytest.raises(SecurityError, match="Empty command"):
            runner.validate_command("   ")


class TestSecurityIntegration:
    """Integration tests for complete security layer."""
    
    def test_combined_path_and_command_security(self, tmp_path):
        """Test using both path resolver and command runner together."""
        # Set up path resolver
        path_resolver = SafePathResolver(
            str(tmp_path),
            allowed_patterns=["src/**", "tests/**"]
        )
        
        # Set up command runner
        cmd_runner = CommandRunner(
            allowed_commands={"python", "pytest"}
        )
        
        # Create allowed path
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        test_file = src_dir / "test.py"
        test_file.write_text("print('test')")
        
        # Validate path is safe
        safe_path = path_resolver.resolve(str(test_file))
        assert safe_path.exists()
        
        # Validate command is safe
        assert cmd_runner.is_allowed(f"python {safe_path}")
        
        # Blocked path
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        doc_file = docs_dir / "readme.md"
        doc_file.touch()
        
        assert not path_resolver.is_safe(str(doc_file))
        
        # Blocked command
        assert not cmd_runner.is_allowed("rm -rf /")
