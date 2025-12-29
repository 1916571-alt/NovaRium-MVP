#!/usr/bin/env python3
"""
NovaRium Database Migration Script v1.0 → v2.0

This script migrates the database schema to support:
- User authentication (auth_users, oauth_accounts, sessions)
- Renamed tables (users → customers)
- New columns for multi-tenancy (created_by)

Usage:
    # Local DuckDB migration
    python scripts/migrate_v2.py --mode duckdb

    # Supabase PostgreSQL migration
    python scripts/migrate_v2.py --mode postgres

    # Dry run (show SQL without executing)
    python scripts/migrate_v2.py --mode postgres --dry-run

    # Fresh install (create all tables from scratch)
    python scripts/migrate_v2.py --mode duckdb --fresh
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Migration")


def migrate_duckdb(dry_run: bool = False, fresh: bool = False):
    """Migrate DuckDB databases."""
    import duckdb
    from src.data.db import WAREHOUSE_DB_PATH, EXPERIMENT_DB_PATH
    from src.data.schema import (
        AUTH_SCHEMA_DUCKDB,
        WAREHOUSE_SCHEMA_DUCKDB,
        EXPERIMENT_SCHEMA_DUCKDB,
        get_full_schema_duckdb
    )

    logger.info("=" * 60)
    logger.info("DuckDB Migration")
    logger.info("=" * 60)

    if fresh:
        logger.info("FRESH INSTALL MODE - Creating new tables")
        schema = get_full_schema_duckdb()
        if dry_run:
            print("\n### SQL to execute (FRESH) ###")
            print(schema)
            return

        # Apply to both DBs
        for db_name, db_path in [("Warehouse", WAREHOUSE_DB_PATH), ("Experiment", EXPERIMENT_DB_PATH)]:
            logger.info(f"Setting up {db_name} DB at {db_path}")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

            with duckdb.connect(db_path) as con:
                for stmt in schema.split(';'):
                    stmt = stmt.strip()
                    if stmt and not stmt.startswith('--'):
                        try:
                            con.execute(stmt)
                        except Exception as e:
                            logger.warning(f"Statement skipped: {e}")
            logger.info(f"{db_name} DB setup complete")
        return

    # Migration mode
    logger.info("MIGRATION MODE - Upgrading existing tables")

    # Step 1: Add auth tables to both DBs
    logger.info("\n[Phase 1] Adding auth tables...")

    for db_name, db_path in [("Warehouse", WAREHOUSE_DB_PATH), ("Experiment", EXPERIMENT_DB_PATH)]:
        logger.info(f"  → {db_name} DB")

        if dry_run:
            print(f"\n### Auth schema for {db_name} ###")
            print(AUTH_SCHEMA_DUCKDB)
            continue

        if not os.path.exists(db_path):
            logger.warning(f"  DB file not found: {db_path}")
            continue

        with duckdb.connect(db_path) as con:
            for stmt in AUTH_SCHEMA_DUCKDB.split(';'):
                stmt = stmt.strip()
                if stmt and not stmt.startswith('--'):
                    try:
                        con.execute(stmt)
                    except Exception as e:
                        if 'already exists' not in str(e).lower():
                            logger.warning(f"    {e}")

    # Step 2: Migrate users → customers in Warehouse DB
    logger.info("\n[Phase 2] Renaming users → customers...")

    if dry_run:
        print("\n### Warehouse migration ###")
        print("""
-- Create customers from users
CREATE TABLE IF NOT EXISTS customers AS
SELECT
    user_id AS customer_id,
    name, gender, age, job, segment, joined_at,
    NULL AS created_by,
    CURRENT_TIMESTAMP AS created_at
FROM users;

