"""
Orchestration service for managing phase transitions and AI engine runs.
Coordinates planner, architect, and coder phases.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session

from ..db import dao
from ..engines import EngineFactory, EngineResponse
from ..models.models import TaskStatus, PhaseType, ArtifactType, RunStatus
from ..core.events import event_bus, EventType, Event
from ..core.logging_config import RunLogger
from ..services.artifacts import artifact_storage


class OrchestrationService:
    """
    Service for orchestrating AI-driven development phases.
    Manages planner, architect, and coder execution.
    """
    
    def __init__(self):
        self.logger = RunLogger()
    
    async def run_planner_phase(
        self,
        db: Session,
        project_id: int,
        spec_content: str,
        engine_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute planner phase to generate task breakdown.
        
        Args:
            db: Database session
            project_id: ID of the project
            spec_content: Project specification content
            engine_name: Optional engine override (defaults to project's default_engine)
            
        Returns:
            Dict containing run results and created artifacts
        """
        # Get project
        project = dao.get_project(db, project_id)
        
        # Use project's default engine if not specified
        if not engine_name:
            engine_name = project.default_engine
        
        # Create run record
        run = dao.create_run(
            db=db,
            project_id=project_id,
            phase=PhaseType.PLAN,
            engine=engine_name,
            status=RunStatus.RUNNING
        )
        
        run_logger = RunLogger(run_id=run.id)
        run_logger.info(f"Starting planner phase for project {project.name}")
        
        try:
            # Create engine instance
            engine = EngineFactory.create(
                engine_name,
                working_directory=project.root_path
            )
            
            # Check engine health
            if not await engine.health_check():
                raise RuntimeError(f"Engine {engine_name} is not available")
            
            # Start engine session
            session_result = await engine.start_session(
                context={
                    "working_directory": project.root_path,
                    "initial_prompt": self._build_planner_prompt(spec_content)
                }
            )
            
            if not session_result.success:
                raise RuntimeError(f"Failed to start engine session: {session_result.error}")
            
            run_logger.info("Engine session started, executing planner")
            
            # Execute planner
            # Read planner prompt template
            planner_prompt_path = Path(__file__).parent.parent.parent.parent / "PROMPTS" / "planner.md"
            if planner_prompt_path.exists():
                with open(planner_prompt_path, 'r') as f:
                    planner_template = f.read()
                
                # Build full prompt
                full_prompt = f"{planner_template}\n\n## Project Specification\n\n{spec_content}\n\nPlease analyze this specification and produce a plan.json file with task breakdown."
            else:
                full_prompt = f"Create a detailed task breakdown plan for this project:\n\n{spec_content}"
            
            # Execute with engine
            result = await engine.execute(full_prompt)
            
            if not result.success:
                raise RuntimeError(f"Planner execution failed: {result.error}")
            
            run_logger.info("Planner completed, parsing results")
            
            # Parse plan from response
            plan_data = self._parse_plan_from_response(result.content)
            
            # Save plan as artifact
            plan_artifact = self._save_plan_artifact(
                db=db,
                project_id=project_id,
                run_id=run.id,
                plan_data=plan_data
            )
            
            # Create tasks from plan
            created_tasks = self._create_tasks_from_plan(
                db=db,
                project_id=project_id,
                plan_data=plan_data
            )
            
            # Save transcript
            transcript = await engine.get_transcript()
            transcript_artifact = self._save_transcript_artifact(
                db=db,
                project_id=project_id,
                run_id=run.id,
                transcript=transcript,
                phase="planner"
            )
            
            # Stop engine session
            await engine.stop_session()
            
            # Update run status
            dao.update_run(db, run.id, {"status": RunStatus.SUCCESS})
            
            run_logger.info(f"Planner phase completed successfully. Created {len(created_tasks)} tasks")
            
            # Emit completion event
            event = Event(
                event_type=EventType.RUN_COMPLETED,
                project_id=project_id,
                data={
                    "run_id": run.id,
                    "phase": PhaseType.PLAN.value,
                    "tasks_created": len(created_tasks),
                    "plan_artifact_id": plan_artifact.id
                }
            )
            event_bus.publish(event)
            
            return {
                "success": True,
                "run_id": run.id,
                "plan_artifact_id": plan_artifact.id,
                "transcript_artifact_id": transcript_artifact.id,
                "tasks_created": len(created_tasks),
                "task_ids": [t.id for t in created_tasks]
            }
            
        except Exception as e:
            run_logger.error(f"Planner phase failed: {str(e)}")
            dao.update_run(db, run.id, {"status": RunStatus.FAILED, "error": str(e)})
            
            # Emit failure event
            event = Event(
                event_type=EventType.RUN_FAILED,
                project_id=project_id,
                data={
                    "run_id": run.id,
                    "phase": PhaseType.PLAN.value,
                    "error": str(e)
                }
            )
            event_bus.publish(event)
            
            return {
                "success": False,
                "run_id": run.id,
                "error": str(e)
            }
    
    def _build_planner_prompt(self, spec_content: str) -> str:
        """Build initial planner prompt"""
        return f"I need to create a development plan for the following project specification:\n\n{spec_content}"
    
    def _parse_plan_from_response(self, response_content: str) -> Dict[str, Any]:
        """
        Parse plan.json from engine response.
        Looks for JSON code blocks or tries to parse the entire response.
        """
        # Try to find JSON code block
        if "```json" in response_content:
            start = response_content.find("```json") + 7
            end = response_content.find("```", start)
            json_str = response_content[start:end].strip()
        elif "```" in response_content:
            # Try any code block
            start = response_content.find("```") + 3
            end = response_content.find("```", start)
            json_str = response_content[start:end].strip()
        else:
            # Try the whole content
            json_str = response_content.strip()
        
        try:
            plan_data = json.loads(json_str)
            return plan_data
        except json.JSONDecodeError:
            # Fallback: create basic structure
            return {
                "tasks": [],
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "note": "Failed to parse structured plan, manual review needed"
                },
                "raw_response": response_content
            }
    
    def _save_plan_artifact(
        self,
        db: Session,
        project_id: int,
        run_id: int,
        plan_data: Dict[str, Any]
    ):
        """Save plan.json as artifact"""
        # Convert to JSON string
        plan_json = json.dumps(plan_data, indent=2)
        
        # Create artifact using DAO
        artifact = dao.create_artifact(
            db=db,
            project_id=project_id,
            artifact_type=ArtifactType.PLAN,
            name="plan.json",
            file_path="plan.json",
            run_id=run_id,
            extra_data=json.dumps({"task_count": len(plan_data.get("tasks", []))})
        )
        
        # Store file
        import io
        file_obj = io.BytesIO(plan_json.encode('utf-8'))
        
        artifact_storage.store_artifact(
            session=db,
            project_id=project_id,
            task_id=None,
            run_id=run_id,
            artifact_type="plan",
            file_path="plan.json",
            file_obj=file_obj
        )
        
        return artifact
    
    def _save_transcript_artifact(
        self,
        db: Session,
        project_id: int,
        run_id: int,
        transcript: List,
        phase: str
    ):
        """Save engine transcript as artifact"""
        # Convert transcript to JSON
        transcript_data = {
            "phase": phase,
            "timestamp": datetime.now().isoformat(),
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "metadata": msg.metadata
                }
                for msg in transcript
            ]
        }
        
        transcript_json = json.dumps(transcript_data, indent=2)
        
        # Create artifact
        artifact = dao.create_artifact(
            db=db,
            project_id=project_id,
            artifact_type=ArtifactType.TRANSCRIPT,
            name=f"{phase}_transcript.json",
            file_path=f"{phase}_transcript.json",
            run_id=run_id,
            extra_data=json.dumps({"message_count": len(transcript)})
        )
        
        # Store file
        import io
        file_obj = io.BytesIO(transcript_json.encode('utf-8'))
        
        artifact_storage.store_artifact(
            session=db,
            project_id=project_id,
            task_id=None,
            run_id=run_id,
            artifact_type="transcript",
            file_path=f"{phase}_transcript.json",
            file_obj=file_obj
        )
        
        return artifact
    
    def _create_tasks_from_plan(
        self,
        db: Session,
        project_id: int,
        plan_data: Dict[str, Any]
    ) -> List:
        """
        Create task records from plan data.
        All tasks start in DRAFT status pending approval.
        """
        created_tasks = []
        tasks_list = plan_data.get("tasks", [])
        
        for idx, task_spec in enumerate(tasks_list):
            # Extract task details
            title = task_spec.get("title", f"Task {idx + 1}")
            description = task_spec.get("description", "")
            priority = task_spec.get("priority", 5)
            dependencies = task_spec.get("dependencies", [])
            acceptance_criteria = task_spec.get("acceptance_criteria", [])
            
            # Create task in DRAFT status
            task = dao.create_task(
                db=db,
                project_id=project_id,
                title=title,
                description=description,
                priority=priority,
                current_phase=PhaseType.PLAN,
                status=TaskStatus.PENDING  # Start as PENDING, will require approval
            )
            
            # Emit task created event
            event = Event(
                event_type=EventType.TASK_CREATED,
                project_id=project_id,
                task_id=task.id,
                data={
                    "title": title,
                    "status": TaskStatus.PENDING.value,
                    "from_plan": True
                }
            )
            event_bus.publish(event)
            
            created_tasks.append(task)
        
        return created_tasks


# Global instance
orchestration_service = OrchestrationService()
