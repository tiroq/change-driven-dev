# Change-Driven Development

UI-first, stack-agnostic engineering control system for AI-assisted development with explicit planning, architecture review, task versioning, approvals, gates, and auditable execution.

## Overview

Change-Driven Development provides structured workflow management through distinct phases with comprehensive governance:

- **Planner**: Task breakdown and planning from specifications
- **Architect**: Architecture options, ADR generation, technical design
- **Review/Approval**: Task governance with versioning, split/merge, approval workflows
- **Coder**: Automated implementation with quality gates and git integration

## Key Features

✅ **Complete Phase Orchestration**: Planner → Architect → Review → Coder workflow  
✅ **Task Versioning**: Full audit trail of task changes with version history  
✅ **Quality Gates**: Automated validation with configurable pass/fail criteria  
✅ **Sandbox Security**: Path validation, command allowlisting, timeout enforcement  
✅ **Git Integration**: Structured commits on success with task metadata  
✅ **Engine-Agnostic**: Works with any AI engine (GitHub Copilot, OpenAI, etc.)  
✅ **Real-Time Updates**: WebSocket streaming for live progress  
✅ **Artifact Storage**: Plans, architectures, ADRs, transcripts, diffs  

## Architecture

### Backend (Python 3.11 + FastAPI)

```
backend/
├── app/
│   ├── api/              # REST API endpoints
│   │   ├── projects.py   # Project CRUD
│   │   ├── tasks.py      # Task management + versioning
│   │   ├── phase.py      # Planner/Architect/Coder orchestration
│   │   ├── gates.py      # Gate configuration + execution
│   │   ├── git.py        # Git operations
│   │   └── websocket.py  # Real-time streaming
│   ├── models/           # SQLAlchemy ORM models
│   ├── db/               # Database + DAO layer
│   ├── services/         # Business logic
│   │   ├── orchestration.py  # Phase orchestration
│   │   ├── artifacts.py      # File storage
│   │   └── git_service.py    # Git wrapper
│   ├── engines/          # AI engine adapters
│   │   ├── engine_base.py    # Protocol interface
│   │   └── copilot_cli.py    # GitHub Copilot adapter
│   └── core/             # Core utilities
│       ├── events.py     # Pub/sub event bus
│       ├── logging_config.py # Structured logging
│       ├── sandbox.py    # Security layer
│       ├── gates.py      # Quality gates
│       └── config.py     # Project configuration
├── tests/                # Test suite
└── requirements.txt      # Dependencies
```

### Frontend (React + Vite)

```
frontend/
├── src/
│   ├── pages/            # Phase-specific UIs
│   │   ├── ProjectsPage.jsx      # Project management
│   │   ├── TasksPage.jsx         # Task kanban board
│   │   ├── PlannerPage.jsx       # Planner execution
│   │   ├── ArchitectPage.jsx     # Architecture design
│   │   ├── ReviewApprovalPage.jsx # Task governance
│   │   └── CoderPage.jsx         # Implementation
│   ├── components/       # Reusable components
│   ├── services/         # API client
│   └── App.jsx           # Main app
└── package.json          # Dependencies
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git
- GitHub Copilot CLI (optional, for AI execution)

### Quick Start

1. **Install dependencies**:
```bash
# Backend
cd backend && pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

2. **Start services**:
```bash
# Backend (Terminal 1)
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (Terminal 2)
cd frontend
npm run dev
```

3. **Access the application**:
- UI: http://localhost:5173
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Project Configuration

Create a `config.yaml` in your project root (see `config.yaml.example`):

```yaml
project_name: my-project
default_engine: copilot-cli

sandbox:
  allowed_paths:
    - "src/**"
    - "tests/**"
  allowed_commands:
    - python
    - pytest
    - git

gates:
  enabled: true
  timeout: 60
  fail_on_error: true
```

## Workflow Example

### 1. Create Project
```bash
POST /api/projects/
{
  "name": "my-app",
  "description": "New application",
  "root_path": "/path/to/project",
  "default_engine": "copilot-cli"
}
```

### 2. Run Planner Phase
```bash
POST /api/phase/plan
{
  "project_id": 1,
  "spec_content": "Build a REST API with authentication..."
}
```
Creates tasks from specification, saves plan.json artifact.

### 3. Run Architect Phase (per task)
```bash
POST /api/phase/architect
{
  "project_id": 1,
  "task_id": 1,
  "context_content": "Use JWT for auth, PostgreSQL for storage..."
}
```
Generates architecture options, creates ADR documents.

### 4. Review & Approve
- View task versions and change requests
- Split complex tasks or merge related ones
- Approve tasks for implementation

### 5. Configure Gates
```bash
PUT /api/gates/task/1?project_id=1
[
  {
    "name": "lint",
    "command": "ruff check .",
    "pass_criteria": "exit_code_0",
    "timeout": 30
  },
  {
    "name": "tests",
    "command": "pytest tests/",
    "pass_criteria": "exit_code_0",
    "timeout": 300
  }
]
```

### 6. Run Coder Phase
```bash
POST /api/phase/coder
{
  "project_id": 1,
  "task_id": 1
}
```
Implements task, runs gates, commits on success.

## API Reference

### Projects
- `GET /api/projects/` - List all projects
- `POST /api/projects/` - Create new project
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project (cascades)