-- Update orders to use customer_id
ALTER TABLE orders RENAME COLUMN user_id TO customer_id;
ALTER TABLE orders ADD COLUMN created_by VARCHAR;
        """)
    else:
        if os.path.exists(WAREHOUSE_DB_PATH):
            with duckdb.connect(WAREHOUSE_DB_PATH) as con:
                # Check if users table exists
                tables = con.execute(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
                ).fetchall()
                table_names = [t[0] for t in tables]

                if 'users' in table_names and 'customers' not in table_names:
                    logger.info("  → Migrating users table to customers")
                    con.execute("""
                        CREATE TABLE customers AS
                        SELECT
                            user_id AS customer_id,
                            name, gender, age, job, segment, joined_at,
                            NULL AS created_by,
                            CURRENT_TIMESTAMP AS created_at
                        FROM users
                    """)
                    logger.info("  → customers table created")

                    # Update orders if needed
                    if 'orders' in table_names:
                        # Check columns
                        cols = con.execute(
                            "SELECT column_name FROM information_schema.columns WHERE table_name = 'orders'"
                        ).fetchall()
                        col_names = [c[0] for c in cols]

                        if 'user_id' in col_names and 'customer_id' not in col_names:
                            # DuckDB doesn't support RENAME COLUMN directly
                            logger.info("  → Rebuilding orders table with customer_id")
                            con.execute("""
                                CREATE TABLE orders_new AS
                                SELECT
                                    order_id,
                                    user_id AS customer_id,
                                    order_at,
                                    menu_item,
                                    amount,
                                    NULL AS created_by,
                                    CURRENT_TIMESTAMP AS created_at
                                FROM orders
                            """)
                            con.execute("DROP TABLE orders")
                            con.execute("ALTER TABLE orders_new RENAME TO orders")
                            logger.info("  → orders table updated")
                else:
                    logger.info("  → Migration not needed (customers table already exists or users missing)")
        else:
            logger.warning(f"  → Warehouse DB not found: {WAREHOUSE_DB_PATH}")

    # Step 3: Update experiment tables
    logger.info("\n[Phase 3] Updating experiment tables...")

    if dry_run:
        print("\n### Experiment table updates ###")
        print("""
