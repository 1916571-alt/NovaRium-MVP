import duckdb
import os
import requests
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DB")

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Constants
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(_BASE_DIR, 'data')

# DB Split: Warehouse (persistent) vs Experiment (volatile)
WAREHOUSE_DB_PATH = os.path.join(DATA_DIR, 'db', 'novarium_warehouse.db')  # users, orders, 30-day history
EXPERIMENT_DB_PATH = os.path.join(DATA_DIR, 'db', 'novarium_experiment.db')  # assignments, events, experiments, adoptions, active_experiment

# Legacy alias (for gradual migration)
DB_PATH = EXPERIMENT_DB_PATH

RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')

# Cloud deployment configuration - prioritize Streamlit secrets
def _get_secret(key: str, default: str = '') -> str:
    """Get config from Streamlit secrets first, then env vars."""
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)

DB_MODE = _get_secret('DB_MODE', 'duckdb')  # 'duckdb' for local, 'supabase' for cloud
DATABASE_URL = _get_secret('DATABASE_URL', '')  # PostgreSQL connection string
TARGET_APP_URL = _get_secret('TARGET_APP_URL', 'http://localhost:8000')

# =========================================================
# PostgreSQL Support (Supabase Cloud)
# =========================================================

_pg_pool = None

def get_pg_pool():
    """Get or create PostgreSQL connection pool for Supabase."""
    global _pg_pool
    if _pg_pool is None and DATABASE_URL:
        try:
            import psycopg2
            from psycopg2 import pool
            _pg_pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=DATABASE_URL
            )
            logger.info("PostgreSQL connection pool created")
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL pool: {e}")
    return _pg_pool

def get_pg_connection():
    """Get a connection from the PostgreSQL pool."""
    from contextlib import contextmanager

    @contextmanager
    def _get_conn():
        pool = get_pg_pool()
        conn = None
        try:
            conn = pool.getconn()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn and pool:
                pool.putconn(conn)

    return _get_conn()

def is_cloud_mode():
    """Check if running in cloud mode (Supabase)."""
    return DB_MODE == 'supabase' and bool(DATABASE_URL)

# =========================================================
# DB Write Utilities with Target App Coordination
# =========================================================

def safe_write_execute(sql: str, params: list = None, use_coordination: bool = True):
    """
    Execute write SQL with optional Target App DB coordination.

    Args:
        sql: SQL statement to execute
        params: Parameters for SQL statement
        use_coordination: If True, coordinate with Target App (release/reconnect)
                         If False, attempt direct write (legacy mode)

    Returns:
        dict with status and message
    """
    if use_coordination:
        return _coordinated_write(sql, params)
    else:
        return _direct_write(sql, params)

def _coordinated_write(sql: str, params: list = None):
    """Write with Target App coordination (recommended)."""
    try:
        # Step 1: Request Target App to release DB
        try:
            resp = requests.post(f"{TARGET_APP_URL}/admin/db_release", timeout=5)
            if resp.status_code != 200:
                return {"status": "warning", "message": "Target App DB release failed, attempting anyway"}
        except requests.exceptions.ConnectionError:
            pass  # Target App not running, proceed directly

        time.sleep(0.3)  # Wait for connection to fully close

        # Step 2: Execute write
        try:
            with duckdb.connect(DB_PATH) as con:
                if params:
                    con.execute(sql, params)
                else:
                    con.execute(sql)
            result = {"status": "success", "message": "Write completed"}
        except Exception as e:
            result = {"status": "error", "message": str(e)}

        # Step 3: Reconnect Target App (always attempt)
        try:
            requests.post(f"{TARGET_APP_URL}/admin/db_reconnect", timeout=5)
        except:
            pass

        return result

    except Exception as e:
        return {"status": "error", "message": str(e)}

