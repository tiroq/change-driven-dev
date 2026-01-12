# Database Migration Guide - PostgreSQL Support

## Overview

PostgreSQL database support has been added to Change-Driven Development. The system now supports both SQLite (default) and PostgreSQL backends with minimal configuration changes.

## What Changed

### Core Changes

1. **Configuration** ([backend/app/core/config.py](backend/app/core/config.py))
   - Added `DatabaseConfig` class with fields for both SQLite and PostgreSQL
   - SQLite: `type`, `path`
   - PostgreSQL: `type`, `host`, `port`, `database`, `username`, `password`, `pool_size`, `max_overflow`, `pool_timeout`

2. **Database Manager** ([backend/app/db/database.py](backend/app/db/database.py))
   - Refactored `DatabaseManager` to accept `DatabaseConfig`
   - Dynamic URL building based on database type
   - Conditional engine kwargs (SQLite: `check_same_thread=False`, PostgreSQL: connection pooling)
   - **Multi-tenancy**: PostgreSQL uses schemas (`project_1`, `project_2`) instead of separate database files
   - Schema-based isolation with automatic `SET search_path`

3. **Dependencies** ([backend/requirements.txt](backend/requirements.txt), [backend/pyproject.toml](backend/pyproject.toml))
   - Added `psycopg2-binary==2.9.9` (PostgreSQL driver)
   - Added `alembic==1.13.1` (migration framework)
   - Added `pyyaml==6.0.1` (config parsing)

4. **Migrations** ([backend/alembic/](backend/alembic/))
   - Initialized Alembic framework
   - Created initial schema migration
   - `env.py` configured to read database type from `config.yaml`

## Configuration

### SQLite (Default)

```yaml
database:
  type: sqlite
  path: ./data
```

### PostgreSQL

```yaml
database:
  type: postgresql
  host: localhost
  port: 5432
  database: change_driven_dev
  username: cdd_user
  password: your_secure_password
  pool_size: 5
  max_overflow: 10
  pool_timeout: 30
```

## Multi-Project Architecture

| Database Type | Project Isolation Method |
|--------------|-------------------------|
| SQLite | Separate database files: `data/project_1.db`, `data/project_2.db` |
| PostgreSQL | Schemas in single database: `project_1`, `project_2` |

PostgreSQL approach advantages:
- Easier backups (single database)
- Simpler connection management
- Schema-level isolation still provides security
- Better for cloud/managed database services

## Migration Commands

```bash
# Generate new migration after model changes
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## Testing

Tests still use in-memory SQLite for speed and isolation. To test PostgreSQL:

1. Set up PostgreSQL database
2. Create test config.yaml with PostgreSQL settings
3. Run backend with PostgreSQL config
4. Run E2E tests (frontend/tests/e2e)

##Known Issues

- **Test failures**: Test suite needs updates to handle new DatabaseManager signature
  - `conftest.py` mocks need adjustment for `DatabaseConfig` parameter
  - Generator side_effects may need correction
- **PostgreSQL search_path**: Event listener approach needs verification with real PostgreSQL instance

## Next Steps

1. Fix test suite (update conftest.py mocks)
2. Test with actual PostgreSQL instance
3. Add data migration tool for SQLite → PostgreSQL conversion
4. Document connection pooling best practices
5. Add PostgreSQL-specific performance tuning guide

## Files Modified

- [backend/app/core/config.py](backend/app/core/config.py) - DatabaseConfig class
- [backend/app/db/database.py](backend/app/db/database.py) - Multi-database support
- [backend/requirements.txt](backend/requirements.txt) - Dependencies
- [backend/pyproject.toml](backend/pyproject.toml) - Dependencies
- [config.yaml.example](config.yaml.example) - Database config examples
- [backend/tests/conftest.py](backend/tests/conftest.py) - Test mocks (needs further work)
- [backend/alembic/](backend/alembic/) - Migration framework

## Success Criteria

- ✅ DatabaseConfig added to config.py
- ✅ DatabaseManager supports both SQLite and PostgreSQL
- ✅ Dependencies installed (psycopg2-binary, alembic, pyyaml)
- ✅ Alembic initialized with initial migration
- ✅ Config examples updated
- ⚠️  Tests need fixes (mock adjustments)
- 🔲 PostgreSQL instance testing required
