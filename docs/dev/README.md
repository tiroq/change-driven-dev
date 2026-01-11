# Developer Documentation

This directory contains technical documentation for developers working with the Change-Driven Development system.

## Setup & Deployment

### [DEVELOPMENT.md](DEVELOPMENT.md)
Local development setup using Task runner. Covers:
- Prerequisites and dependencies
- Backend and frontend setup
- Development workflow
- Running services locally
- Code quality tools

**Start here** for local development.

### [DEPLOYMENT.md](DEPLOYMENT.md)
Production deployment guide. Covers:
- Production setup with Nginx
- Systemd service configuration
- Security hardening
- SSL/TLS setup
- Monitoring and logging

### [LOCAL_SETUP.md](LOCAL_SETUP.md)
Alternative local setup without Docker. Covers:
- Manual Python/Node.js setup
- Direct service execution
- Development without containerization

### [SERVICE_SETUP.md](SERVICE_SETUP.md)
Running as systemd services on Linux. Covers:
- Service file configuration
- Installation and enablement
- Service management commands
- Log access
- Troubleshooting

## Testing

### [TESTING.md](TESTING.md)
Comprehensive testing guide. Covers:
- Backend tests with pytest
- E2E tests with Playwright
- Test commands and options
- Writing new tests
- CI/CD integration

## Related Documentation

- [User Documentation](../user/README.md) - End-user guides and tutorials
- [Reference Documentation](../reference/README.md) - Core concepts
- [Main README](../../README.md) - Project overview

## Quick Commands

```bash
# Development
task backend              # Start backend dev server
task frontend             # Start frontend dev server
task start-bg             # Start both in background

# Testing
task test                 # Run all tests
task test-backend         # Backend tests only
task test-e2e             # E2E tests only

# Quality
task lint-backend         # Run linters
task format-backend       # Format code
```

## Architecture

See the [Main README](../../README.md#architecture) for:
- Backend structure (FastAPI)
- Frontend structure (React + Vite)
- Database schema
- API reference
- Event system

---

For documentation standards and guidelines, see [DOCUMENTATION_STANDARDS.md](../DOCUMENTATION_STANDARDS.md)
