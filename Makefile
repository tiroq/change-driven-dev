.PHONY: help dev test lint fmt clean install docker-up docker-down

help:
	@echo "Change-Driven Development - Development Commands"
	@echo ""
	@echo "Available targets:"
	@echo "  make dev         - Run backend and frontend in development mode"
	@echo "  make install     - Install all dependencies (backend + frontend)"
	@echo "  make test        - Run all tests"
	@echo "  make lint        - Run linters on backend and frontend"
	@echo "  make fmt         - Format code (backend + frontend)"
	@echo "  make clean       - Remove build artifacts and cache files"
	@echo "  make docker-up   - Start services with docker-compose"
	@echo "  make docker-down - Stop docker-compose services"
	@echo ""

# Development
dev:
	@echo "Starting development servers..."
	@echo "Backend will run on http://localhost:8000"
	@echo "Frontend will run on http://localhost:5173"
	@./scripts/dev.sh

# Installation
install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✓ All dependencies installed"

# Testing
test:
	@echo "Running backend tests..."
	cd backend && python -m pytest tests/ -v
	@echo "Running frontend tests..."
	cd frontend && npm test

# Linting
lint:
	@echo "Linting backend (ruff)..."
	cd backend && ruff check app/
	@echo "Linting frontend (eslint)..."
	cd frontend && npm run lint

# Formatting
fmt:
	@echo "Formatting backend code..."
	cd backend && ruff format app/
	@echo "Formatting frontend code..."
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
	docker-compose up -d
	@echo "✓ Services started"
	@echo "Backend API: http://localhost:8000"
	@echo "Frontend UI: http://localhost:5173"

docker-down:
	docker-compose down
	@echo "✓ Services stopped"
