#!/usr/bin/env python
"""
Clean Alembic Files Script
This script removes all existing migration files and creates a fresh initial migration.
"""

import os
import sys
import shutil
import glob
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🧹 Cleaning up Alembic files...")

# Step 1: Backup current migration files
print("\n1️⃣ Backing up current migration files...")
if not os.path.exists("alembic_backup"):
    os.makedirs("alembic_backup")

for migration_file in glob.glob("alembic/versions/*.py"):
    shutil.copy(migration_file, "alembic_backup/")
print("✅ Migration files backed up to alembic_backup/")

# Step 2: Remove all existing migration files
print("\n2️⃣ Removing all existing migration files...")
for migration_file in glob.glob("alembic/versions/*.py"):
    os.remove(migration_file)
print("✅ All migration files removed")

print("\n✨ Alembic files cleaned up!")
print("Now you can create a fresh initial migration with:")
print("python scripts/create_initial_migration.py")