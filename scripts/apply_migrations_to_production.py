import os
import sys
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the production database URL
PROD_DB_URL = os.getenv("PROD_DATABASE_URL")

if not PROD_DB_URL:
    print("Error: PROD_DATABASE_URL environment variable not set")
    sys.exit(1)

# Create a temporary alembic.ini with the production database URL
with open("alembic.ini", "r") as f:
    alembic_config = f.read()

# Replace the sqlalchemy.url line
alembic_config = alembic_config.replace(
    "sqlalchemy.url = ", 
    f"sqlalchemy.url = {PROD_DB_URL}"
)

# Write to a temporary file
with open("alembic_prod.ini", "w") as f:
    f.write(alembic_config)

try:
    # Run alembic commands with the temporary config
    print("Checking current revision...")
    subprocess.run(["alembic", "-c", "alembic_prod.ini", "current"], check=True)
    
    print("\nShowing migration history...")
    subprocess.run(["alembic", "-c", "alembic_prod.ini", "history"], check=True)
    
    # Ask for confirmation before upgrading
    confirm = input("\nDo you want to apply migrations to the production database? (y/n): ")
    if confirm.lower() == 'y':
        print("\nApplying migrations...")
        subprocess.run(["alembic", "-c", "alembic_prod.ini", "upgrade", "head"], check=True)
        print("\nMigrations applied successfully!")
    else:
        print("\nMigration cancelled.")
finally:
    # Clean up the temporary file
    if os.path.exists("alembic_prod.ini"):
        os.remove("alembic_prod.ini")