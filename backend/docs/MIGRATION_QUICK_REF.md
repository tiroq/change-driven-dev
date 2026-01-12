# Database Migrations - Quick Reference

## Current Status
**Migration Version:** `e6e5369fb4d1` (complete_initial_schema)  
**Tables:** 8 (projects, tasks, change_requests, approvals, artifacts, task_versions, runs, control_state)  
**Status:** ✅ Production Ready

## Common Commands

### Check Migration Status
```bash
cd backend
alembic current          # Show current version
alembic history          # Show all migrations
```

### Apply Migrations
```bash
alembic upgrade head     # Upgrade to latest
alembic downgrade -1     # Downgrade one version
```

### Create New Migration
```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "add_user_field"

# Manual migration (empty template)
alembic revision -m "custom_data_migration"
```

### Migrate Existing Databases
```bash
# Test first
python scripts/migrate_existing_dbs.py --dry-run

# Execute
python scripts/migrate_existing_dbs.py
```

## Architecture

### Production Mode
- **SQLite:** `data/project_{id}.db` per project
- **PostgreSQL:** Schemas `project_1`, `project_2`, etc.
- **Schema Creation:** Via Alembic migrations (`run_migrations()`)

### Test Mode
- **Database:** In-memory SQLite (`:memory:`)
- **Schema Creation:** Direct `create_all()` for speed
- **Isolation:** Single shared database, cleared between tests

## When to Create Migration

✅ **Always migrate for:**
- Adding/removing tables
- Adding/removing columns
- Changing column types
- Adding/removing constraints (FK, UNIQUE, CHECK)
- Adding/removing indexes
- Modifying enum values

❌ **Don't need migration for:**
- Code-only changes (services, routes, etc.)
- Configuration changes
- Test data changes

## Migration Workflow

1. **Modify models** in [backend/app/models/models.py](backend/app/models/models.py)
2. **Generate migration**
   ```bash
   alembic revision --autogenerate -m "description"
   ```
3. **Review migration** in `backend/alembic/versions/{revision}_description.py`
   - Check table/column names
   - Verify foreign keys
   - Confirm enum handling
   - Review up/down operations
4. **Test migration**
   ```bash
   # Backup database first!
   cp data/project_1.db data/project_1.db.backup
   
   # Apply migration
   alembic upgrade head
   
   # Test application
   python -m pytest tests/
   ```
5. **Commit migration file** to version control

## Troubleshooting

### Migration fails: "table already exists"
The database was created with `create_all()`. Stamp it:
```bash
alembic stamp head
```

### Need to undo last migration
```bash
alembic downgrade -1
```

### Want to see SQL without executing
```bash
alembic upgrade head --sql
```

### Multiple heads (branching)
```bash
alembic merge {revision1} {revision2} -m "merge branches"
```

### Migration out of sync with models
```bash
# See what would change
alembic revision --autogenerate -m "sync" --sql

# If clean, delete the empty migration file
rm backend/alembic/versions/{revision}_sync.py
```

## Database Schema Overview

```
projects (1) ─────┬─── (N) tasks ─────┬─── (N) change_requests
       │          │                    │
       │          ├─── (N) approvals   ├─── (N) approvals
       │          │                    │
       │          ├─── (N) task_versions
       │          │
       │          └─── (N) runs ───┬─── (N) artifacts
       │                           │
       ├─── (N) artifacts ◄────────┘
       │
       └─── (1) control_state (UNIQUE)
```

## Testing Migrations

Run migration-specific tests:
```bash
python -m pytest tests/test_migrations.py -v
```

Run full test suite:
```bash
python -m pytest tests/ -v
```

## Emergency Rollback

### SQLite (per-project databases)
```bash
# Restore from backup
cp data_backup/project_1.db data/project_1.db

# Or downgrade migration
alembic downgrade {previous_revision}
```

### PostgreSQL (schema-based)
```bash
# Downgrade specific schema
ALEMBIC_DB_URL="postgresql://..." alembic downgrade {previous_revision}
```

## Files Reference

- **Migrations:** `backend/alembic/versions/`
- **Alembic config:** `backend/alembic.ini`
- **Alembic env:** `backend/alembic/env.py`
- **Database manager:** `backend/app/db/database.py`
- **Models:** `backend/app/models/models.py`
- **Migration tool:** `backend/scripts/migrate_existing_dbs.py`

## Further Reading

- Full implementation details: [MIGRATION_IMPLEMENTATION.md](MIGRATION_IMPLEMENTATION.md)
- Database architecture: [DATABASE_MIGRATION.md](DATABASE_MIGRATION.md)
- Alembic docs: https://alembic.sqlalchemy.org/
