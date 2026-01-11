# Local Development Setup

## Quick Start (Background Mode)

1. **Ensure you have installed:**
   - Python 3.11+
   - Node.js 18+
   - Task (already installed at `/snap/bin/task`)

2. **Start everything in background:**
   ```bash
   task start
   ```

3. **Check status:**
   ```bash
   task status-bg
   ```

4. **Access the app:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000/docs

## Alternative: Run in Separate Terminals

If you prefer seeing logs in real-time:

**Terminal 1 - Start Backend:**
```bash
task backend
```

**Terminal 2 - Start Frontend:**
```bash
task frontend
```

## Background Process Management

```bash
# Start both in background
task start-bg

# Check status
task status-bg

# View logs
task logs              # All logs
task logs-backend      # Backend only
task logs-frontend     # Frontend only

# Restart services
task restart-bg

# Stop services
task stop-bg
```

Process tracking:
- PIDs stored in `.pids/backend.pid` and `.pids/frontend.pid`
- Logs stored in `logs/backend.log` and `logs/frontend.log`

## GitHub Copilot CLI Setup (Required for Planner)

```bash
# Install
task install-copilot-cli

# Authenticate
github-copilot-cli auth

# Test
github-copilot-cli --version
```

## Useful Commands

```bash
# View all tasks
task --list

# Background process management
task start-bg          # Start in background
task stop-bg           # Stop background processes
task restart-bg        # Restart services
task status-bg         # Check process status
task logs              # Tail all logs
task logs-backend      # Tail backend logs only
task logs-frontend     # Tail frontend logs only

# Database
task clean-db          # Clean database (WARNING: deletes data!)

# Development
task health            # Check backend health
task clean             # Clean everything (also stops processes)
```

## Differences from Docker Setup

- Backend runs on Python virtual environment at `.venv/`
- Frontend uses `.env.local` for localhost proxy (not Docker service names)
- GitHub Copilot CLI runs natively (not in container)
- Databases stored in `backend/data/`
- Hot reload works for both backend and frontend

See [DEVELOPMENT.md](DEVELOPMENT.md) for full documentation.
