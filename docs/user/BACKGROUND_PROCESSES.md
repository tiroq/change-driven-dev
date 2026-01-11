# Background Process Management Guide

## Overview

The system can now run completely in the background without requiring multiple terminals. Process tracking is done via PID files and logs.

## Quick Start

```bash
# Start everything
task start

# Check what's running
task status-bg

# View logs
task logs
```

## Process Management

### Starting Services

```bash
# Start both backend and frontend in background
task start-bg

# Or start individually
task backend-bg
task frontend-bg
```

**What happens:**
- Backend starts on port 8000
- Frontend starts on port 5173
- PIDs saved to `.pids/backend.pid` and `.pids/frontend.pid`
- Logs written to `logs/backend.log` and `logs/frontend.log`
- Processes continue running after you close the terminal

### Checking Status

```bash
task status-bg
```

**Example output:**
```
Process Status:

✓ Backend  - Running (PID: 12345) - http://localhost:8000
✓ Frontend - Running (PID: 12346) - http://localhost:5173
```

### Viewing Logs

```bash
# All logs together
task logs

# Backend only
task logs-backend

# Frontend only
task logs-frontend
```

**Tip:** Press `Ctrl+C` to exit log viewing (processes keep running)

### Stopping Services

```bash
# Stop both
task stop-bg

# Or stop individually by killing the PID
kill $(cat .pids/backend.pid)
kill $(cat .pids/frontend.pid)
```

### Restarting Services

```bash
task restart-bg
```

This is equivalent to:
```bash
task stop-bg
task start-bg
```

## Process Tracking

### PID Files

Location: `.pids/`

- `.pids/backend.pid` - Backend process ID
- `.pids/frontend.pid` - Frontend process ID

**Manual process management:**
```bash
# Check if running
kill -0 $(cat .pids/backend.pid) && echo "Running" || echo "Not running"

# Stop process
kill $(cat .pids/backend.pid)

# Force kill
kill -9 $(cat .pids/backend.pid)
```

### Log Files

Location: `logs/`

- `logs/backend.log` - Backend output (stdout + stderr)
- `logs/frontend.log` - Frontend output (stdout + stderr)

**View logs with standard tools:**
```bash
# Tail logs
tail -f logs/backend.log

# Search logs
grep ERROR logs/backend.log

# Last 100 lines
tail -n 100 logs/backend.log

# All logs from today
grep "$(date +%Y-%m-%d)" logs/backend.log
```

## Comparison: Background vs. Foreground

### Background Mode (Recommended)

**Pros:**
- ✅ Single terminal
- ✅ Processes survive terminal close
- ✅ Clean workspace
- ✅ Easy to start/stop all services
- ✅ Centralized logging

**Cons:**
- ❌ Not interactive (can't see real-time output)
- ❌ Need to tail logs separately

**Usage:**
```bash
task start-bg
task logs  # In another terminal if you want to watch
```

### Foreground Mode

**Pros:**
- ✅ See real-time output
- ✅ Interactive debugging
- ✅ Direct `Ctrl+C` to stop

**Cons:**
- ❌ Requires 2 terminals
- ❌ Processes stop when terminal closes
- ❌ Cluttered workspace

**Usage:**
```bash
# Terminal 1
task backend

# Terminal 2
task frontend
```

## Common Workflows

### Daily Development

```bash
# Morning - Start everything
task start-bg

# Work on code (hot reload works automatically)

# Check logs occasionally
task logs-backend

# Evening - Stop everything
task stop-bg
```

### Debugging

```bash
# Stop background processes
task stop-bg

# Run in foreground to see detailed output
task backend  # In terminal 1
task frontend  # In terminal 2

# Fix issues

# Resume background mode
task start-bg
```

### After Git Pull

```bash
# Restart to pick up changes
task restart-bg
```

### Server/Remote Development

```bash
# Start services (they'll survive SSH disconnect)
task start-bg

# Verify running
task status-bg

# Logout (services keep running)
exit

# Later, reconnect and check status
task status-bg
```

## Troubleshooting

### Services won't start

```bash
# Check if already running
task status-bg

# Check for port conflicts
lsof -i :8000  # Backend
lsof -i :5173  # Frontend

# Kill conflicting processes
kill <PID>

# Try again
task start-bg
```

### Stale PID files

If `status-bg` shows "stale PID file":

```bash
# Clean up
rm .pids/*.pid

# Restart
task start-bg
```

### Can't find logs

```bash
# Ensure logs directory exists
ls -la logs/

# If missing, create and restart
mkdir -p logs
task restart-bg
```

### Services crash on startup

```bash
# Check logs for errors
cat logs/backend.log
cat logs/frontend.log

# Common issues:
# - Missing dependencies: task setup
# - Port in use: Check with lsof
# - Database issues: task db-init
```

## Integration with Systemd Services

You can use both background mode AND systemd:

- **Background mode**: Development, quick testing
- **Systemd services**: Production, auto-start on boot

```bash
# Development
task start-bg

# Production
task service-install
task service-start
```

They use different process management:
- Background: PID files in `.pids/`
- Systemd: Managed by systemd

## Advanced Usage

### Custom Log Locations

Edit Taskfile.yml to change log paths:

```yaml
nohup npm run dev > /custom/path/frontend.log 2>&1 &
```

### Multiple Instances

Run multiple instances on different ports:

```yaml
nohup ../.venv/bin/uvicorn app.main:app --port 8001 > logs/backend-8001.log 2>&1 &
```

### Log Rotation

Prevent logs from growing too large:

```bash
# Manual rotation
mv logs/backend.log logs/backend.log.old
task restart-bg

# Or use logrotate (system tool)
```

### Process Monitoring

Add to crontab for automatic restart:

```bash
# Check every 5 minutes and restart if down
*/5 * * * * cd /path/to/project && task status-bg | grep -q "Not running" && task start-bg
```

## Files Created

- `.pids/backend.pid` - Backend process ID
- `.pids/frontend.pid` - Frontend process ID  
- `logs/backend.log` - Backend logs
- `logs/frontend.log` - Frontend logs

All in `.gitignore` - won't be committed.

## See Also

- [LOCAL_SETUP.md](LOCAL_SETUP.md) - Quick setup guide
- [DEVELOPMENT.md](DEVELOPMENT.md) - Full development documentation
- [SERVICE_SETUP.md](SERVICE_SETUP.md) - Systemd service installation
