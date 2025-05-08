import os
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create a manual migration for adding institutions and venues tables
print("Creating manual migration for adding institutions and venues tables...")
subprocess.run(["alembic", "revision", "-m", "add_institutions_and_venues_manual"], check=True)

print("\nMigration template created successfully!")
print("Now edit the generated migration file to add the tables manually")
print("Then run: python scripts/apply_local_migration.py")