"""
Gates system for automated task validation.
Gates are executable checks that must pass before a task can proceed.
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from pathlib import Path
import re

from .sandbox import CommandRunner, SafePathResolver, SecurityError


class GateSpec(BaseModel):
    """
    Specification for a validation gate.
    Gates are commands that must succeed for a task to proceed.
    """
    name: str = Field(description="Gate name/identifier")
    description: Optional[str] = Field(
        default=None,
        description="Human-readable description"
    )
    command: str = Field(description="Command to execute for this gate")
    pass_criteria: Literal["exit_code_0", "output_contains", "output_matches"] = Field(
        default="exit_code_0",
        description="Criteria for gate to pass"
    )
    expected_output: Optional[str] = Field(
        default=None,
        description="Expected output for output_contains or regex for output_matches"
    )
    timeout: int = Field(
        default=60,
        description="Timeout in seconds for gate execution"
    )
    fail_task_on_error: bool = Field(
        default=True,
        description="Whether to fail the task if this gate fails"
    )
    required: bool = Field(
        default=True,
        description="Whether this gate must be run"
    )


class GateResult(BaseModel):
    """Result of gate execution."""
    gate_name: str
    passed: bool
    exit_code: int
    stdout: str
    stderr: str
    error: Optional[str] = None
    execution_time: float
    executed_at: datetime = Field(default_factory=datetime.now)


class GateRunner:
    """
    Executes gates and validates results.
    Uses sandbox CommandRunner for safe execution.
    """
    
    def __init__(
        self,
        command_runner: CommandRunner,
        path_resolver: Optional[SafePathResolver] = None
    ):
        """
        Initialize gate runner.
        
        Args:
            command_runner: Sandbox command runner for safe execution
            path_resolver: Optional path resolver for file access validation
        """
        self.command_runner = command_runner
        self.path_resolver = path_resolver
    
    async def run_gate(
        self,
        gate: GateSpec,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None
    ) -> GateResult:
        """
        Execute a single gate and validate results.
        
        Args:
            gate: Gate specification to execute
            cwd: Working directory for execution
            env: Environment variables
            
        Returns:
            GateResult with execution details
        """
        start_time = datetime.now()
        
        try:
            # Run command with sandbox
            exit_code, stdout, stderr = await self.command_runner.run(
                command=gate.command,
                cwd=cwd,
                timeout=gate.timeout,
                env=env
            )
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Validate based on pass criteria
            passed = self._validate_result(
                gate=gate,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr
            )
            
            return GateResult(
                gate_name=gate.name,
                passed=passed,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                execution_time=execution_time
            )
            
        except SecurityError as e:
            # Security violation
            execution_time = (datetime.now() - start_time).total_seconds()
            return GateResult(
                gate_name=gate.name,
                passed=False,
                exit_code=-1,
                stdout="",
                stderr="",
                error=f"Security violation: {str(e)}",
                execution_time=execution_time
            )
        
        except TimeoutError as e:
            # Timeout
            execution_time = gate.timeout
            return GateResult(
                gate_name=gate.name,
                passed=False,
                exit_code=-1,
                stdout="",
                stderr="",
                error=f"Timeout: {str(e)}",
                execution_time=execution_time
            )
        
        except Exception as e:
            # Other errors
            execution_time = (datetime.now() - start_time).total_seconds()
            return GateResult(
                gate_name=gate.name,
                passed=False,
                exit_code=-1,
                stdout="",
                stderr="",
                error=f"Execution error: {str(e)}",
                execution_time=execution_time
            )
    
    def _validate_result(
        self,
        gate: GateSpec,
        exit_code: int,
        stdout: str,
        stderr: str
    ) -> bool:
        """
        Validate gate result based on pass criteria.
        
        Args:
            gate: Gate specification
            exit_code: Command exit code
            stdout: Standard output
            stderr: Standard error
            
        Returns:
            True if gate passed, False otherwise
        """
        if gate.pass_criteria == "exit_code_0":
            return exit_code == 0
        
        elif gate.pass_criteria == "output_contains":
            if not gate.expected_output:
                return exit_code == 0
            combined_output = stdout + stderr
            return gate.expected_output in combined_output
        
        elif gate.pass_criteria == "output_matches":
            if not gate.expected_output:
                return exit_code == 0
            combined_output = stdout + stderr
            try:
                pattern = re.compile(gate.expected_output)
                return bool(pattern.search(combined_output))
            except re.error:
                # Invalid regex, fall back to exit code
                return exit_code == 0
        
        else:
            # Unknown criteria, default to exit code
            return exit_code == 0
    
    async def run_gates(
        self,
        gates: List[GateSpec],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        stop_on_failure: bool = False
    ) -> List[GateResult]:
        """
        Execute multiple gates in sequence.
        
        Args:
            gates: List of gate specifications
            cwd: Working directory for execution
            env: Environment variables
            stop_on_failure: If True, stop executing gates after first failure
            
        Returns:
            List of GateResult objects
        """
        results = []
        
        for gate in gates:
            # Skip optional gates if configured
            if not gate.required:
                continue
            
            result = await self.run_gate(gate, cwd=cwd, env=env)
            results.append(result)
            
            # Stop on failure if configured
            if stop_on_failure and not result.passed:
                break
        
        return results
    
    def all_passed(self, results: List[GateResult]) -> bool:
        """
        Check if all gates passed.
        
        Args:
            results: List of gate results
            
        Returns:
            True if all gates passed, False otherwise
        """
        return all(r.passed for r in results)
    
    def get_summary(self, results: List[GateResult]) -> Dict[str, Any]:
        """
        Get summary statistics for gate results.
        
        Args:
            results: List of gate results
            
        Returns:
            Dictionary with summary statistics
        """
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed
        total_time = sum(r.execution_time for r in results)
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0,
            "total_execution_time": total_time,
            "all_passed": passed == total
        }


# Example gate configurations
EXAMPLE_GATES = [
    GateSpec(
        name="lint",
        description="Run code linter",
        command="ruff check .",
        pass_criteria="exit_code_0",
        timeout=30
    ),
    GateSpec(
        name="unit-tests",
        description="Run unit tests",
        command="pytest tests/unit -v",
        pass_criteria="exit_code_0",
        timeout=300
    ),
    GateSpec(
        name="type-check",
        description="Run type checker",
        command="mypy src/",
        pass_criteria="exit_code_0",
        timeout=60
    ),
    GateSpec(
        name="security-scan",
        description="Run security scanner",
        command="bandit -r src/",
        pass_criteria="exit_code_0",
        timeout=60,
        required=False  # Optional gate
    ),
    GateSpec(
        name="coverage-check",
        description="Check test coverage",
        command="pytest --cov=src --cov-report=term-missing tests/",
        pass_criteria="output_contains",
        expected_output="TOTAL",
        timeout=300
    )
]
