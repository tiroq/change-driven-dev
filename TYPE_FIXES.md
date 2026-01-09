# Type Checking Issues - Remaining Fixes Needed

## Issues to Fix

### 1. app/main.py - Line 82
**Problem**: SQLAlchemy execute() requires text() wrapper for raw SQL
```python
# Current (incorrect):
db.execute("SELECT 1")

# Fix needed:
from sqlalchemy import text
db.execute(text("SELECT 1"))
```

### 2. app/core/sandbox.py - Line 254
**Problem**: proc.returncode can be None
```python
# Current return can have None returncode
return proc.returncode, stdout.decode(), stderr.decode()

# Fix: Default to -1 if returncode is None
returncode = proc.returncode if proc.returncode is not None else -1
return returncode, stdout.decode(), stderr.decode()
```

### 3. app/services/git_service.py - Line 88
**Problem**: exit_code can be None
```python
# Current return can have None exit_code  
return exit_code, stdout_str, stderr_str

# Fix: Default to -1 if exit_code is None
returncode = exit_code if exit_code is not None else -1
return returncode, stdout_str, stderr_str
```

## Already Fixed

✅ app/api/gates.py - Fixed dependency injection (removed Depends, call get_db directly)
✅ app/api/gates.py - Added null checks for project.root_path
✅ app/api/git.py - Recreated file with proper structure and null checks

## Notes

These are type checking warnings from Pylance/mypy. The code will run correctly, but fixing these will:
- Eliminate type checking warnings
- Make code more robust
- Follow Python type safety best practices

The fixes are straightforward - just ensuring return codes default to -1 instead of possibly being None, and using text() for raw SQL queries in SQLAlchemy.