-- Add new columns to experiments
ALTER TABLE experiments ADD COLUMN name VARCHAR(100);
ALTER TABLE experiments ADD COLUMN description VARCHAR;
ALTER TABLE experiments ADD COLUMN status VARCHAR(20) DEFAULT 'draft';
ALTER TABLE experiments ADD COLUMN created_by VARCHAR;
ALTER TABLE experiments ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Add columns to adoptions
ALTER TABLE adoptions ADD COLUMN winning_variant VARCHAR(10);
ALTER TABLE adoptions ADD COLUMN adopted_by VARCHAR;
ALTER TABLE adoptions ADD COLUMN notes VARCHAR;
        """)
    else:
        if os.path.exists(EXPERIMENT_DB_PATH):
            with duckdb.connect(EXPERIMENT_DB_PATH) as con:
                # Add columns to experiments (if they don't exist)
                new_cols = [
                    ('name', 'VARCHAR(100)'),
                    ('description', 'VARCHAR'),
                    ('status', "VARCHAR(20) DEFAULT 'draft'"),
                    ('created_by', 'VARCHAR'),
                    ('updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
                ]

                for col_name, col_type in new_cols:
                    try:
                        con.execute(f"ALTER TABLE experiments ADD COLUMN {col_name} {col_type}")
                        logger.info(f"  → Added experiments.{col_name}")
                    except Exception as e:
                        if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                            pass
                        else:
                            logger.warning(f"  → experiments.{col_name}: {e}")

                # Add columns to adoptions
                adoption_cols = [
                    ('winning_variant', 'VARCHAR(10)'),
                    ('adopted_by', 'VARCHAR'),
                    ('notes', 'VARCHAR')
                ]

                for col_name, col_type in adoption_cols:
                    try:
                        con.execute(f"ALTER TABLE adoptions ADD COLUMN {col_name} {col_type}")
                        logger.info(f"  → Added adoptions.{col_name}")
                    except Exception as e:
                        if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                            pass
                        else:
                            logger.warning(f"  → adoptions.{col_name}: {e}")
        else:
            logger.warning(f"  → Experiment DB not found: {EXPERIMENT_DB_PATH}")

    logger.info("\n" + "=" * 60)
    logger.info("DuckDB migration complete!")
    logger.info("=" * 60)


def migrate_postgres(dry_run: bool = False, fresh: bool = False):
    """Migrate PostgreSQL (Supabase) database."""
    from src.data.schema import (
        AUTH_SCHEMA_POSTGRES,
        WAREHOUSE_SCHEMA_POSTGRES,
        EXPERIMENT_SCHEMA_POSTGRES,
        get_full_schema_postgres,
        MIGRATION_V2_POSTGRES
    )

    logger.info("=" * 60)
    logger.info("PostgreSQL Migration")
    logger.info("=" * 60)

    # Check DATABASE_URL
    database_url = os.getenv('DATABASE_URL', '')
    if not database_url:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            database_url = os.getenv('DATABASE_URL', '')
        except ImportError:
            pass

    if not database_url:
        logger.error("DATABASE_URL environment variable not set!")
        logger.info("Set it in .env file or environment:")
        logger.info("  export DATABASE_URL='postgresql://user:pass@host:5432/db'")
        return

    if fresh:
        logger.info("FRESH INSTALL MODE")
        schema = get_full_schema_postgres()
        if dry_run:
            print("\n### SQL to execute (FRESH) ###")
            print(schema)
            return

        # Execute schema
        import psycopg2
        try:
            conn = psycopg2.connect(database_url)
            with conn.cursor() as cur:
                cur.execute(schema)
            conn.commit()
            conn.close()
            logger.info("Fresh schema applied successfully!")
        except Exception as e:
            logger.error(f"Error: {e}")
            return
    else:
        logger.info("MIGRATION MODE")
        if dry_run:
            print("\n### Migration SQL ###")
            print(MIGRATION_V2_POSTGRES)
            return

        # Execute migration
        import psycopg2
        try:
            conn = psycopg2.connect(database_url)
            with conn.cursor() as cur:
                cur.execute(MIGRATION_V2_POSTGRES)
            conn.commit()
            conn.close()
            logger.info("Migration applied successfully!")
        except Exception as e:
            logger.error(f"Error: {e}")
            return

    logger.info("\n" + "=" * 60)
    logger.info("PostgreSQL migration complete!")
    logger.info("=" * 60)


def verify_migration(mode: str):
    """Verify migration was successful."""
    logger.info("\n" + "=" * 60)
    logger.info("Verifying Migration")
    logger.info("=" * 60)

    if mode == 'duckdb':
        import duckdb
        from src.data.db import WAREHOUSE_DB_PATH, EXPERIMENT_DB_PATH

        expected_tables = {
            'Warehouse': ['auth_users', 'oauth_accounts', 'sessions', 'customers', 'orders'],
            'Experiment': ['auth_users', 'oauth_accounts', 'sessions', 'experiments', 'assignments', 'events', 'adoptions', 'active_experiment']
        }

        for db_name, db_path in [('Warehouse', WAREHOUSE_DB_PATH), ('Experiment', EXPERIMENT_DB_PATH)]:
            logger.info(f"\n{db_name} DB:")
            if not os.path.exists(db_path):
                logger.warning(f"  Not found: {db_path}")
                continue

            with duckdb.connect(db_path, read_only=True) as con:
                tables = con.execute(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
                ).fetchall()
                table_names = [t[0] for t in tables]

                for expected in expected_tables[db_name]:
                    if expected in table_names:
                        count = con.execute(f"SELECT COUNT(*) FROM {expected}").fetchone()[0]
                        logger.info(f"  ✓ {expected}: {count} rows")
                    else:
                        logger.warning(f"  ✗ {expected}: MISSING")

    elif mode == 'postgres':
        database_url = os.getenv('DATABASE_URL', '')
        if not database_url:
            logger.error("DATABASE_URL not set")
            return

        import psycopg2
        expected_tables = ['auth_users', 'oauth_accounts', 'sessions', 'customers', 'orders',
                          'experiments', 'assignments', 'events', 'adoptions', 'active_experiment']

        try:
            conn = psycopg2.connect(database_url)
            with conn.cursor() as cur:
                for table in expected_tables:
                    try:
                        cur.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cur.fetchone()[0]
                        logger.info(f"  ✓ {table}: {count} rows")
                    except Exception as e:
                        logger.warning(f"  ✗ {table}: {e}")
            conn.close()
        except Exception as e:
            logger.error(f"Connection error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="NovaRium Database Migration v1.0 → v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Migrate local DuckDB
    python scripts/migrate_v2.py --mode duckdb

    # Migrate Supabase PostgreSQL
    python scripts/migrate_v2.py --mode postgres

    # Preview migration SQL without executing
    python scripts/migrate_v2.py --mode postgres --dry-run

    # Fresh install (new database)
    python scripts/migrate_v2.py --mode duckdb --fresh

    # Verify migration
    python scripts/migrate_v2.py --mode duckdb --verify
        """
    )

    parser.add_argument(
        '--mode',
        choices=['duckdb', 'postgres'],
        default='duckdb',
        help='Database mode (default: duckdb)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show SQL without executing'
    )
    parser.add_argument(
        '--fresh',
        action='store_true',
        help='Fresh install (create all tables from scratch)'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify migration was successful'
    )

    args = parser.parse_args()

    # Header
    print("""
================================================================
        NovaRium Database Migration Tool v2.0

  Upgrading schema for authentication and multi-tenancy
================================================================
    """)

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"Started at: {timestamp}")
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info(f"Fresh install: {args.fresh}")

    if args.verify:
        verify_migration(args.mode)
        return

    if args.mode == 'duckdb':
        migrate_duckdb(dry_run=args.dry_run, fresh=args.fresh)
    else:
        migrate_postgres(dry_run=args.dry_run, fresh=args.fresh)

    if not args.dry_run:
        verify_migration(args.mode)


if __name__ == "__main__":
    main()
