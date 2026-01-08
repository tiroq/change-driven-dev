"""
Orchestration service - manages workflow through phases.
Engine-agnostic design for AI-assisted development.
"""

from typing import Protocol, Optional
from app.models import Task, PhaseType, TaskStatus


class PhaseExecutor(Protocol):
    """Protocol for phase executors - engine-agnostic interface"""
    
    def execute(self, task: Task) -> dict:
        """Execute phase logic for a task"""
        ...


class PlannerPhase:
    """Planner phase - initial task planning"""
    
    def execute(self, task: Task) -> dict:
        """Execute planner phase"""
        # Placeholder for planner logic
        return {
            "phase": PhaseType.PLANNER,
            "status": "pending",
            "output": "Planner phase placeholder"
        }


class ArchitectPhase:
    """Architect phase - architectural design and review"""
    
    def execute(self, task: Task) -> dict:
        """Execute architect phase"""
        # Placeholder for architect logic
        return {
            "phase": PhaseType.ARCHITECT,
            "status": "pending",
            "output": "Architect phase placeholder"
        }


class ReviewApprovalPhase:
    """Review/Approval phase - human or automated review"""
    
    def execute(self, task: Task) -> dict:
        """Execute review/approval phase"""
        # Placeholder for review/approval logic
        return {
            "phase": PhaseType.REVIEW_APPROVAL,
            "status": "pending",
            "output": "Review/Approval phase placeholder"
        }


class CoderPhase:
    """Coder phase - code implementation"""
    
    def execute(self, task: Task) -> dict:
        """Execute coder phase"""
        # Placeholder for coder logic
        return {
            "phase": PhaseType.CODER,
            "status": "pending",
            "output": "Coder phase placeholder"
        }


class OrchestrationEngine:
    """
    Orchestration engine - coordinates workflow through phases.
    Engine-agnostic design allows plugging different AI engines.
    """
    
    def __init__(self):
        self.phases = {
            PhaseType.PLANNER: PlannerPhase(),
            PhaseType.ARCHITECT: ArchitectPhase(),
            PhaseType.REVIEW_APPROVAL: ReviewApprovalPhase(),
            PhaseType.CODER: CoderPhase(),
        }
        
        # Define phase flow
        self.phase_flow = [
            PhaseType.PLANNER,
            PhaseType.ARCHITECT,
            PhaseType.REVIEW_APPROVAL,
            PhaseType.CODER,
        ]
    
    def get_next_phase(self, current_phase: Optional[PhaseType]) -> Optional[PhaseType]:
        """Get next phase in the workflow"""
        if current_phase is None:
            return self.phase_flow[0] if self.phase_flow else None
        
        try:
            current_index = self.phase_flow.index(current_phase)
            if current_index < len(self.phase_flow) - 1:
                return self.phase_flow[current_index + 1]
        except (ValueError, IndexError):
            pass
        
        return None
    
    def execute_phase(self, task: Task, phase: PhaseType) -> dict:
        """Execute a specific phase for a task"""
        if phase not in self.phases:
            raise ValueError(f"Unknown phase: {phase}")
        
        executor = self.phases[phase]
        return executor.execute(task)
    
    def advance_task(self, task: Task) -> dict:
        """Advance task to next phase"""
        next_phase = self.get_next_phase(task.current_phase)
        
        if next_phase is None:
            return {
                "status": "completed",
                "message": "Task has completed all phases"
            }
        
        result = self.execute_phase(task, next_phase)
        
        return {
            "status": "advanced",
            "current_phase": next_phase,
            "next_phase": self.get_next_phase(next_phase),
            "result": result
        }


# Global orchestration engine instance
orchestration_engine = OrchestrationEngine()
