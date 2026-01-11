# Change-Driven Development - AI Agent Guide

## Architecture Overview

**Multi-Database Design**: Each project gets its own SQLite database (`data/project_{id}.db`). Main database (project_1.db) stores project metadata. Use `get_db_for_project(project_id)` from [backend/app/db/database.py](backend/app/db/database.py).

**Event-Driven Updates**: Global `event_bus` singleton ([backend/app/core/events.py](backend/app/core/events.py)) enables pub/sub across components. WebSocket endpoint subscribes to all events and broadcasts to connected clients. Always publish events after state changes (see [backend/app/api/change_requests.py](backend/app/api/change_requests.py) for examples).

**AI Engine Plugins**: Engines implement `EngineBase` protocol from [backend/app/engines/engine_base.py](backend/app/engines/engine_base.py). Factory pattern in `EngineFactory.create()` instantiates by name. Add new engines by implementing the protocol.

**Security Sandbox**: [backend/app/core/sandbox.py](backend/app/core/sandbox.py) provides `SafePathResolver` (path allowlists) and `CommandRunner` (command filtering, timeouts). All file/command operations must use these wrappers.

## Task Workflow

Tasks are **immutable** once approved. Changes require creating a `ChangeRequest` (DRAFT → SUBMITTED → APPROVED → IMPLEMENTED). New task versions created via `dao.create_task_version()`. Active version tracked in `Task.active_version_id`.

**Phase Flow**: PLANNER → ARCHITECT → REVIEW_APPROVAL → CODER  
- PLANNER: Creates tasks from spec, outputs plan.json artifact
- ARCHITECT: Generates architecture options per task, outputs ADR documents  
- REVIEW_APPROVAL: Task versioning, split/merge, approvals
- CODER: Implementation with quality gates and git commits

## Development Commands

```bash
task setup              # First-time setup (backend + frontend)
task start-bg           # Run both services in background
task stop-bg            # Stop background services
task backend            # Dev server (separate terminal)
task frontend           # Dev server (separate terminal)
task test-backend       # pytest backend/tests/
task test-e2e           # Playwright E2E tests (services must be running)
```

## Critical Patterns

**Quality Gates**: Defined in [backend/app/core/gates.py](backend/app/core/gates.py). Gates validate tasks via shell commands. Pass criteria: `exit_code_0`, `output_contains`, `output_matches`. Configure per-task via `/api/gates/task/{id}`.

**Artifact Storage**: Files stored in `backend/artifacts/{project_id}/{artifact_type}/`. Use [backend/app/services/artifacts.py](backend/app/services/artifacts.py) `artifact_storage` singleton, never direct filesystem access.

**WebSocket in Frontend**: Pages maintain WebSocket connections via `useRef`. Pattern in [frontend/src/pages/TasksPage.jsx](frontend/src/pages/TasksPage.jsx): connect on mount, handle events, auto-reconnect on close. Use `api.connectWebSocket(projectId)` from [frontend/src/services/api.js](frontend/src/services/api.js).

**DAO Layer**: All database operations through [backend/app/db/dao.py](backend/app/db/dao.py). Never use raw SQLAlchemy queries in routes/services. DAO functions handle session commits.

## Common Gotchas

- Frontend routing uses `?project_id=X` query params, not path segments
- Database sessions are project-specific; use correct `project_id` when calling DAO
- Event bus is synchronous by default; use `subscribe_async()` for async handlers
- Sandbox command timeouts default to 300s; configure in `config.yaml` or per-gate
- Task status transitions are enforced; check `TaskStatus` enum before updates

## Configuration

Project-level config in workspace root `config.yaml` (see `config.yaml.example`). Schema in [backend/app/core/config.py](backend/app/core/config.py). Loaded per-project via `ProjectConfig.load_from_project()`.

## Testing

Backend: pytest with fixtures in [backend/tests/conftest.py](backend/tests/conftest.py)  
Frontend: Playwright E2E tests in [frontend/tests/e2e/](frontend/tests/e2e/)  
Run E2E with services already running or use `task start-bg` first
