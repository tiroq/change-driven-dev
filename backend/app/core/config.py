"""
Project configuration management.
Loads and validates project-specific security and execution settings.
"""
import yaml
from pathlib import Path
from typing import Optional, List, Set, Dict, Any
from pydantic import BaseModel, Field


class SandboxConfig(BaseModel):
    """Sandbox security configuration."""
    allowed_paths: List[str] = Field(
        default=["**/*"],
        description="Glob patterns for allowed file paths"
    )
    allowed_commands: Optional[List[str]] = Field(
        default=None,
        description="Whitelist of allowed commands (None = use blocklist only)"
    )
    blocked_commands: List[str] = Field(
        default=[],
        description="Additional commands to block beyond defaults"
    )
    command_timeout: int = Field(
        default=300,
        description="Default timeout for command execution in seconds"
    )


class GateConfig(BaseModel):
    """Gate execution configuration."""
    enabled: bool = Field(default=True, description="Whether gates are enabled")
    timeout: int = Field(default=60, description="Timeout for gate execution in seconds")
    fail_on_error: bool = Field(
        default=True,
        description="Whether to fail task on gate errors"
    )


class ProjectConfig(BaseModel):
    """
    Project-level configuration.
    Loaded from project root config.yaml file.
    """
    project_name: str = Field(description="Project name")
    default_engine: str = Field(
        default="copilot-cli",
        description="Default AI engine to use"
    )
    sandbox: SandboxConfig = Field(
        default_factory=SandboxConfig,
        description="Sandbox security settings"
    )
    gates: GateConfig = Field(
        default_factory=GateConfig,
        description="Gate execution settings"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional project metadata"
    )
    
    @classmethod
    def load(cls, config_path: Path) -> "ProjectConfig":
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to config.yaml file
            
        Returns:
            ProjectConfig instance
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        if not data:
            raise ValueError(f"Empty or invalid configuration file: {config_path}")
        
        return cls(**data)
    
    @classmethod
    def load_from_project(cls, project_root: Path) -> "ProjectConfig":
        """
        Load configuration from project root directory.
        
        Args:
            project_root: Project root directory
            
        Returns:
            ProjectConfig instance (uses defaults if config.yaml not found)
        """
        config_path = project_root / "config.yaml"
        
        if config_path.exists():
            return cls.load(config_path)
        else:
            # Return default configuration
            return cls(
                project_name=project_root.name,
                default_engine="copilot-cli"
            )
    
    def save(self, config_path: Path) -> None:
        """
        Save configuration to YAML file.
        
        Args:
            config_path: Path to save config.yaml
        """
        with open(config_path, 'w') as f:
            yaml.dump(
                self.model_dump(exclude_none=True),
                f,
                default_flow_style=False,
                sort_keys=False
            )
    
    def get_allowed_commands(self) -> Optional[Set[str]]:
        """Get set of allowed commands for CommandRunner."""
        if self.sandbox.allowed_commands:
            return set(self.sandbox.allowed_commands)
        return None
    
    def get_blocked_commands(self) -> Set[str]:
        """Get set of blocked commands for CommandRunner."""
        return set(self.sandbox.blocked_commands)


# Example config.yaml structure:
EXAMPLE_CONFIG = """
# Change-Driven Development Project Configuration

project_name: my-project
default_engine: copilot-cli

sandbox:
  # Allowed file path patterns (glob syntax)
  allowed_paths:
    - "src/**"
    - "tests/**"
    - "docs/**"
    - "*.md"
    - "*.json"
  
  # Allowed commands (whitelist approach)
  # If null/empty, uses blocklist approach instead
  allowed_commands:
    - python
    - python3
    - node
    - npm
    - pytest
    - git
    - make
  
  # Additional blocked commands (beyond defaults)
  blocked_commands:
    - rm
    - rmdir
  
  # Command execution timeout (seconds)
  command_timeout: 300

gates:
  # Enable/disable gate execution
  enabled: true
  
  # Gate execution timeout (seconds)
  timeout: 60
  
  # Fail task if gate errors (vs. just warning)
  fail_on_error: true

# Additional project metadata
metadata:
  version: "1.0.0"
  description: "Project description"
"""