def _direct_write(sql: str, params: list = None):
    """Direct write without coordination (legacy mode)."""
    try:
        with duckdb.connect(DB_PATH) as con:
            if params:
                con.execute(sql, params)
            else:
                con.execute(sql)
        return {"status": "success", "message": "Direct write completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def safe_write_batch(operations: list, use_coordination: bool = True):
    """
    Execute multiple write operations in a single coordinated session.
    Supports both DuckDB (local) and PostgreSQL (Supabase cloud).

    Args:
        operations: List of (sql, params) tuples
        use_coordination: If True, coordinate with Target App (DuckDB only)

    Returns:
        dict with status and results
    """
    # Cloud mode: Use PostgreSQL
    if is_cloud_mode():
        return _pg_batch_write(operations)

    # Local mode: Use DuckDB with optional coordination
    if use_coordination:
        try:
            # Step 1: Request Target App to release DB
            try:
                resp = requests.post(f"{TARGET_APP_URL}/admin/db_release", timeout=5)
            except requests.exceptions.ConnectionError:
                pass

            time.sleep(0.3)

            # Step 2: Execute all operations
            results = []
            try:
                with duckdb.connect(DB_PATH) as con:
                    for sql, params in operations:
                        try:
                            if params:
                                con.execute(sql, params)
                            else:
                                con.execute(sql)
                            results.append({"sql": sql[:50], "status": "success"})
                        except Exception as e:
                            results.append({"sql": sql[:50], "status": "error", "message": str(e)})
            except Exception as e:
                return {"status": "error", "message": str(e), "results": results}

            # Step 3: Reconnect Target App
            try:
                requests.post(f"{TARGET_APP_URL}/admin/db_reconnect", timeout=5)
            except:
                pass

            return {"status": "success", "results": results}

        except Exception as e:
            return {"status": "error", "message": str(e)}
    else:
        # Direct mode
        results = []
        try:
            with duckdb.connect(DB_PATH) as con:
                for sql, params in operations:
                    try:
                        if params:
                            con.execute(sql, params)
                        else:
                            con.execute(sql)
                        results.append({"sql": sql[:50], "status": "success"})
                    except Exception as e:
                        results.append({"sql": sql[:50], "status": "error", "message": str(e)})
            return {"status": "success", "results": results}
        except Exception as e:
            return {"status": "error", "message": str(e), "results": results}

def _pg_batch_write(operations: list):
    """Execute batch write on PostgreSQL (Supabase)."""
    import re
    results = []
    has_error = False
    try:
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                for sql, params in operations:
                    try:
                        # Skip DuckDB-specific SQL that PostgreSQL doesn't support
                        sql_lower = sql.lower().strip()
                        if 'create sequence' in sql_lower and 'nextval' not in sql_lower:
                            # Skip DuckDB sequence creation - PostgreSQL uses SERIAL
                            results.append({"sql": sql[:50], "status": "skipped", "message": "DuckDB-specific"})
                            continue

                        # Convert DuckDB-style table creation to PostgreSQL
                        pg_sql = sql
                        if 'create table' in sql_lower and 'nextval' in sql_lower:
                            # Replace DuckDB's nextval with PostgreSQL SERIAL PRIMARY KEY
                            pg_sql = re.sub(
                                r'(\w+)\s+INTEGER\s+DEFAULT\s+nextval\([\'"][^\'"]+[\'"]\)',
                                r'\1 SERIAL PRIMARY KEY',
                                sql,
                                flags=re.IGNORECASE
                            )

                        # Convert DuckDB-style placeholders to PostgreSQL
                        pg_sql = pg_sql.replace('?', '%s')

                        logger.info(f"PG Executing: {pg_sql[:100]}...")
                        if params:
                            cur.execute(pg_sql, tuple(params))
                        else:
                            cur.execute(pg_sql)
                        results.append({"sql": sql[:50], "status": "success"})
                    except Exception as e:
                        has_error = True
                        logger.error(f"PG Batch Error: {e} | SQL: {sql[:100]}")
                        results.append({"sql": sql[:50], "status": "error", "message": str(e)})

        # Return error status if any operation failed
        if has_error:
            return {"status": "partial_error", "message": "Some operations failed", "results": results}
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"PG Batch Connection Error: {e}")
        return {"status": "error", "message": str(e), "results": results}

# =========================================================
# DB Initialization Functions (Split Architecture)
# =========================================================

def initialize_warehouse_db():
    """Initialize Warehouse DB (persistent data: users, orders, history)."""
    print(f"Connecting to Warehouse DB at {WAREHOUSE_DB_PATH}...")
    con = duckdb.connect(WAREHOUSE_DB_PATH)
    return con

def initialize_experiment_db():
    """Initialize Experiment DB (volatile data: assignments, events, experiments)."""
    print(f"Connecting to Experiment DB at {EXPERIMENT_DB_PATH}...")
    con = duckdb.connect(EXPERIMENT_DB_PATH)
    return con

def initialize_db():
    """Legacy function - returns experiment DB for backward compatibility."""
    return initialize_experiment_db()

def setup_warehouse_schema(con):
    """Setup warehouse schema (users, orders from CSV)."""
    print("=== Setting up Warehouse DB ===")

    # Load CSVs (persistent data)
    tables = ['users', 'orders']
    for table_name in tables:
        csv_path = os.path.join(RAW_DATA_DIR, f'{table_name}.csv')
        if os.path.exists(csv_path):
            print(f"Loading {table_name} from {csv_path}...")
            con.execute(f"DROP TABLE IF EXISTS {table_name}")
            con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM read_csv_auto('{csv_path}')")
        else:
            print(f"Warning: {csv_path} not found.")

    print("Warehouse schema setup complete.")

