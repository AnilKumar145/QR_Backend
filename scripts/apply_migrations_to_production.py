#!/usr/bin/env python
"""
Apply Migrations to Production Script
This script applies Alembic migrations to the production database.
"""

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

# Create a temporary alembic.ini file for production
with open("alembic_prod.ini", "w") as f:
    f.write(f"""# A generic, single database configuration.

[alembic]
# path to migration scripts
script_location = alembic

# template used to generate migration files
# file_template = %%(rev)s_%%(slug)s

# timezone to use when rendering the date
# within the migration file as well as the filename.
# string value is passed to dateutil.tz.gettz()
# leave blank for localtime
# timezone =

# max length of characters to apply to the
# "slug" field
# truncate_slug_length = 40

# set to 'true' to run the environment during
# the 'revision' command, regardless of autogenerate
# revision_environment = false

# set to 'true' to allow .pyc and .pyo files without
# a source .py file to be detected as revisions in the
# versions/ directory
# sourceless = false

# version location specification; this defaults
# to alembic/versions.  When using multiple version
# directories, initial revisions must be specified with --version-path
# version_locations = %(here)s/bar %(here)s/bat alembic/versions

# the output encoding used when revision files
# are written from script.py.mako
# output_encoding = utf-8

sqlalchemy.url = {PROD_DB_URL}


[post_write_hooks]
# post_write_hooks defines scripts or Python functions that are run
# on newly generated revision scripts.  See the documentation for further
# detail and examples

# format using "black" - use the console_scripts runner, against the "black" entrypoint
# hooks=black
# black.type=console_scripts
# black.entrypoint=black
# black.options=-l 79

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
""")

print("Checking current revision...")
try:
    subprocess.run(["alembic", "-c", "alembic_prod.ini", "current"], check=True)
    
    print("\nShowing migration history...")
    subprocess.run(["alembic", "-c", "alembic_prod.ini", "history"], check=True)
    
    # Ask for confirmation before upgrading
    confirm = input("\nDo you want to apply migrations to production? (y/n): ")
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