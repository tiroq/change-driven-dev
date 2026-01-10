"""
Orchestration service for managing phase transitions and AI engine runs.
Coordinates planner, architect, and coder phases.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session

from ..db import dao, get_db
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
            db: Database session (project-specific)
            project_id: ID of the project
            spec_content: Project specification content
            engine_name: Optional engine override (defaults to project's default_engine)
            
        Returns:
            Dict containing run results and created artifacts
        """
        # Get project from main database (not project-specific db)
        main_db = next(get_db(1))  # Main database has ID=1
        try:
            project = dao.get_project(main_db, project_id)
        finally:
            main_db.close()
        
        # Use project's default engine if not specified
        if not engine_name:
            engine_name = project.default_engine
        
        # Create a "planning" task to track this planner execution
        planning_task = dao.create_task(
            db=db,
            project_id=project_id,
            title="Project Planning",
            description=f"Generate development plan from specification",
            current_phase=PhaseType.PLANNER,
            status=TaskStatus.IN_PROGRESS
        )
        
        # Create run record for the planning task
        run = dao.create_run(
            db=db,
            task_id=planning_task.id,
            engine=engine_name
        )
        
        # Create log path for this run
        log_path = Path(project.root_path) / "logs" / f"run_{run.id}.log"
        run_logger = RunLogger(run_id=run.id, log_path=log_path, project_id=project_id, task_id=planning_task.id)
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
            
            # Update run status and planning task status
            dao.update_run(db, run.id, status=RunStatus.SUCCESS)
            dao.update_task(db, planning_task.id, status=TaskStatus.COMPLETED)
            
            run_logger.info(f"Planner phase completed successfully. Created {len(created_tasks)} tasks")
            
            # Emit completion event
            event = Event(
                event_type=EventType.RUN_COMPLETED,
                project_id=project_id,
                data={
                    "run_id": run.id,
                    "phase": PhaseType.PLANNER.value,
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
            dao.update_run(db, run.id, status=RunStatus.FAILURE)
            dao.update_task(db, planning_task.id, status=TaskStatus.REJECTED)
            
            # Emit failure event
            event = Event(
                event_type=EventType.RUN_FAILED,
                project_id=project_id,
                data={
                    "run_id": run.id,
                    "phase": PhaseType.PLANNER.value,
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
                current_phase=PhaseType.PLANNER,
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
    
    async def run_architect_phase(
        self,
        db: Session,
        project_id: int,
        task_id: int,
        context_content: str,
        engine_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute architect phase to generate architecture options and decisions.
        
        Args:
            db: Database session
            project_id: ID of the project
            task_id: ID of the task to architect
            context_content: Architecture context/requirements
            engine_name: Optional engine override
            
        Returns:
            Dict containing run results and created artifacts
        """
        # Get project from main database
        main_db = next(get_db(1))
        try:
            project = dao.get_project(main_db, project_id)
        finally:
            main_db.close()
        
        # Get task from project-specific database
        task = dao.get_task(db, task_id)
        
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Use project's default engine if not specified
        if not engine_name:
            engine_name = project.default_engine
        
        # Create run record for this task
        run = dao.create_run(
            db=db,
            task_id=task_id,
            engine=engine_name
        )
        
        # Create log path for this run
        log_path = Path(project.root_path) / "logs" / f"run_{run.id}.log"
        run_logger = RunLogger(run_id=run.id, log_path=log_path, project_id=project_id, task_id=task_id)
        run_logger.info(f"Starting architect phase for task '{task.title}'")
        
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
                    "task": task.title,
                    "task_description": task.description
                }
            )
            
            if not session_result.success:
                raise RuntimeError(f"Failed to start engine session: {session_result.error}")
            
            run_logger.info("Engine session started, executing architect")
            
            # Read architect prompt template
            architect_prompt_path = Path(__file__).parent.parent.parent.parent / "PROMPTS" / "architect.md"
            if architect_prompt_path.exists():
                with open(architect_prompt_path, 'r') as f:
                    architect_template = f.read()
                
                # Build full prompt
                full_prompt = f"""{architect_template}

## Task
{task.title}

{task.description or ''}

## Architecture Context
{context_content}

Please analyze this and produce:
1. architecture.json with 2-3 architecture options
2. ADR (Architecture Decision Record) markdown files for key decisions

Output the architecture.json in a JSON code block."""
            else:
                full_prompt = f"""Design architecture options for this task:

Task: {task.title}
Description: {task.description or ''}

Context:
{context_content}

Provide 2-3 architecture options with trade-offs."""
            
            # Execute with engine
            result = await engine.execute(full_prompt)
            
            if not result.success:
                raise RuntimeError(f"Architect execution failed: {result.error}")
            
            run_logger.info("Architect completed, parsing results")
            
            # Parse architecture from response
            arch_data = self._parse_architecture_from_response(result.content)
            
            # Save architecture.json as artifact
            arch_artifact = self._save_architecture_artifact(
                db=db,
                project_id=project_id,
                task_id=task_id,
                run_id=run.id,
                arch_data=arch_data
            )
            
            # Extract and save ADR documents
            adr_artifacts = self._extract_and_save_adrs(
                db=db,
                project_id=project_id,
                task_id=task_id,
                run_id=run.id,
                response_content=result.content
            )
            
            # Save transcript
            transcript = await engine.get_transcript()
            transcript_artifact = self._save_transcript_artifact(
                db=db,
                project_id=project_id,
                run_id=run.id,
                transcript=transcript,
                phase="architect"
            )
            
            # Stop engine session
            await engine.stop_session()
            
            # Update task phase
            dao.update_task(db, task_id, current_phase=PhaseType.ARCHITECT)
            
            # Update run status
            dao.update_run(db, run.id, status=RunStatus.SUCCESS)
            
            run_logger.info(f"Architect phase completed successfully")
            
            # Emit completion event
            event = Event(
                event_type=EventType.RUN_COMPLETED,
                project_id=project_id,
                task_id=task_id,
                data={
                    "run_id": run.id,
                    "phase": PhaseType.ARCHITECT.value,
                    "arch_artifact_id": arch_artifact.id,
                    "adr_count": len(adr_artifacts)
                }
            )
            event_bus.publish(event)
            
            return {
                "success": True,
                "run_id": run.id,
                "arch_artifact_id": arch_artifact.id,
                "transcript_artifact_id": transcript_artifact.id,
                "adr_artifacts": [a.id for a in adr_artifacts]
            }
            
        except Exception as e:
            run_logger.error(f"Architect phase failed: {str(e)}")
            dao.update_run(db, run.id, status=RunStatus.FAILURE)
            
            # Emit failure event
            event = Event(
                event_type=EventType.RUN_FAILED,
                project_id=project_id,
                task_id=task_id,
                data={
                    "run_id": run.id,
                    "phase": PhaseType.ARCHITECT.value,
                    "error": str(e)
                }
            )
            event_bus.publish(event)
            
            return {
                "success": False,
                "run_id": run.id,
                "error": str(e)
            }
    
    def _parse_architecture_from_response(self, response_content: str) -> Dict[str, Any]:
        """
        Parse architecture.json from engine response.
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
            arch_data = json.loads(json_str)
            return arch_data
        except json.JSONDecodeError:
            # Fallback: create basic structure
            return {
                "options": [],
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "note": "Failed to parse structured architecture, manual review needed"
                },
                "raw_response": response_content
            }
    
    def _save_architecture_artifact(
        self,
        db: Session,
        project_id: int,
        task_id: int,
        run_id: int,
        arch_data: Dict[str, Any]
    ):
        """Save architecture.json as artifact"""
        # Convert to JSON string
        arch_json = json.dumps(arch_data, indent=2)
        
        # Create artifact using DAO
        artifact = dao.create_artifact(
            db=db,
            project_id=project_id,
            artifact_type=ArtifactType.ARCHITECTURE,
            name="architecture.json",
            file_path="architecture.json",
            task_id=task_id,
            run_id=run_id,
            extra_data=json.dumps({"option_count": len(arch_data.get("options", []))})
        )
        
        # Store file
        import io
        file_obj = io.BytesIO(arch_json.encode('utf-8'))
        
        artifact_storage.store_artifact(
            session=db,
            project_id=project_id,
            task_id=task_id,
            run_id=run_id,
            artifact_type="architecture",
            file_path="architecture.json",
            file_obj=file_obj
        )
        
        return artifact
    
    def _extract_and_save_adrs(
        self,
        db: Session,
        project_id: int,
        task_id: int,
        run_id: int,
        response_content: str
    ) -> List:
        """
        Extract ADR (Architecture Decision Record) documents from response.
        Looks for markdown sections or code blocks containing ADRs.
        """
        adr_artifacts = []
        
        # Look for markdown code blocks that might be ADRs
        import re
        
        # Pattern for markdown code blocks
        md_pattern = r'```markdown\n(.*?)\n```'
        matches = re.findall(md_pattern, response_content, re.DOTALL)
        
        for idx, adr_content in enumerate(matches):
            # Extract title from first line if it's a heading
            first_line = adr_content.split('\n')[0]
            if first_line.startswith('#'):
                title = first_line.lstrip('#').strip()
                filename = f"ADR_{idx+1:03d}_{title.replace(' ', '_')[:30]}.md"
            else:
                filename = f"ADR_{idx+1:03d}.md"
            
            # Create artifact
            artifact = dao.create_artifact(
                db=db,
                project_id=project_id,
                artifact_type=ArtifactType.ADR,
                name=filename,
                file_path=filename,
                task_id=task_id,
                run_id=run_id,
                extra_data=None
            )
            
            # Store file
            import io
            file_obj = io.BytesIO(adr_content.encode('utf-8'))
            
            artifact_storage.store_artifact(
                session=db,
                project_id=project_id,
                task_id=task_id,
                run_id=run_id,
                artifact_type="adr",
                file_path=filename,
                file_obj=file_obj
            )
            
            adr_artifacts.append(artifact)
        
        return adr_artifacts
    
    async def run_coder_phase(
        self,
        db: Session,
        project_id: int,
        task_id: int,
        engine_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute coder phase to implement an approved task.
        
        Workflow:
        1. Verify task is approved
        2. Build context bundle (task, architecture, files)
        3. Execute engine with coder prompt
        4. Run gates on implementation
        5. If gates pass: commit changes
        6. If gates fail: update task with error, increment attempts
        
        Args:
            db: Database session
            project_id: ID of the project
            task_id: ID of the task to implement
            engine_name: Optional engine override
            
        Returns:
            Dict containing run results and gate execution summary
        """
        from ..core.gates import GateRunner, GateSpec
        from ..core.sandbox import CommandRunner
        from ..core.config import ProjectConfig
        from ..services.git_service import GitService
        
        # Get project from main database
        main_db = next(get_db(1))
        try:
            project = dao.get_project(main_db, project_id)
        finally:
            main_db.close()
        
        # Get task from project-specific database
        task = dao.get_task(db, task_id)
        
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Verify task is approved
        if task.status != TaskStatus.APPROVED:
            raise ValueError(
                f"Task {task_id} must be APPROVED before coder execution. "
                f"Current status: {task.status.value}"
            )
        
        # Use project's default engine if not specified
        if not engine_name:
            engine_name = project.default_engine
        
        # Create run record for this task
        run = dao.create_run(
            db=db,
            task_id=task_id,
            engine=engine_name
        )
        
        # Create log path for this run
        log_path = Path(project.root_path) / "logs" / f"run_{run.id}.log"
        run_logger = RunLogger(run_id=run.id, log_path=log_path, project_id=project_id, task_id=task_id)
        run_logger.info(f"Starting coder phase for task '{task.title}'")
        
        try:
            # Increment attempts
            dao.update_task(db, task_id, attempts=task.attempts + 1)
            
            # Create engine instance
            engine = EngineFactory.create(
                engine_name,
                working_directory=project.root_path
            )
            
            # Check engine health
            if not await engine.health_check():
                raise RuntimeError(f"Engine {engine_name} is not available")
            
            # Build context bundle
            context = await self._build_coder_context(db, project_id, task_id)
            
            # Start engine session
            session_result = await engine.start_session(
                context={
                    "working_directory": project.root_path,
                    "task": task.title,
                    "task_id": task_id
                }
            )
            
            if not session_result.success:
                raise RuntimeError(f"Failed to start engine session: {session_result.error}")
            
            run_logger.info("Engine session started, executing coder")
            
            # Read coder prompt template
            coder_prompt_path = Path(__file__).parent.parent.parent.parent / "PROMPTS" / "coder.md"
            if coder_prompt_path.exists():
                with open(coder_prompt_path, 'r') as f:
                    coder_template = f.read()
                
                # Build full prompt
                full_prompt = f"""{coder_template}

## Task to Implement
ID: {task_id}
Title: {task.title}
Description: {task.description or 'No description provided'}

## Context
{context}

Please implement this task following the architecture and constraints.
Focus on minimal, correct changes that pass all gates."""
            else:
                full_prompt = f"""Implement this task:

Task ID: {task_id}
Title: {task.title}
Description: {task.description or ''}

{context}

Implement the changes needed to complete this task."""
            
            # Execute with engine
            result = await engine.execute(full_prompt)
            
            if not result.success:
                raise RuntimeError(f"Coder execution failed: {result.error}")
            
            run_logger.info("Coder completed, running gates")
            
            # Save transcript
            transcript = await engine.get_transcript()
            transcript_artifact = self._save_transcript_artifact(
                db=db,
                project_id=project_id,
                run_id=run.id,
                transcript=transcript,
                phase="coder"
            )
            
            # Stop engine session
            await engine.stop_session()
            
            # Run gates
            gate_results = await self._run_task_gates(
                db=db,
                project=project,
                task_id=task_id
            )
            
            gates_passed = gate_results.get("all_passed", False)
            
            if gates_passed:
                run_logger.info("All gates passed, committing changes")
                
                # Commit changes with git
                git_service = GitService(project.root_path)
                
                # Check if repo exists
                if await git_service.is_repo():
                    commit_sha = await git_service.create_task_commit(
                        task_id=task_id,
                        task_title=task.title,
                        phase="coder",
                        gate_results=gate_results
                    )
                    run_logger.info(f"Changes committed: {commit_sha}")
                else:
                    run_logger.warning("Project is not a git repo, skipping commit")
                    commit_sha = None
                
                # Update task status to completed
                dao.update_task(
                    db,
                    task_id,
                    status=TaskStatus.COMPLETED,
                    current_phase=PhaseType.CODER
                )
                
                # Update run status
                dao.update_run(db, run.id, status=RunStatus.SUCCESS)
                
                run_logger.info("Coder phase completed successfully")
                
                # Emit completion event
                event = Event(
                    event_type=EventType.RUN_COMPLETED,
                    project_id=project_id,
                    task_id=task_id,
                    data={
                        "run_id": run.id,
                        "phase": PhaseType.CODER.value,
                        "gates_passed": True,
                        "commit_sha": commit_sha
                    }
                )
                event_bus.publish(event)
                
                return {
                    "success": True,
                    "run_id": run.id,
                    "transcript_artifact_id": transcript_artifact.id,
                    "gates_passed": True,
                    "gate_results": gate_results,
                    "commit_sha": commit_sha,
                    "task_status": TaskStatus.COMPLETED.value
                }
            
            else:
                run_logger.error("Gates failed, task not complete")
                
                # Keep task in approved state for retry
                # Update run status to failed
                dao.update_run(
                    db,
                    run.id,
                    status=RunStatus.FAILURE
                )
                
                run_logger.info("Coder phase completed with gate failures")
                
                # Emit failure event
                event = Event(
                    event_type=EventType.RUN_FAILED,
                    project_id=project_id,
                    task_id=task_id,
                    data={
                        "run_id": run.id,
                        "phase": PhaseType.CODER.value,
                        "gates_passed": False,
                        "gate_summary": gate_results["summary"]
                    }
                )
                event_bus.publish(event)
                
                return {
                    "success": False,
                    "run_id": run.id,
                    "transcript_artifact_id": transcript_artifact.id,
                    "gates_passed": False,
                    "gate_results": gate_results,
                    "task_status": task.status.value,
                    "error": "Gates failed, see gate_results for details"
                }
            
        except Exception as e:
            run_logger.error(f"Coder phase failed: {str(e)}")
            dao.update_run(db, run.id, status=RunStatus.FAILURE)
            
            # Emit failure event
            event = Event(
                event_type=EventType.RUN_FAILED,
                project_id=project_id,
                task_id=task_id,
                data={
                    "run_id": run.id,
                    "phase": PhaseType.CODER.value,
                    "error": str(e)
                }
            )
            event_bus.publish(event)
            
            return {
                "success": False,
                "run_id": run.id,
                "error": str(e)
            }
    
    async def _build_coder_context(
        self,
        db: Session,
        project_id: int,
        task_id: int
    ) -> str:
        """
        Build context bundle for coder execution.
        
        Includes:
        - Task details and version history
        - Architecture artifacts
        - Related files/dependencies
        
        Args:
            db: Database session
            project_id: Project ID
            task_id: Task ID
            
        Returns:
            Context string for coder prompt
        """
        context_parts = []
        
        # Get task
        task = dao.get_task(db, task_id)
        
        # Get architecture artifacts for this task
        arch_artifacts = dao.list_artifacts(
            db,
            project_id=project_id,
            artifact_type=ArtifactType.ARCHITECTURE,
            task_id=task_id
        )
        
        if arch_artifacts:
            context_parts.append("## Architecture")
            context_parts.append(
                "Architecture options and decisions have been defined for this task. "
                "Follow the approved architecture approach."
            )
        
        # Get task version history
        versions = dao.list_task_versions(db, task_id)
        if len(versions) > 1:
            context_parts.append(f"\n## Task Evolution")
            context_parts.append(f"This task has {len(versions)} versions showing its refinement.")
        
        # Get gates configuration
        latest_version = dao.get_latest_task_version(db, task_id)
        if latest_version and latest_version.gates_json:
            context_parts.append("\n## Quality Gates")
            context_parts.append(
                "Your implementation must pass the configured quality gates. "
                "Focus on correctness and quality."
            )
        
        return "\n".join(context_parts) if context_parts else "No additional context available."
    
    async def _run_task_gates(
        self,
        db: Session,
        project,
        task_id: int
    ) -> Dict[str, Any]:
        """
        Run gates for a task and return results.
        
        Args:
            db: Database session
            project: Project model instance
            task_id: Task ID
            
        Returns:
            Gate execution results dict
        """
        from ..core.gates import GateRunner, GateSpec
        from ..core.sandbox import CommandRunner
        from ..core.config import ProjectConfig
        
        # Get gates from task
        latest_version = dao.get_latest_task_version(db, task_id)
        
        if not latest_version or not latest_version.gates_json:
            return {
                "all_passed": True,
                "results": [],
                "summary": {"total": 0, "passed": 0, "failed": 0}
            }
        
        try:
            gates_data = json.loads(latest_version.gates_json)
            gate_specs = [GateSpec(**g) for g in gates_data]
        except (json.JSONDecodeError, ValueError):
            return {
                "all_passed": False,
                "results": [],
                "summary": {"total": 0, "passed": 0, "failed": 0},
                "error": "Invalid gates configuration"
            }
        
        # Load project config
        try:
            config = ProjectConfig.load_from_project(Path(project.root_path))
            allowed_commands = config.get_allowed_commands()
            blocked_commands = config.get_blocked_commands()
        except Exception:
            allowed_commands = None
            blocked_commands = set()
        
        # Create command runner
        cmd_runner = CommandRunner(
            allowed_commands=allowed_commands,
            blocked_commands=blocked_commands
        )
        
        # Create gate runner
        gate_runner = GateRunner(command_runner=cmd_runner)
        
        # Execute gates
        results = await gate_runner.run_gates(
            gates=gate_specs,
            cwd=project.root_path,
            stop_on_failure=False
        )
        
        # Get summary
        summary = gate_runner.get_summary(results)
        
        return {
            "all_passed": summary["all_passed"],
            "results": [r.dict() for r in results],
            "summary": summary
        }


# Global instance
orchestration_service = OrchestrationService()
