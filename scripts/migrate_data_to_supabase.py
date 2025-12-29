#!/usr/bin/env python3
"""
DuckDB to Supabase Data Migration Script

Migrates customers and orders data from local DuckDB to Supabase PostgreSQL.
"""

import os
import sys
import logging
from datetime import datetime

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DataMigration")


def migrate_data():
    """Migrate data from DuckDB to Supabase."""
    import duckdb
    import psycopg2
    from psycopg2.extras import execute_values
    from dotenv import load_dotenv

    load_dotenv()

    # Paths
    warehouse_db = os.path.join(PROJECT_ROOT, 'data', 'db', 'novarium_warehouse.db')
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        logger.error("DATABASE_URL not set!")
        return False

    print("=" * 60)
    print("DuckDB to Supabase Data Migration")
    print("=" * 60)

    # Step 1: Extract from DuckDB
    logger.info("\n[Phase 1] Extracting data from DuckDB...")

    with duckdb.connect(warehouse_db, read_only=True) as duck:
        # Extract customers
        customers_df = duck.execute("SELECT * FROM customers").df()
        logger.info(f"  Extracted {len(customers_df)} customers")

        # Extract orders
        orders_df = duck.execute("SELECT * FROM orders").df()
        logger.info(f"  Extracted {len(orders_df)} orders")

    # Step 2: Transform data
    logger.info("\n[Phase 2] Transforming data...")

    # Ensure correct column types for PostgreSQL
    customers_data = []
    for _, row in customers_df.iterrows():
        customers_data.append((
            str(row['customer_id']),
            row['name'],
            row.get('gender'),
            int(row['age']) if row.get('age') else None,
            row.get('job'),
            row.get('segment'),
            row['joined_at'],
            None,  # created_by
        ))

    orders_data = []
    for _, row in orders_df.iterrows():
        orders_data.append((
            str(row['order_id']),
            str(row['customer_id']),
            row['order_at'],
            row['menu_item'],
            float(row['amount']),
            None,  # created_by
        ))

    logger.info(f"  Prepared {len(customers_data)} customers for insert")
    logger.info(f"  Prepared {len(orders_data)} orders for insert")

    # Step 3: Load into Supabase
    logger.info("\n[Phase 3] Loading data into Supabase...")

    try:
        conn = psycopg2.connect(database_url)

        with conn.cursor() as cur:
            # Clear existing data (if any)
            logger.info("  Clearing existing data...")
            cur.execute("DELETE FROM orders")
            cur.execute("DELETE FROM customers")

            # Insert customers
            logger.info("  Inserting customers...")
            customers_sql = """
                INSERT INTO customers (customer_id, name, gender, age, job, segment, joined_at, created_by)
                VALUES %s
                ON CONFLICT (customer_id) DO NOTHING
            """
            execute_values(cur, customers_sql, customers_data, page_size=500)
            logger.info(f"  Inserted {len(customers_data)} customers")

            # Insert orders
            logger.info("  Inserting orders...")
            orders_sql = """
                INSERT INTO orders (order_id, customer_id, order_at, menu_item, amount, created_by)
                VALUES %s
                ON CONFLICT (order_id) DO NOTHING
            """
            execute_values(cur, orders_sql, orders_data, page_size=500)
            logger.info(f"  Inserted {len(orders_data)} orders")

        conn.commit()
        conn.close()

    except Exception as e:
        logger.error(f"Load failed: {e}")
        return False

    # Step 4: Verify
    logger.info("\n[Phase 4] Verifying migration...")

    try:
        conn = psycopg2.connect(database_url)
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM customers")
            pg_customers = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM orders")
            pg_orders = cur.fetchone()[0]
        conn.close()

        print("\n" + "=" * 60)
        print("MIGRATION VERIFICATION")
        print("=" * 60)
        print(f"\n  Source (DuckDB):")
        print(f"    - customers: {len(customers_df)} rows")
        print(f"    - orders: {len(orders_df)} rows")
        print(f"\n  Target (Supabase):")
        print(f"    - customers: {pg_customers} rows")
        print(f"    - orders: {pg_orders} rows")

        if pg_customers == len(customers_df) and pg_orders == len(orders_df):
            print(f"\n  STATUS: SUCCESS - All data migrated!")
            return True
        else:
            print(f"\n  STATUS: PARTIAL - Some data missing")
            return False

    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False


if __name__ == "__main__":
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    success = migrate_data()
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sys.exit(0 if success else 1)
