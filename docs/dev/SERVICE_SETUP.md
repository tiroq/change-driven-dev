# Setting Up as System Services

This guide explains how to run the Change-Driven Development system as systemd services on Linux.

## Prerequisites

- Ubuntu/Debian Linux (or any systemd-based distribution)
- Root/sudo access
- Completed setup: `task setup`

## Service Files

The service files in `systemd/` directory use placeholders that are automatically replaced during installation:

- `{{PROJECT_DIR}}` - Replaced with your actual project directory
- `{{USER}}` - Replaced with your username

This makes the setup portable across different installations.

## Quick Reference

The service files use **placeholders** instead of hardcoded paths:

```ini
# Template (in git):
User={{USER}}
WorkingDirectory={{PROJECT_DIR}}/backend

# After installation:
User=mysterx
WorkingDirectory=/home/mysterx/dev/change-driven-dev/backend
```

This makes the setup **portable** - it works regardless of:
- Your username
- Installation directory
- Server/machine

## Installation Steps

### Quick Installation (Recommended)

The automated script will detect your paths and configure everything:

```bash
cd /path/to/change-driven-dev
./setup-services.sh
```

This script will:
1. Detect your project directory and username
2. Replace placeholders in service files
3. Install configured services to systemd
4. Optionally enable and start services

### Manual Installation

If you prefer manual installation:

### Manual Installation

If you prefer manual installation:

#### Using Task (Automatic Path Replacement)

```bash
# Install services (automatically replaces placeholders)
task service-install

# Enable and start
task service-enable
task service-start
```

#### Manual systemd Installation

```bash
# Create temporary directory for processed service files
mkdir -p /tmp/cdd-services

# Replace placeholders with your actual paths
PROJECT_DIR="$(pwd)"
CURRENT_USER="$(whoami)"

sed -e "s|{{PROJECT_DIR}}|$PROJECT_DIR|g" \
    -e "s|{{USER}}|$CURRENT_USER|g" \
    systemd/cdd-backend.service > /tmp/cdd-services/cdd-backend.service

sed -e "s|{{PROJECT_DIR}}|$PROJECT_DIR|g" \
    -e "s|{{USER}}|$CURRENT_USER|g" \
    systemd/cdd-frontend.service > /tmp/cdd-services/cdd-frontend.service

# Install to systemd
sudo cp /tmp/cdd-services/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Clean up
rm -rf /tmp/cdd-services
```

### Original Manual Steps

### 1. Create Log Directory

```bash
mkdir -p logs
```

### 2. Enable Services (Auto-start on Boot)

```bash
sudo systemctl enable cdd-backend cdd-frontend
```

### 3. Start Services

```bash
# Start backend
sudo systemctl start cdd-backend

# Start frontend
sudo systemctl start cdd-frontend
```

## Managing Services

### Check Service Status

```bash
# Backend status
sudo systemctl status cdd-backend

# Frontend status
sudo systemctl status cdd-frontend
```

### View Logs

```bash
# Backend logs (systemd journal)
sudo journalctl -u cdd-backend -f

# Frontend logs (systemd journal)
sudo journalctl -u cdd-frontend -f

# Or view log files directly
tail -f /home/mysterx/dev/change-driven-dev/logs/backend.log
tail -f /home/mysterx/dev/change-driven-dev/logs/frontend.log
```

### Stop Services

```bash
sudo systemctl stop cdd-backend
sudo systemctl stop cdd-frontend
```

### Restart Services

```bash
sudo systemctl restart cdd-backend
sudo systemctl restart cdd-frontend
```

### Disable Services (Prevent Auto-start)

```bash
sudo systemctl disable cdd-backend
sudo systemctl disable cdd-frontend
```

## Quick Service Management with Task

Add these tasks to your Taskfile.yml for easier service management:

```yaml
  service-install:
    desc: Install systemd services
    cmds:
      - mkdir -p logs
      - sudo cp systemd/cdd-backend.service /etc/systemd/system/
      - sudo cp systemd/cdd-frontend.service /etc/systemd/system/
      - sudo systemctl daemon-reload
      - echo "Services installed. Run task service-enable to enable auto-start"

  service-enable:
    desc: Enable services to start on boot
    cmds:
      - sudo systemctl enable cdd-backend
      - sudo systemctl enable cdd-frontend
      - echo "Services enabled for auto-start"

  service-start:
    desc: Start all services
    cmds:
      - sudo systemctl start cdd-backend
      - sudo systemctl start cdd-frontend
      - sleep 2
      - task: service-status

  service-stop:
    desc: Stop all services
    cmds:
      - sudo systemctl stop cdd-backend
      - sudo systemctl stop cdd-frontend

  service-restart:
    desc: Restart all services
    cmds:
      - sudo systemctl restart cdd-backend
      - sudo systemctl restart cdd-frontend
      - sleep 2
      - task: service-status

  service-status:
    desc: Show status of all services
    cmds:
      - sudo systemctl status cdd-backend --no-pager
      - echo ""
      - sudo systemctl status cdd-frontend --no-pager

  service-logs:
    desc: Tail service logs
    cmds:
      - echo "Press Ctrl+C to exit"
      - sudo journalctl -u cdd-backend -u cdd-frontend -f
```

