# Docker Deployment Guide

Complete guide for running Change-Driven Development with Docker.

## Quick Start

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 2. Start Services

**Production Mode:**
```bash
# Build and start
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

**Development Mode (with hot reload):**
```bash
# Start dev environment
docker-compose -f docker-compose.dev.yml up

# Or use Makefile
make dev
```

### 3. Access Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Configuration

### Environment Variables

Edit `.env` file to configure:

```bash
# Backend
BACKEND_PORT=8000
BACKEND_LOG_LEVEL=info

# Frontend
FRONTEND_PORT=5173
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws

# Database & Storage
DATA_DIR=/app/data
ARTIFACTS_DIR=/app/artifacts

# Security
SECRET_KEY=your-secret-key-here

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

## Docker Commands

### Using Makefile (Recommended)

```bash
make build      # Build images
make up         # Start production
make dev        # Start development
make down       # Stop containers
make logs       # View logs
make test       # Run tests
make clean      # Clean everything
make validate   # Run validation
```

### Using Docker Compose Directly

```bash
# Build
docker-compose build

# Start (detached)
docker-compose up -d

# Start (interactive)
docker-compose up

# Stop
docker-compose down

# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Remove everything
docker-compose down -v
```

## Container Management

### Access Container Shell

```bash
# Backend
docker-compose exec backend /bin/bash

# Frontend
docker-compose exec frontend /bin/sh
```

### Run Commands in Container

```bash
# Run tests
docker-compose exec backend pytest tests/ -v

# Run linter
docker-compose exec backend ruff check .

# Database migrations
docker-compose exec backend python -m alembic upgrade head
```

### View Container Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100
```

## Development Workflow

### Hot Reload Setup

Development mode automatically enables hot reload:

```bash
# Start dev environment
make dev

# Or
docker-compose -f docker-compose.dev.yml up
```

Changes to code will automatically reload:
- **Backend**: Uvicorn auto-reload enabled
- **Frontend**: Vite HMR (Hot Module Replacement)

### Volume Mounts

Development containers mount source code:
- `./backend:/app` - Backend source
- `./frontend:/app` - Frontend source
- `./backend/data:/app/data` - Database files
- `./backend/artifacts:/app/artifacts` - Artifacts
- `./backend/logs:/app/logs` - Log files

## Production Deployment

### Build Optimized Images

```bash
# Build production images
docker-compose build --no-cache

# Start production services
docker-compose up -d
```

### Health Checks

Containers include health checks:

```bash
# Check container health
docker-compose ps

# Manual health check
curl http://localhost:8000/health
```

### Resource Limits

Add resource limits in `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 512M
```

## Networking

### Container Network

Services communicate via `cdd-network`:
- Backend accessible at: `http://backend:8000`
- Frontend accessible at: `http://frontend:80`

### Port Mapping

Default ports (configurable via `.env`):
- Backend: `8000:8000`
- Frontend: `5173:80` (dev) or `80:80` (prod)

## Data Persistence

### Volumes

Data persists in Docker volumes:
- `backend-data` - Database files
- `backend-artifacts` - Artifact storage
- `backend-logs` - Application logs

### Backup Data

```bash
# Backup database
docker cp cdd-backend:/app/data ./backup/data

# Backup artifacts
docker cp cdd-backend:/app/artifacts ./backup/artifacts
```

### Restore Data

```bash
# Restore database
docker cp ./backup/data cdd-backend:/app/

# Restore artifacts
docker cp ./backup/artifacts cdd-backend:/app/
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs backend

# Check container status
docker-compose ps

# Rebuild image
docker-compose build --no-cache backend
docker-compose up -d backend
```

### Port Already in Use

```bash
# Change port in .env
BACKEND_PORT=8001
FRONTEND_PORT=5174

# Restart
docker-compose down
docker-compose up -d
```

### Database Issues

```bash
# Reset database
docker-compose down -v
docker-compose up -d

# Or manually
docker-compose exec backend rm -rf /app/data/*.db
docker-compose restart backend
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R $USER:$USER backend/data
sudo chown -R $USER:$USER backend/artifacts
sudo chown -R $USER:$USER backend/logs
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Docker Build

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build images
        run: docker-compose build
      
      - name: Run tests
        run: docker-compose run backend pytest
      
      - name: Push to registry
        run: |
          docker tag cdd-backend registry/cdd-backend:latest
          docker push registry/cdd-backend:latest
```

## Advanced Configuration

### Custom Docker Network

```yaml
networks:
  cdd-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

### Using External Database

```yaml
services:
  backend:
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/cdd
```

### SSL/TLS Setup

Mount certificates in nginx:

```yaml
frontend:
  volumes:
    - ./certs:/etc/nginx/certs
```

## Monitoring

### Container Stats

```bash
# Real-time stats
docker stats

# Specific container
docker stats cdd-backend
```

### Logs Management

```bash
# Limit log size in docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## Cleanup

### Remove Containers

```bash
# Stop and remove
docker-compose down

# Remove volumes too
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

### System Cleanup

```bash
# Remove unused resources
docker system prune -a

# Remove volumes
docker volume prune
```

## Support

For issues or questions:
1. Check container logs: `docker-compose logs -f`
2. Verify health: `curl http://localhost:8000/health`
3. Review environment: `docker-compose config`
4. Run validation: `./validate.sh`