def setup_experiment_schema(con, reset=False):
    """
    Setup experiment schema (assignments, events, experiments).

    Args:
        con: DuckDB connection
        reset: If True, DROP and recreate tables (deletes all data).
               If False (default), only CREATE IF NOT EXISTS (preserves data).
    """
    print("=== Setting up Experiment DB ===")

    if reset:
        print("⚠️  RESET MODE: All experiment data will be deleted!")

    # Assignments table
    print("Creating 'assignments' table...")
    if reset:
        con.execute("DROP TABLE IF EXISTS assignments")
    con.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            user_id VARCHAR,
            experiment_id VARCHAR,
            variant VARCHAR,
            assigned_at TIMESTAMP,
            run_id VARCHAR,
            weight FLOAT DEFAULT 1.0
        )
    """)

    # Events table
    print("Creating 'events' table...")
    if reset:
        con.execute("DROP TABLE IF EXISTS events")
    con.execute("""
        CREATE TABLE IF NOT EXISTS events (
            event_id VARCHAR,
            user_id VARCHAR,
            event_name VARCHAR,
            timestamp TIMESTAMP,
            value DOUBLE,
            run_id VARCHAR
        )
    """)

    # Experiments table (Retrospective)
    print("Creating 'experiments' table...")
    if reset:
        con.execute("DROP TABLE IF EXISTS experiments")
    con.execute("CREATE SEQUENCE IF NOT EXISTS exp_id_seq START 1")
    con.execute("""
        CREATE TABLE IF NOT EXISTS experiments (
            exp_id INTEGER DEFAULT nextval('exp_id_seq'),
            target VARCHAR,
            hypothesis VARCHAR,
            primary_metric VARCHAR,
            guardrails VARCHAR,
            sample_size INTEGER,
            start_date DATE,
            end_date DATE,
            traffic_split FLOAT,
            p_value FLOAT,
            decision VARCHAR,
            learning_note VARCHAR,
            run_id VARCHAR,
            control_rate FLOAT,
            test_rate FLOAT,
            lift FLOAT,
            guardrail_results VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Adoptions table
    print("Creating 'adoptions' table...")
    if reset:
        con.execute("DROP TABLE IF EXISTS adoptions")
    con.execute("""
        CREATE TABLE IF NOT EXISTS adoptions (
            adoption_id INTEGER PRIMARY KEY,
            experiment_id VARCHAR,
            variant_config VARCHAR,
            adopted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Active Experiment table
    print("Creating 'active_experiment' table...")
    if reset:
        con.execute("DROP TABLE IF EXISTS active_experiment")
    con.execute("""
        CREATE TABLE IF NOT EXISTS active_experiment (
            id INTEGER PRIMARY KEY,
            is_active BOOLEAN,
            started_at TIMESTAMP
        )
    """)

    print("Experiment schema setup complete.")

def load_data(con):
    """Legacy function - setup experiment schema only."""
    setup_experiment_schema(con)

def verify_warehouse(con):
    """Verify warehouse DB tables."""
    print("\nVerifying Warehouse DB...")
    tables = ['users', 'orders']
    for table_name in tables:
        try:
            result = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
            print(f"  {table_name}: {result[0]} rows")
        except Exception as e:
            print(f"  {table_name}: MISSING ({e})")

def verify_experiment(con):
    """Verify experiment DB tables."""
    print("\nVerifying Experiment DB...")
    tables = ['assignments', 'events', 'experiments', 'adoptions', 'active_experiment']
    for table_name in tables:
        try:
            result = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
            print(f"  {table_name}: {result[0]} rows")
        except Exception as e:
            print(f"  {table_name}: MISSING ({e})")

def verify_data(con):
    """Legacy function - verify experiment tables."""
    verify_experiment(con)

def setup_all():
    """Initialize both DBs with proper schema."""
    print("=" * 50)
    print("NovaRium DB Setup (Split Architecture)")
    print("=" * 50)

    # Warehouse DB
    wh_con = initialize_warehouse_db()
    setup_warehouse_schema(wh_con)
    verify_warehouse(wh_con)
    wh_con.close()

    # Experiment DB
    exp_con = initialize_experiment_db()
    setup_experiment_schema(exp_con)
    verify_experiment(exp_con)
    exp_con.close()

    print("\n" + "=" * 50)
    print("Setup Complete!")
    print(f"  Warehouse DB: {WAREHOUSE_DB_PATH}")
    print(f"  Experiment DB: {EXPERIMENT_DB_PATH}")
    print("=" * 50)

if __name__ == "__main__":
    setup_all()
