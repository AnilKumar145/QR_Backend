import os
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create a merge migration
print("Creating a merge migration...")
subprocess.run(["alembic", "revision", "--autogenerate", "-m", "merge_migration_heads"], check=True)

print("\nMerge migration created successfully!")
print("Now edit the generated migration file to fix any issues before running 'alembic upgrade head'")