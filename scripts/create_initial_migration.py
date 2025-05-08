#!/usr/bin/env python
"""
Create Initial Migration Script
This script creates an initial migration based on the actual production schema.
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the production database URL
PROD_DB_URL = os.getenv("PROD_DATABASE_URL")

if not PROD_DB_URL:
    print("Error: PROD_DATABASE_URL environment variable not set")
    sys.exit(1)

print("Analyzing production database schema...")

try:
    # Connect to the database
    conn = psycopg2.connect(PROD_DB_URL)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        AND table_name NOT IN ('pg_stat_statements', 'pg_stat_statements_info', 'alembic_version')
    """)
    
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\nFound {len(tables)} tables in production database:")
    for table in tables:
        print(f"  - {table}")
    
    # Get columns for each table
    table_columns = {}
    for table in tables:
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable, 
                   column_default, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = '{table}'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        table_columns[table] = columns
    
    # Get foreign keys
    cursor.execute("""
        SELECT
            tc.table_name, 
            kcu.column_name, 
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name 
        FROM 
            information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu 
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY';
    """)
    
    foreign_keys = cursor.fetchall()
    
    # Check if venue_id column exists in qr_sessions
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_name = 'qr_sessions' AND column_name = 'venue_id'
        )
    """)
    venue_id_exists = cursor.fetchone()[0]
    
    # Close cursor and connection
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error connecting to database: {e}")
    sys.exit(1)

# Create alembic/versions directory if it doesn't exist
if not os.path.exists("alembic/versions"):
    os.makedirs("alembic/versions")

# Create a clean initial migration file
initial_migration_path = "alembic/versions/initial_schema.py"
with open(initial_migration_path, "w", encoding="utf-8") as f:
    f.write("""\"\"\"Initial schema

Revision ID: initial_schema
Revises: 
Create Date: 2023-01-01 00:00:00.000000

\"\"\"

# revision identifiers, used by Alembic.
revision = 'initial_schema'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    \"\"\"Create initial schema based on production database.\"\"\"
""")
    
    # Add create table statements
    for table in tables:
        f.write(f"    # Create {table} table\n")
        f.write(f"    op.create_table('{table}',\n")
        
        for col_name, data_type, is_nullable, default, max_length in table_columns[table]:
            # Skip id columns as they're usually auto-generated
            if col_name == 'id' and default and 'nextval' in default:
                f.write(f"        sa.Column('{col_name}', sa.Integer(), nullable=False, primary_key=True),\n")
                continue
                
            # Map PostgreSQL types to SQLAlchemy types
            sa_type = "sa.String()"
            if data_type == "integer":
                sa_type = "sa.Integer()"
            elif data_type == "boolean":
                sa_type = "sa.Boolean()"
            elif data_type == "timestamp with time zone":
                sa_type = "sa.DateTime(timezone=True)"
            elif data_type == "double precision":
                sa_type = "sa.Float()"
            elif data_type == "text":
                sa_type = "sa.Text()"
            elif data_type == "bytea":
                sa_type = "sa.LargeBinary()"
            elif data_type == "character varying":
                if max_length:
                    sa_type = f"sa.String({max_length})"
                else:
                    sa_type = "sa.String()"
            
            f.write(f"        sa.Column('{col_name}', {sa_type}, nullable={'True' if is_nullable == 'YES' else 'False'}),\n")
        
        # Add primary key for id column
        f.write("        sa.PrimaryKeyConstraint('id')\n")
        f.write("    )\n\n")
    
    # Add foreign key constraints
    for table, column, foreign_table, foreign_column in foreign_keys:
        constraint_name = f"fk_{table}_{column}_to_{foreign_table}"
        f.write(f"    # Add foreign key from {table}.{column} to {foreign_table}.{foreign_column}\n")
        f.write(f"    op.create_foreign_key('{constraint_name}', '{table}', '{foreign_table}', ['{column}'], ['{foreign_column}'])\n\n")
    
    # Add institutions and venues tables if they don't exist
    f.write("""    # Create institutions table (missing in production)
    op.create_table('institutions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create venues table (missing in production)
    op.create_table('venues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('institution_id', sa.Integer(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('geofence_radius', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
""")

    # Add venue_id to qr_sessions if it doesn't exist
    if not venue_id_exists:
        f.write("""
    # Add venue_id to qr_sessions
    op.add_column('qr_sessions', sa.Column('venue_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_qr_sessions_venue_id', 'qr_sessions', 'venues', ['venue_id'], ['id'])
""")

    # Add downgrade function
    f.write("""
def downgrade() -> None:
    \"\"\"Downgrade schema.\"\"\"
""")
    
    # Add drop statements for venue_id if it was added
    if not venue_id_exists:
        f.write("""    # Drop venue_id from qr_sessions
    op.drop_constraint('fk_qr_sessions_venue_id', 'qr_sessions', type_='foreignkey')
    op.drop_column('qr_sessions', 'venue_id')
""")
    
    # Drop venues and institutions tables
    f.write("""    # Drop venues table
    op.drop_table('venues')
    
    # Drop institutions table
    op.drop_table('institutions')
""")
    
    # Drop foreign keys
    for table, column, foreign_table, foreign_column in reversed(foreign_keys):
        constraint_name = f"fk_{table}_{column}_to_{foreign_table}"
        f.write(f"    op.drop_constraint('{constraint_name}', '{table}', type_='foreignkey')\n")
    
    # Drop tables in reverse order
    for table in reversed(tables):
        f.write(f"    op.drop_table('{table}')\n")

print(f"Created initial migration: {initial_migration_path}")

# Create a script to update alembic_version in production
update_script_path = "scripts/update_alembic_version.py"
with open(update_script_path, "w", encoding="utf-8") as f:
    f.write("""#!/usr/bin/env python
\"\"\"
Update Alembic Version Script
This script updates the alembic_version table in production.
\"\"\"

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the production database URL
PROD_DB_URL = os.getenv("PROD_DATABASE_URL")

if not PROD_DB_URL:
    print("Error: PROD_DATABASE_URL environment variable not set")
    sys.exit(1)

print("Updating alembic_version in production...")

try:
    # Connect to the database
    conn = psycopg2.connect(PROD_DB_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Update alembic_version
    cursor.execute("DELETE FROM alembic_version")
    cursor.execute("INSERT INTO alembic_version (version_num) VALUES ('initial_schema')")
    
    print("Successfully updated alembic_version to 'initial_schema'")
    
    # Close cursor and connection
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error updating alembic_version: {e}")
    sys.exit(1)

print("\\nAlembic version updated")
print("Now you can create new migrations from this clean state.")
""")

print(f"Created update script: {update_script_path}")

print("\nInitial migration created!")
print("Next steps:")
print("1. Review the generated migration file")
print("2. Run: python scripts/update_alembic_version.py")
print("3. Then you can create new migrations with: alembic revision --autogenerate -m \"add_new_feature\"")