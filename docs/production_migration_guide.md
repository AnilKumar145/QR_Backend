# Production Database Migration Guide

## Overview
This guide outlines the process for safely applying database migrations to the production environment.

## Prerequisites
- Production database credentials in `.env` file as `PROD_DATABASE_URL`
- Alembic migration environment properly set up
- All migrations tested in development/staging environment

## Migration Process

### 1. Backup Production Database
Always create a backup before applying migrations:

```bash
# For PostgreSQL
pg_dump -U username -d database_name > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 2. Check Current Migration Status
```bash
python scripts/apply_migrations_to_production.py
```
This will show the current migration version without applying changes.

### 3. Review Pending Migrations
Review all pending migrations that will be applied:
```bash
alembic -c alembic_prod.ini history
```

### 4. Test Migrations in Staging
Before applying to production, test all migrations in a staging environment with a copy of production data.

### 5. Apply Migrations
After confirming everything is ready:
```bash
python scripts/apply_migrations_to_production.py
```
When prompted, enter 'y' to apply the migrations.

### 6. Verify Migration Success
- Check that the application works correctly with the new schema
- Verify that all tables and columns were created as expected
- Check that existing data is intact

### 7. Rollback Plan
If issues occur, restore from the backup created in step 1.

## Handling Special Cases

### Adding New Tables
New tables are generally safe to add and can be applied directly.

### Schema Changes to Existing Tables
For changes to existing tables:
1. Create a migration that adds new columns (nullable or with defaults)
2. Deploy application code that can work with both old and new schema
3. Apply migration
4. Deploy application code that uses new schema
5. Later, create a migration to clean up old columns if needed

### Fixing Migration Issues
If you encounter issues with migration history:
```bash
python scripts/fix_and_apply_migration.py
```

### Merging Multiple Migration Heads
If you have multiple migration heads:
```bash
python scripts/create_merge_migration.py
python scripts/apply_safe_migrations.py
```