### Tasks
- `GET /api/tasks/?project_id={id}&status={status}` - List/filter tasks
- `POST /api/tasks/` - Create task
- `GET /api/tasks/{id}?project_id={id}` - Get task with versions
- `PATCH /api/tasks/{id}?project_id={id}` - Update task (creates version)
- `DELETE /api/tasks/{id}?project_id={id}` - Delete task
- `POST /api/tasks/{id}/split?project_id={id}` - Split task into subtasks
- `POST /api/tasks/merge?project_id={id}` - Merge tasks

### Change Requests
- `GET /api/change-requests/task/{task_id}?project_id={id}` - Get CRs for task
- `POST /api/change-requests/` - Create change request
- `PATCH /api/change-requests/{id}/approve?project_id={id}` - Approve CR
- `PATCH /api/change-requests/{id}/reject?project_id={id}` - Reject CR

### Phase Orchestration
- `POST /api/phase/plan` - Run planner phase (create tasks from spec)
- `POST /api/phase/architect` - Run architect phase (generate options/ADRs)
- `POST /api/phase/coder` - Run coder phase (implement + validate + commit)

### Quality Gates
- `GET /api/gates/task/{task_id}?project_id={id}` - Get gates for task
- `PUT /api/gates/task/{task_id}?project_id={id}` - Set gates configuration
- `POST /api/gates/execute?project_id={id}` - Execute gates for task

### Git Operations
- `GET /api/git/status?project_id={id}` - Get git status
- `POST /api/git/init?project_id={id}` - Initialize git repository
- `POST /api/git/commit` - Create manual commit
- `GET /api/git/diff?project_id={id}` - Get git diff

### Artifacts
- `GET /api/artifacts/task/{task_id}?project_id={id}` - List task artifacts
- `POST /api/artifacts/` - Upload artifact
- `GET /api/artifacts/{id}?project_id={id}` - Get artifact metadata
- `GET /api/artifacts/{id}/content?project_id={id}` - Download artifact

### WebSocket
- `ws://localhost:8000/ws/{project_id}` - Real-time event stream

## Security Model

### Sandbox Isolation

All code execution runs through the **Sandbox Security Layer**:

- **Path Validation**: Only allow file access within configured patterns (e.g., `src/**`, `tests/**`)
- **Command Allowlisting**: Restrict to safe commands (python, pytest, git, etc.)
- **Timeout Enforcement**: Kill processes exceeding configured limits
- **Directory Traversal Prevention**: Block `../` and symlink attacks

Configuration in `config.yaml`:
```yaml
sandbox:
  allowed_paths:
    - "src/**"
    - "tests/**"
    - "docs/**"
  blocked_paths:
    - ".env"
    - "secrets/**"
  allowed_commands:
    - python
    - pytest
    - git
    - make
  blocked_commands:
    - rm
    - curl
  command_timeout: 300
```

### Quality Gates

Gates validate code before committing:

**Pass Criteria Types**:
1. `exit_code_0` - Command must return 0
2. `output_contains` - Output must contain string
3. `output_matches` - Output must match regex pattern

**Example Gates**:
```yaml
gates:
  - name: lint
    command: ruff check .
    pass_criteria: exit_code_0
    timeout: 30
  - name: type-check
    command: mypy src/
    pass_criteria: exit_code_0
    timeout: 60
  - name: tests
    command: pytest tests/ -v
    pass_criteria: output_contains
    expected_value: "passed"
    timeout: 300
```

## Data Model

### Database Schema

Each project has a dedicated SQLite database with 9 tables:

- **projects** - Project metadata
- **tasks** - Task definitions (title, description, status, priority)
- **task_versions** - Version history (phase, gates, created_at)
- **change_requests** - Proposed changes (type, status, diff)
- **approvals** - Approval decisions (approved_by, notes)
- **artifacts** - File storage (type, storage_path, sha256)
- **runs** - Execution history (engine, phase, status)
- **control_state** - Workflow state machine
- **events** - Audit trail (type, timestamp, payload)

### Task Lifecycle

```
PENDING → APPROVED → IN_PROGRESS → COMPLETED
   ↓          ↓            ↓
REJECTED   BLOCKED     FAILED
```

**State Transitions**:
- Task created: `PENDING`
- Change request approved: `APPROVED`
- Coder starts: `IN_PROGRESS`
- Gates pass + commit: `COMPLETED`
- Gates fail: Remains `APPROVED` for retry

## Event System

Real-time event streaming via WebSocket:

**Event Types**:
- `task.created`, `task.updated`, `task.deleted`
- `change_request.created`, `change_request.approved`
- `phase.started`, `phase.completed`, `phase.failed`
- `gate.executed`, `gate.passed`, `gate.failed`
- `artifact.created`, `git.committed`

Subscribe via WebSocket:
```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/${projectId}`);
ws.onmessage = (event) => {
  const { event_type, payload } = JSON.parse(event.data);
  console.log(`Event: ${event_type}`, payload);
};
```

## Development

### Running Tests
```bash
cd backend
pytest tests/ -v
```

### Code Quality
```bash
# Linting
ruff check .

# Type checking
mypy app/

# Formatting
ruff format .
```

### Project Scripts
```bash
make dev      # Start development servers
make test     # Run test suite
make lint     # Run linters
```

## License

MIT License - see LICENSE file for details

