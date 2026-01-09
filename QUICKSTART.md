# Quick Start Guide

Get up and running with Change-Driven Development in 10 minutes.

## Prerequisites

- Python 3.11+
- Node.js 18+
- Git
- GitHub Copilot CLI (optional, for AI execution)

## Installation

### 1. Clone & Install

```bash
# Clone repository
git clone <repository-url>
cd change-driven-dev

# Backend dependencies
cd backend
pip install -r requirements.txt

# Frontend dependencies
cd ../frontend
npm install
```

### 2. Start Services

```bash
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

Access:
- UI: http://localhost:5173
- API: http://localhost:8000/docs

## First Project

### 1. Create Project

In the UI (http://localhost:5173):
1. Click "Create New Project"
2. Enter project details:
   - **Name**: my-first-app
   - **Description**: Sample project
   - **Root Path**: `/path/to/your/project`
   - **Engine**: copilot-cli
3. Click "Create"

### 2. Initialize Configuration

Create `config.yaml` in your project directory:

```yaml
project_name: my-first-app
default_engine: copilot-cli

sandbox:
  allowed_paths:
    - "src/**"
    - "tests/**"
    - "docs/**"
  allowed_commands:
    - python
    - pytest
    - git
    - make
    - ruff
  command_timeout: 300

gates:
  enabled: true
  timeout: 60
  fail_on_error: true

metadata:
  team: engineering
  environment: development
```

### 3. Run Planner Phase

1. Click on your project
2. Navigate to "Planner" tab
3. Enter a specification:
```
Build a simple calculator module with:
- Addition, subtraction, multiplication, division functions
- Input validation for divide-by-zero
- Unit tests with pytest
- Type hints for all functions
```
4. Click "Run Planner"

The AI will generate a `plan.json` and create tasks.

### 4. Review Tasks

1. Navigate to "Tasks" tab
2. Review created tasks
3. Tasks should be in "PENDING" status

### 5. Run Architect Phase

For each task:
1. Click on task
2. Navigate to "Architect" tab
3. Add context (optional):
```
Use Python 3.11+ features
Follow PEP 8 style guide
Add docstrings for all functions
```
4. Click "Run Architect"

The AI will generate architecture options and ADRs.

### 6. Approve Tasks

1. Navigate to "Review & Approval" tab
2. Review architecture decisions
3. For each task:
   - Review version history
   - Click "Approve" to allow implementation

### 7. Configure Gates

Before running coder, set up quality gates:

1. Click on an approved task
2. Navigate to "Gates" section
3. Add gates:

```json
[
  {
    "name": "lint",
    "command": "ruff check src/",
    "pass_criteria": "exit_code_0",
    "timeout": 30
  },
  {
    "name": "tests",
    "command": "pytest tests/ -v",
    "pass_criteria": "exit_code_0",
    "timeout": 120
  }
]
```

4. Save gates configuration

### 8. Run Coder Phase

1. Navigate to "Coder" tab
2. Select an approved task
3. Click "Run Coder"

The system will:
- Bundle context (architecture, specs, history)
- Execute AI engine to generate code
- Run quality gates
- Commit to git on success

### 9. Monitor Execution

Watch real-time progress:
- Task status updates
- Gate execution results
- Git commit creation
- WebSocket live updates

### 10. Review Results

After completion:
- Check task status: `COMPLETED`
- Review git commits with structured messages
- View artifacts (transcripts, diffs)
- Check gate results (lint, tests)

## Common Workflows

### Split Complex Task

If a task is too large:
1. Navigate to task details
2. Click "Split Task"
3. Define subtasks:
```json
{
  "subtasks": [
    "Implement calculator core functions",
    "Add input validation",
    "Write unit tests"
  ]
}
```

### Merge Related Tasks

To combine related tasks:
1. Select multiple tasks
2. Click "Merge Tasks"
3. Merged task inherits all context

### Manual Gate Execution

To test gates without running coder:
1. Navigate to "Gates" tab
2. Click "Execute Gates"
3. View results without committing

### Git Status Check

Before running coder:
1. Check "Git Status" section
2. Ensure repository is clean
3. Stash or commit any uncommitted changes

## Troubleshooting

### Gates Failing

If gates fail repeatedly:
1. Check gate configuration (timeout, command)
2. Run gate commands manually to debug
3. Review gate output in results panel
4. Adjust pass criteria if needed

### Engine Errors

If AI engine fails:
1. Verify engine is installed (e.g., `gh copilot --version`)
2. Check engine credentials
3. Review engine logs in artifacts
4. Try different engine or manual mode

### Path Not Allowed

If seeing "path not allowed" errors:
1. Check `config.yaml` `allowed_paths`
2. Add necessary patterns (e.g., `lib/**`)
3. Verify no directory traversal (`../`)
4. Restart backend after config changes

### Command Blocked

If commands are blocked:
1. Add to `allowed_commands` in config
2. Remove from `blocked_commands`
3. Consider security implications
4. Use command timeout for safety

## Next Steps

- Read full [README.md](README.md) for detailed documentation
- Explore [API documentation](http://localhost:8000/docs)
- Review [SECURITY.md](docs/SECURITY.md) for security best practices
- Check example configurations in `config.yaml.example`
- Join community for support and updates

## Tips

- **Start small**: Begin with simple tasks to learn workflow
- **Use gates**: Quality gates prevent bad code from being committed
- **Review ADRs**: Architecture Decision Records provide valuable context
- **Monitor WebSocket**: Real-time updates show system health
- **Git hygiene**: Keep repository clean before running coder
- **Iterate**: Tasks can be revised and re-run as needed
