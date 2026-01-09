.PHONY: help build up down dev logs test lint clean validate shell-be shell-fe health

help:
	@echo "Change-Driven Development - Available Commands:"
	@echo ""
	@echo "  make build       - Build all Docker images"
	@echo "  make up          - Start production containers"
	@echo "  make down        - Stop all containers"
	@echo "  make dev         - Start development containers with hot reload"
	@echo "  make logs        - Show container logs"
	@echo "  make logs-f      - Follow container logs"
	@echo "  make test        - Run backend tests"
	@echo "  make lint        - Run linters"
	@echo "  make clean       - Remove containers, volumes, and images"
	@echo "  make validate    - Run system validation"
	@echo "  make shell-be    - Open shell in backend container"
	@echo "  make shell-fe    - Open shell in frontend container"
	@echo "  make health      - Check service health"
	@echo ""

# Build Docker images
build:
	docker compose build

# Start production containers
up:
	docker compose up -d

# Stop containers
down:
	docker compose down

# Start development containers with hot reload
dev:
	docker compose -f docker compose.dev.yml up

# View logs
logs:
	docker compose logs

# Follow logs
logs-f:
	docker compose logs -f

# Run backend tests
test:
	docker compose exec backend python -m pytest tests/ -v

# Run linters
lint:
	docker compose exec backend ruff check .

# Clean up everything
clean:
	docker compose down -v
	docker compose -f docker compose.dev.yml down -v
	docker system prune -f

# Run validation script
validate:
	./validate.sh

# Backend shell
shell-be:
	docker compose exec backend /bin/bash

# Frontend shell
shell-fe:
	docker compose exec frontend /bin/sh

# Restart services
restart:
	docker compose restart

# View backend logs only
logs-be:
	docker compose logs -f backend

# View frontend logs only
logs-fe:
	docker compose logs -f frontend

# Health check
health:
	@echo "Checking backend health..."
	@curl -f http://localhost:8000/health || echo "Backend not responding"
	@echo ""
	@echo "Checking frontend health..."
	@curl -f http://localhost:5173 || echo "Frontend not responding"

	cd frontend && npm run format

# Cleanup
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleanup complete"

# Docker
docker-up:
	docker compose up -d
	@echo "✓ Services started"
	@echo "Backend API: http://localhost:8000"
	@echo "Frontend UI: http://localhost:5173"

docker-down:
	docker compose down
	@echo "✓ Services stopped"
