# Service Installation - Quick Reference

## What Changed

The service files now use **placeholders** instead of hardcoded paths:

```ini
# Old (hardcoded):
User=mysterx
WorkingDirectory=/home/mysterx/dev/change-driven-dev/backend

# New (placeholders):
User={{USER}}
WorkingDirectory={{PROJECT_DIR}}/backend
```

This makes the setup **portable** - it works regardless of:
- Your username
- Installation directory
- Server/machine

## Installation Methods

### Method 1: Automated Script (Easiest)
```bash
./setup-services.sh
```
✅ Auto-detects paths
✅ Replaces placeholders
✅ Interactive prompts

### Method 2: Using Task
```bash
task service-install  # Detects paths automatically
task service-enable
task service-start
```
✅ One-command installation
✅ Automatic path detection

### Method 3: Manual
```bash
# From project directory
PROJECT_DIR="$(pwd)"
CURRENT_USER="$(whoami)"

# Process service files
mkdir -p /tmp/cdd-services
sed -e "s|{{PROJECT_DIR}}|$PROJECT_DIR|g" \
    -e "s|{{USER}}|$CURRENT_USER|g" \
    systemd/cdd-backend.service > /tmp/cdd-services/cdd-backend.service

sed -e "s|{{PROJECT_DIR}}|$PROJECT_DIR|g" \
    -e "s|{{USER}}|$CURRENT_USER|g" \
    systemd/cdd-frontend.service > /tmp/cdd-services/cdd-frontend.service

# Install
sudo cp /tmp/cdd-services/*.service /etc/systemd/system/
sudo systemctl daemon-reload
rm -rf /tmp/cdd-services

# Enable and start
sudo systemctl enable cdd-backend cdd-frontend
sudo systemctl start cdd-backend cdd-frontend
```

## Placeholders Used

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{PROJECT_DIR}}` | Full path to project root | `/home/user/projects/change-driven-dev` |
| `{{USER}}` | Username running the services | `john` |

## Verifying Installation

After installation, check that placeholders were replaced:

```bash
# View installed service file
cat /etc/systemd/system/cdd-backend.service

# Should show real paths like:
# User=mysterx
# WorkingDirectory=/home/mysterx/dev/change-driven-dev/backend
```

## Benefits

1. **Portable** - Clone and run anywhere
2. **Multi-user** - Each user gets correct paths
3. **Safe** - No hardcoded paths in git
4. **Flexible** - Easy to customize

See [SERVICE_SETUP.md](SERVICE_SETUP.md) for full documentation.
