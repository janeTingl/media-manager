#!/usr/bin/env python3
"""
Database migration script for multi-library support.

This script ensures the database schema is up-to-date with the latest changes.
Run this after updating to a version with multi-library support.
"""

from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from media_manager.persistence.database import init_database_service
from media_manager.settings import get_settings


def migrate_database():
    """Run database migration."""
    print("Multi-Library Database Migration")
    print("=" * 50)
    
    # Get database URL from settings
    settings = get_settings()
    db_url = settings.get_database_url()
    db_path = settings.get_database_path()
    
    print(f"\nDatabase location: {db_path}")
    
    # Check if database exists
    db_file = Path(db_path)
    if not db_file.exists():
        print("\nNo existing database found. Creating new database with multi-library support...")
    else:
        print("\nExisting database found. Updating schema...")
    
    # Initialize database service (this will create/update tables)
    try:
        init_database_service(db_url, auto_migrate=False)
        print("\n✓ Database schema updated successfully!")
        print("\nNew fields added to Library table:")
        print("  - is_active: Boolean flag for active/inactive libraries")
        print("  - scan_roots: JSON array of paths to scan")
        print("  - default_destination: Default path for processed files")
        print("  - color: UI color for library identification")
        print("\nYou can now use the Library Manager to create and manage multiple libraries.")
        print("Access it via: File > Manage Libraries (Ctrl+L)")
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    migrate_database()
