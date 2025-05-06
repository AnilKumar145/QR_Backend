import os
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Apply the merge migration
print("Applying the merge migration...")
try:
    subprocess.run(["alembic", "upgrade", "merge_migration_heads"], check=True)
    print("Merge migration applied successfully!")
except subprocess.CalledProcessError:
    print("Error applying merge migration. It might already be applied.")

# Apply the safe details column migration
print("\nApplying the safe details column migration...")
try:
    subprocess.run(["alembic", "upgrade", "add_details_column_safe"], check=True)
    print("Safe details column migration applied successfully!")
except subprocess.CalledProcessError:
    print("Error applying safe details column migration.")

print("\nMigration process completed!")