## Troubleshooting

### Service won't start

1. **Check service status for errors:**
   ```bash
   sudo systemctl status cdd-backend
   sudo journalctl -u cdd-backend -n 50
   ```

2. **Verify paths in service file:**
   ```bash
   # Edit service file
   sudo nano /etc/systemd/system/cdd-backend.service
   
   # Reload after changes
   sudo systemctl daemon-reload
   sudo systemctl restart cdd-backend
   ```

3. **Check permissions:**
   ```bash
   # Ensure user can access files
   ls -la /home/mysterx/dev/change-driven-dev/
   ls -la /home/mysterx/dev/change-driven-dev/.venv/
   ```

### Backend service fails

- **Check Python virtual environment exists:**
  ```bash
  test -d /home/mysterx/dev/change-driven-dev/.venv && echo "OK" || echo "Run: task setup-backend"
  ```

- **Test manual start:**
  ```bash
  cd /home/mysterx/dev/change-driven-dev/backend
  ../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
  ```

### Frontend service fails

- **Check node_modules exists:**
  ```bash
  test -d /home/mysterx/dev/change-driven-dev/frontend/node_modules && echo "OK" || echo "Run: task setup-frontend"
  ```

- **Test manual start:**
  ```bash
  cd /home/mysterx/dev/change-driven-dev/frontend
  npm run dev
  ```

### Port already in use

```bash
# Check what's using port 8000
sudo lsof -i :8000

# Check what's using port 5173
sudo lsof -i :5173

# Kill process if needed
sudo kill -9 <PID>
```

## Service File Customization

### Change User

Edit the service files and change `User=mysterx` to your username:

```bash
sudo nano /etc/systemd/system/cdd-backend.service
```

### Change Ports

**Backend (default 8000):**
Edit `/etc/systemd/system/cdd-backend.service` and change:
```ini
ExecStart=/home/mysterx/dev/change-driven-dev/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
```

**Frontend (default 5173):**
Edit `frontend/vite.config.js` and change the port, then restart service.

### Change Log Location

Edit service files and change `StandardOutput` and `StandardError` paths:

```ini
StandardOutput=append:/var/log/cdd-backend.log
StandardError=append:/var/log/cdd-backend-error.log
```

## Production Considerations

For production deployment, consider:

1. **Use production build for frontend:**
   ```bash
   # Build frontend
   cd frontend
   npm run build
   
   # Serve with nginx or similar
   ```

2. **Add reverse proxy (nginx/caddy):**
   - Proxy `/api` and `/ws` to backend
   - Serve frontend static files
   - Enable HTTPS/SSL

3. **Use environment variables:**
   - Add `EnvironmentFile=/path/to/.env` to service files
   - Store secrets securely

4. **Resource limits:**
   ```ini
   [Service]
   MemoryLimit=1G
   CPUQuota=50%
   ```

5. **Security hardening:**
   ```ini
   [Service]
   NoNewPrivileges=true
   PrivateTmp=true
   ProtectSystem=strict
   ProtectHome=read-only
   ```

## Uninstall Services

```bash
# Stop services
sudo systemctl stop cdd-backend cdd-frontend

# Disable services
sudo systemctl disable cdd-backend cdd-frontend

# Remove service files
sudo rm /etc/systemd/system/cdd-backend.service
sudo rm /etc/systemd/system/cdd-frontend.service

# Reload systemd
sudo systemctl daemon-reload
```

## Alternative: Using PM2 (Node.js Process Manager)

If you prefer PM2:

```bash
# Install PM2
npm install -g pm2

# Start backend
pm2 start --name cdd-backend "cd backend && ../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000"

# Start frontend
pm2 start --name cdd-frontend "npm run dev" --cwd frontend

# Save configuration
pm2 save

# Enable startup
pm2 startup
```

See [DEVELOPMENT.md](DEVELOPMENT.md) for local development setup.
