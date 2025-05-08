import os
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create a migration for adding institutions and venues tables
print("Creating migration for adding institutions and venues tables...")
subprocess.run(["alembic", "revision", "--autogenerate", "-m", "add_institutions_and_venues"], check=True)

print("\nMigration created successfully!")
print("Now review the generated migration file before applying it")
print("Then run: python scripts/apply_local_migration.py")