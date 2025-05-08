#!/usr/bin/env python
"""
Production Migration Checklist Script
This script helps verify that all prerequisites are met before applying migrations to production.
"""

import os
import sys
import subprocess
from dotenv import load_dotenv
import psycopg2
from datetime import datetime

# Load environment variables
load_dotenv()

# Get the production database URL
PROD_DB_URL = os.getenv("PROD_DATABASE_URL")

if not PROD_DB_URL:
    print("❌ Error: PROD_DATABASE_URL environment variable not set")
    sys.exit(1)

print("🔍 Running production migration checklist...")

# Check 1: Can connect to production database
try:
    print("\n1️⃣ Checking database connection...")
    conn = psycopg2.connect(PROD_DB_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    db_version = cursor.fetchone()
    print(f"✅ Successfully connected to database: {db_version[0]}")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ Failed to connect to database: {e}")
    sys.exit(1)

# Check 2: Alembic is installed and working
try:
    print("\n2️⃣ Checking Alembic installation...")
    result = subprocess.run(["alembic", "--version"], capture_output=True, text=True, check=True)
    print(f"✅ Alembic is installed: {result.stdout.strip()}")
except Exception as e:
    print(f"❌ Alembic check failed: {e}")
    sys.exit(1)

# Check 3: Alembic history is available
try:
    print("\n3️⃣ Checking Alembic history...")
    result = subprocess.run(["alembic", "history"], capture_output=True, text=True, check=True)
    if "No revisions" in result.stdout:
        print("❌ No Alembic revisions found")
        sys.exit(1)
    print(f"✅ Alembic history available with {result.stdout.count('->') + 1} revisions")
except Exception as e:
    print(f"❌ Alembic history check failed: {e}")
    sys.exit(1)

# Check 4: Create backup file name suggestion
print("\n4️⃣ Database backup recommendation:")
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
db_name = PROD_DB_URL.split("/")[-1].split("?")[0]
backup_filename = f"{db_name}_backup_{timestamp}.sql"
print(f"✅ Suggested backup command:")
print(f"   pg_dump -U <username> -d {db_name} > {backup_filename}")

# Check 5: Verify migration scripts exist
print("\n5️⃣ Checking migration scripts...")
required_scripts = [
    "apply_migrations_to_production.py",
    "fix_and_apply_migration.py",
    "create_merge_migration.py",
    "apply_safe_migrations.py"
]

for script in required_scripts:
    script_path = os.path.join("scripts", script)
    if os.path.exists(script_path):
        print(f"✅ Found {script_path}")
    else:
        print(f"❌ Missing {script_path}")

# Final checklist
print("\n📋 Final Checklist:")
print("  □ Have you tested these migrations in a staging environment?")
print("  □ Have you created a backup of the production database?")
print("  □ Is there a rollback plan if migrations fail?")
print("  □ Are all application servers ready for the new schema?")
print("  □ Is there a maintenance window scheduled for the migration?")

print("\n✨ If all checks pass and checklist items are complete, you can proceed with:")
print("   python scripts/apply_migrations_to_production.py")