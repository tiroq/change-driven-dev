#!/usr/bin/env python3
"""
Migrate existing project databases to use Alembic migrations.

This script:
1. Discovers all project_*.db files in data/
2. For each database, stamps it with the current migration version
3. Runs any pending migrations

Usage:
    python scripts/migrate_existing_dbs.py [--dry-run] [--data-dir PATH]
"""

import argparse
import subprocess
import sys
from pathlib import Path


def find_project_databases(data_dir: Path) -> list[tuple[int, Path]]:
    """Find all project_*.db files and extract project IDs"""
    databases = []
    
    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}")
        return databases
    
    for db_file in data_dir.glob("project_*.db"):
        try:
            # Extract project ID from filename
            project_id = int(db_file.stem.split("_")[1])
            databases.append((project_id, db_file))
        except (IndexError, ValueError):
            print(f"Warning: Skipping invalid database file: {db_file}")
    
    return sorted(databases)


def run_alembic_command(db_url: str, *args, dry_run: bool = False) -> bool:
    """Run an alembic command with the specified database URL"""
    backend_dir = Path(__file__).parent.parent
    alembic_ini = backend_dir / "alembic.ini"
    
    if not alembic_ini.exists():
        print(f"Error: alembic.ini not found at {alembic_ini}")
        return False
    
    cmd = [sys.executable, "-m", "alembic", "-c", str(alembic_ini)] + list(args)
    
    if dry_run:
        print(f"[DRY RUN] Would run: {' '.join(cmd)}")
        print(f"[DRY RUN] With ALEMBIC_DB_URL={db_url}")
        return True
    
    import os
    env = os.environ.copy()
    env["ALEMBIC_DB_URL"] = db_url
    
    try:
        result = subprocess.run(
            cmd,
            cwd=backend_dir,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running alembic command: {e.stderr}")
        return False


def check_migration_status(db_url: str, dry_run: bool = False) -> str:
    """Check current migration version of a database"""
    backend_dir = Path(__file__).parent.parent
    alembic_ini = backend_dir / "alembic.ini"
    
    cmd = [sys.executable, "-m", "alembic", "-c", str(alembic_ini), "current"]
    
    if dry_run:
        return "unknown (dry-run)"
    
    import os
    env = os.environ.copy()
    env["ALEMBIC_DB_URL"] = db_url
    
    try:
        result = subprocess.run(
            cmd,
            cwd=backend_dir,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip() or "No migration version"
    except subprocess.CalledProcessError:
        return "No alembic_version table (needs stamping)"


def migrate_database(project_id: int, db_path: Path, dry_run: bool = False) -> bool:
    """Migrate a single project database"""
    db_url = f"sqlite:///{db_path.absolute()}"
    
    print(f"\n{'='*60}")
    print(f"Project {project_id}: {db_path}")
    print(f"{'='*60}")
    
    # Check current migration status
    current_version = check_migration_status(db_url, dry_run)
    print(f"Current migration: {current_version}")
    
    # If no alembic_version table, stamp with current head
    # This handles databases created with Base.metadata.create_all()
    if "No alembic_version table" in current_version or "No migration version" in current_version:
        print("Database has no migration tracking. Stamping with current version...")
        if not run_alembic_command(db_url, "stamp", "head", dry_run=dry_run):
            print(f"❌ Failed to stamp database for project {project_id}")
            return False
        print("✅ Database stamped successfully")
        # After stamping, no upgrade is needed (already at head)
        print(f"✅ Project {project_id} is now at migration head")
        return True
    
    # Run any pending migrations
    print("Checking for pending migrations...")
    if not run_alembic_command(db_url, "upgrade", "head", dry_run=dry_run):
        print(f"❌ Failed to upgrade database for project {project_id}")
        return False
    
    print(f"✅ Successfully migrated project {project_id}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Migrate existing project databases to use Alembic"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).parent.parent / "data_backup",
        help="Path to data directory containing project_*.db files"
    )
    
    args = parser.parse_args()
    
    print("Database Migration Tool")
    print("=" * 60)
    
    # Find all project databases
    databases = find_project_databases(args.data_dir)
    
    if not databases:
        print(f"\nNo project databases found in {args.data_dir}")
        print("\nNote: Looking for files matching pattern 'project_*.db'")
        return 0
    
    print(f"\nFound {len(databases)} project database(s):")
    for project_id, db_path in databases:
        print(f"  - Project {project_id}: {db_path}")
    
    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made")
    
    print()
    
    # Migrate each database
    success_count = 0
    failure_count = 0
    
    for project_id, db_path in databases:
        if migrate_database(project_id, db_path, dry_run=args.dry_run):
            success_count += 1
        else:
            failure_count += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("Migration Summary")
    print(f"{'='*60}")
    print(f"Total databases: {len(databases)}")
    print(f"✅ Successful: {success_count}")
    if failure_count > 0:
        print(f"❌ Failed: {failure_count}")
    
    return 0 if failure_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
