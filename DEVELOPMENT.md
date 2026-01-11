# Local Development Setup

This guide explains how to run the Change-Driven Development system locally without Docker.

## Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- [Task](https://taskfile.dev/) - Task runner (install via `brew install go-task/tap/go-task` on macOS or see [installation guide](https://taskfile.dev/installation/))
- GitHub Copilot CLI (optional, for AI features)

## Quick Start

1. **Install Task** (if not already installed):
   ```bash
   # macOS
   brew install go-task/tap/go-task
   
   # Linux
   sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b ~/.local/bin
   
   # Or using Go
   go install github.com/go-task/task/v3/cmd/task@latest
   ```

2. **Run the complete setup and start**:
   ```bash
   task start
   ```

   This will:
   - Create a Python virtual environment
   - Install backend dependencies
   - Install frontend dependencies
   - Start both backend and frontend servers

3. **Access the application**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Available Commands

View all available tasks:
```bash
task --list
```

### Setup Commands

```bash
task setup              # Set up both backend and frontend
task setup-backend      # Set up Python environment and dependencies
task setup-frontend     # Install npm dependencies
```

### Running Services

```bash
task dev                # Run both backend and frontend (parallel)
task backend            # Run only backend server
task frontend           # Run only frontend server
```

### Database Commands

```bash
task db-init            # Initialize the main database
task clean-db           # Remove all database files (WARNING: deletes data)
```

### Development Tools

```bash
task health             # Check if backend is healthy
task test-backend       # Run backend tests
task lint-backend       # Run backend linter
task format-backend     # Format backend code
```

### Cleanup

```bash
task clean              # Remove virtual env, node_modules, caches
```

## GitHub Copilot CLI Setup

The system uses GitHub Copilot CLI as the default AI engine. To set it up:

1. **Install Copilot CLI**:
   ```bash
   task install-copilot-cli
   ```

2. **Authenticate**:
   ```bash
   github-copilot-cli auth
   ```

3. **Verify installation**:
   ```bash
   github-copilot-cli --version
   ```

## Manual Setup (without Task)

If you prefer not to use Task:

### Backend

```bash
cd backend
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

### Frontend (.env.local)

```bash
VITE_BACKEND_URL=http://localhost:8000
VITE_BACKEND_WS_URL=ws://localhost:8000
```

### Backend

The backend uses SQLite databases stored in `backend/data/` by default. No additional environment variables are required for local development.

## Troubleshooting

### Backend won't start

1. Check Python version: `python3 --version` (must be 3.11+)
2. Ensure virtual environment is activated
3. Reinstall dependencies: `task setup-backend`

### Frontend won't start

1. Check Node version: `node --version` (should be 18+)
2. Clear node_modules: `task clean` then `task setup-frontend`

### Database issues

1. Check if data directory exists: `mkdir -p backend/data`
2. Initialize database: `task db-init`
3. If corrupted, reset: `task clean-db` (WARNING: deletes all data)

### GitHub Copilot CLI not found

1. Install: `task install-copilot-cli`
2. Authenticate: `github-copilot-cli auth`
3. Ensure npm global bin is in PATH: `echo $PATH | grep npm`

## Development Workflow

1. Start services: `task dev` (or run backend/frontend separately)
2. Create a project in the UI
3. Use the Planner page to generate a development plan
4. Review and approve tasks
5. Use Architect and Coder pages for implementation

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI endpoints
│   │   ├── core/         # Core utilities
│   │   ├── db/           # Database models and DAOs
│   │   ├── engines/      # AI engine integrations
│   │   ├── models/       # Pydantic models
│   │   └── services/     # Business logic
│   ├── data/             # SQLite databases
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   └── services/     # API client
│   └── package.json
└── Taskfile.yml          # Task definitions
```

## Next Steps

- Read the main [README.md](README.md) for project overview
- Check [DECISIONS.md](docs/DECISIONS.md) for architecture decisions
- Review [SECURITY.md](docs/SECURITY.md) for security considerations
