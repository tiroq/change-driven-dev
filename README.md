# Change-Driven Development

Change-Driven Development framework for building AI-assisted systems with explicit planning, architecture review, task versioning, approvals, and auditable execution. Engine-agnostic (Copilot, Codex), UI-first, and gate-controlled.

## Overview

A UI-first, stack-agnostic engineering control system for AI-assisted development. This framework provides structured workflow management through distinct phases:

- **Planner**: Initial task planning and requirement gathering
- **Architect**: Architectural design and technical review
- **Review/Approval**: Human or automated review gates with approval workflows
- **Coder**: Code implementation and execution

## Core Concepts

- **Tasks**: Versioned objects that flow through development phases
- **Change Requests**: Versioned changes proposed at each phase, requiring approval
- **Approvals**: Audit trail of decisions and gate controls
- **Projects**: Independent workspaces, each with its own SQLite database
- **Engine-Agnostic**: Works with any AI engine (GitHub Copilot, OpenAI Codex, etc.)

## Architecture

### Backend (Python 3.11 + FastAPI)

```
backend/
├── app/
│   ├── api/           # API endpoints
│   ├── models/        # Database models
│   ├── db/            # Database connection & management
│   ├── services/      # Orchestration and business logic
│   └── core/          # Core utilities and config
├── requirements.txt   # Python dependencies
└── pyproject.toml     # Project metadata
```

### Frontend (React + Vite)

```
frontend/
├── src/
│   ├── components/    # Reusable UI components
│   ├── pages/         # Page components for each phase
│   ├── services/      # API service layer
│   └── App.jsx        # Main application component
├── package.json       # Node dependencies
└── vite.config.js     # Vite configuration
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Run the FastAPI server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install Node dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

The UI will be available at `http://localhost:3000`

## API Endpoints

### Projects
- `GET /api/projects/` - List all projects
- `POST /api/projects/` - Create new project
- `GET /api/projects/{id}` - Get project details

### Tasks
- `GET /api/tasks/` - List all tasks
- `POST /api/tasks/` - Create new task
- `GET /api/tasks/{id}` - Get task details
- `POST /api/tasks/{id}/advance` - Advance task to next phase

### Change Requests
- `GET /api/change-requests/` - List all change requests
- `POST /api/change-requests/` - Create new change request
- `GET /api/change-requests/{id}` - Get change request details
- `POST /api/change-requests/{id}/submit` - Submit for approval
- `POST /api/change-requests/{id}/approve` - Approve change request
- `POST /api/change-requests/{id}/reject` - Reject change request

## Database

Each project maintains its own SQLite database in the `data/` directory:
- Location: `./data/project_{id}.db`
- Schema includes: Projects, Tasks, ChangeRequests, Approvals
- Versioning support for tasks and change requests

## Development Status

**v0.1.0 - Skeleton/Scaffold Phase**

This is the initial skeleton with:
- ✅ Basic folder structure
- ✅ Database models for core concepts
- ✅ Minimal API endpoints (placeholders)
- ✅ Frontend UI placeholders for all phases
- ✅ Orchestration flow skeleton
- ⏳ Business logic (to be implemented)
- ⏳ AI engine integration (to be implemented)
- ⏳ Full CRUD operations (to be implemented)

## License

MIT License - see LICENSE file for details
