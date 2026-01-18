"""
Supabase (PostgreSQL) Database Module for Cloud Deployment.

This module provides PostgreSQL connectivity via Supabase for cloud environments
where DuckDB file-based storage would be lost on server restarts.

Usage:
    - Set environment variables: SUPABASE_URL, SUPABASE_KEY, DATABASE_URL
    - Or use .env file with python-dotenv
"""
import os
import logging
import time
from typing import Optional, List, Tuple, Dict, Any
from contextlib import contextmanager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SupabaseDB")

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use system env vars

# =========================================================
# Configuration Helper: Streamlit Secrets Priority
# =========================================================

def _get_env(key: str, default: str = '') -> str:
    """
    Get environment variable with Streamlit secrets priority.
    1. Check st.secrets first (Streamlit Cloud)
    2. Fall back to os.getenv (local/Render)
    """
    # Try Streamlit secrets first
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass  # Not in Streamlit context or secrets not available

    return os.getenv(key, default)

# =========================================================
# Configuration
# =========================================================

# Database mode: 'supabase' for cloud, 'duckdb' for local
DB_MODE = _get_env('DB_MODE', 'duckdb')

# Supabase connection string (PostgreSQL)
_raw_database_url = _get_env('DATABASE_URL', '')

# Ensure SSL mode is set for cloud PostgreSQL connections
def _ensure_ssl(url: str) -> str:
    """Add sslmode=require if not present in DATABASE_URL."""
    if not url:
        return url
    if 'sslmode=' not in url:
        separator = '&' if '?' in url else '?'
        return f"{url}{separator}sslmode=require"
    return url

DATABASE_URL = _ensure_ssl(_raw_database_url)
SUPABASE_URL = _get_env('SUPABASE_URL', '')
SUPABASE_KEY = _get_env('SUPABASE_KEY', '')

# Log configuration on import (for debugging)
logger.info(f"DB_MODE: {DB_MODE}")
logger.info(f"DATABASE_URL set: {bool(DATABASE_URL)}")
if DATABASE_URL:
    # Log masked URL for debugging (hide password)
    import re
    masked_url = re.sub(r':([^:@]+)@', ':****@', DATABASE_URL)
    logger.info(f"DATABASE_URL (masked): {masked_url}")

# For backward compatibility with local development
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(_BASE_DIR, 'data')
EXPERIMENT_DB_PATH = os.path.join(DATA_DIR, 'db', 'novarium_experiment.db')
WAREHOUSE_DB_PATH = os.path.join(DATA_DIR, 'db', 'novarium_warehouse.db')

# =========================================================
# PostgreSQL Connection Pool (Supabase) with Retry Logic
# =========================================================

_pg_pool = None
_pg_pool_error = None  # Store last error for diagnostics
_pg_pool_last_attempt = 0  # Timestamp of last connection attempt
_PG_RETRY_INTERVAL = 30  # Seconds between retry attempts

def get_pg_pool(force_retry: bool = False):
    """
    Get or create PostgreSQL connection pool with lazy initialization and retry logic.

    Args:
        force_retry: If True, attempt connection even if recently failed

    Returns:
        Connection pool or None if connection fails
    """
    global _pg_pool, _pg_pool_error, _pg_pool_last_attempt

    if not DATABASE_URL:
        _pg_pool_error = "DATABASE_URL not set"
        return None

    # If pool exists and is valid, return it
    if _pg_pool is not None:
        return _pg_pool

    # Throttle retry attempts (don't hammer the database)
    current_time = time.time()
    if not force_retry and _pg_pool_last_attempt > 0:
        time_since_last = current_time - _pg_pool_last_attempt
        if time_since_last < _PG_RETRY_INTERVAL:
            logger.debug(f"Skipping pool creation - retry in {_PG_RETRY_INTERVAL - time_since_last:.0f}s")
            return None

    # Attempt to create pool with retries
    max_retries = 3
    retry_delay = 2  # seconds

    for attempt in range(1, max_retries + 1):
        _pg_pool_last_attempt = time.time()

        try:
            import psycopg2
            from psycopg2 import pool

            logger.info(f"Attempting PostgreSQL connection (attempt {attempt}/{max_retries})...")

            # Create connection pool
            _pg_pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=DATABASE_URL,
                connect_timeout=10  # 10 second connection timeout
            )

            # Test the connection immediately
            test_conn = _pg_pool.getconn()
            try:
                with test_conn.cursor() as cur:
                    cur.execute("SELECT 1")
                logger.info("PostgreSQL connection pool created and tested successfully!")
                _pg_pool_error = None  # Clear error on success
                return _pg_pool
            finally:
                _pg_pool.putconn(test_conn)

        except psycopg2.OperationalError as e:
            error_msg = str(e)
            _pg_pool_error = f"OperationalError: {error_msg}"
            logger.error(f"PostgreSQL OperationalError (attempt {attempt}): {error_msg}")

            # Check for specific error types
            if "password authentication failed" in error_msg.lower():
                logger.error("Password is incorrect - check DATABASE_URL")
                break  # Don't retry for auth failures
            elif "could not connect to server" in error_msg.lower():
                logger.error("Cannot reach database server - check network/host")
            elif "network is unreachable" in error_msg.lower():
                logger.error("Network unreachable - possible IPv6 issue")

            _pg_pool = None

        except psycopg2.Error as e:
            _pg_pool_error = f"PostgreSQL Error [{e.pgcode}]: {e.pgerror or e}"
            logger.error(f"PostgreSQL Error (attempt {attempt}): {_pg_pool_error}")
            _pg_pool = None

        except Exception as e:
            _pg_pool_error = f"{type(e).__name__}: {e}"
            logger.error(f"Unexpected error (attempt {attempt}): {_pg_pool_error}")
            _pg_pool = None

        # Wait before retry (except on last attempt)
        if attempt < max_retries:
            logger.info(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            retry_delay *= 2  # Exponential backoff

    logger.error(f"Failed to create PostgreSQL pool after {max_retries} attempts")
    return None

def get_pg_pool_error() -> Optional[str]:
    """Get the last connection pool error for diagnostics."""
    return _pg_pool_error

def reset_pg_pool():
    """Reset pool state to force a fresh connection attempt."""
    global _pg_pool, _pg_pool_error, _pg_pool_last_attempt
    if _pg_pool:
        try:
            _pg_pool.closeall()
        except Exception:
            pass
    _pg_pool = None
    _pg_pool_error = None
    _pg_pool_last_attempt = 0
    logger.info("PostgreSQL pool reset - will retry on next request")

@contextmanager
def get_pg_connection():
    """Get a connection from the pool with detailed error reporting."""
    pool = get_pg_pool()
    if pool is None:
        # Build detailed error message
        error_details = []
        error_details.append(f"DB_MODE={DB_MODE}")
        error_details.append(f"DATABASE_URL set={bool(DATABASE_URL)}")

        if DATABASE_URL:
            import re
            masked = re.sub(r':([^:@]+)@', ':****@', DATABASE_URL)
            error_details.append(f"URL (masked): {masked}")

        if _pg_pool_error:
            error_details.append(f"Last error: {_pg_pool_error}")

        error_msg = f"PostgreSQL pool not available. {'; '.join(error_details)}"
        logger.error(error_msg)
        raise ConnectionError(error_msg)

    conn = None
    try:
        conn = pool.getconn()
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"PostgreSQL connection error: {type(e).__name__}: {e}")
        raise e
    finally:
        if conn and pool:
            pool.putconn(conn)

def close_pg_pool():
    """Close all connections in the pool."""
    global _pg_pool
    if _pg_pool:
        _pg_pool.closeall()
        _pg_pool = None
        logger.info("PostgreSQL connection pool closed")

# =========================================================
# Unified Query Interface
# =========================================================

def run_query(sql: str, params: tuple = None, db_type: str = 'experiment') -> 'pd.DataFrame':
    """
    Execute a SELECT query and return results as DataFrame.
    Automatically chooses between DuckDB and PostgreSQL based on DB_MODE.

    Args:
        sql: SQL query string
        params: Query parameters (tuple for PostgreSQL, list for DuckDB)
        db_type: 'experiment' or 'warehouse'

    Returns:
        pandas DataFrame with query results
    """
    import pandas as pd

    if DB_MODE == 'supabase' and DATABASE_URL:
        return _pg_query(sql, params)
    else:
        return _duckdb_query(sql, params, db_type)

def _pg_query(sql: str, params: tuple = None) -> 'pd.DataFrame':
    """Execute query on PostgreSQL."""
    import pandas as pd
    try:
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                if cur.description:
                    columns = [desc[0] for desc in cur.description]
                    data = cur.fetchall()
                    return pd.DataFrame(data, columns=columns)
                return pd.DataFrame()
    except Exception as e:
        logger.error(f"PostgreSQL query error: {e}")
        return pd.DataFrame()

def _duckdb_query(sql: str, params: tuple = None, db_type: str = 'experiment') -> 'pd.DataFrame':
    """Execute query on DuckDB (local mode)."""
    import pandas as pd
    import duckdb

    db_path = WAREHOUSE_DB_PATH if db_type == 'warehouse' else EXPERIMENT_DB_PATH

    try:
        with duckdb.connect(db_path, read_only=True) as conn:
            if params:
                return conn.execute(sql, list(params)).df()
            return conn.execute(sql).df()
    except Exception as e:
        logger.error(f"DuckDB query error: {e}")
        return pd.DataFrame()

# =========================================================
# Unified Write Interface
# =========================================================

def execute_write(sql: str, params: tuple = None) -> Dict[str, Any]:
    """
    Execute a write (INSERT/UPDATE/DELETE) statement.

    Args:
        sql: SQL statement
        params: Query parameters

    Returns:
        dict with 'status' and 'message'
    """
    if DB_MODE == 'supabase' and DATABASE_URL:
        return _pg_write(sql, params)
    else:
        return _duckdb_write(sql, params)

def _pg_write(sql: str, params: tuple = None) -> Dict[str, Any]:
    """Execute write on PostgreSQL."""
    try:
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
        return {"status": "success", "message": "Write completed"}
    except Exception as e:
        logger.error(f"PostgreSQL write error: {e}")
        return {"status": "error", "message": str(e)}

def _duckdb_write(sql: str, params: tuple = None) -> Dict[str, Any]:
    """Execute write on DuckDB."""
    import duckdb
    try:
        with duckdb.connect(EXPERIMENT_DB_PATH) as conn:
            if params:
                conn.execute(sql, list(params))
            else:
                conn.execute(sql)
        return {"status": "success", "message": "Write completed"}
    except Exception as e:
        logger.error(f"DuckDB write error: {e}")
        return {"status": "error", "message": str(e)}

def execute_batch(operations: List[Tuple[str, tuple]]) -> Dict[str, Any]:
    """
    Execute multiple write operations in a transaction.

    Args:
        operations: List of (sql, params) tuples

    Returns:
        dict with 'status' and 'results'
    """
    if DB_MODE == 'supabase' and DATABASE_URL:
        return _pg_batch(operations)
    else:
        return _duckdb_batch(operations)

def _pg_batch(operations: List[Tuple[str, tuple]]) -> Dict[str, Any]:
    """Execute batch on PostgreSQL."""
    results = []
    try:
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                for sql, params in operations:
                    try:
                        cur.execute(sql, params)
                        results.append({"sql": sql[:50], "status": "success"})
                    except Exception as e:
                        results.append({"sql": sql[:50], "status": "error", "message": str(e)})
        return {"status": "success", "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e), "results": results}

def _duckdb_batch(operations: List[Tuple[str, tuple]]) -> Dict[str, Any]:
    """Execute batch on DuckDB."""
    import duckdb
    results = []
    try:
        with duckdb.connect(EXPERIMENT_DB_PATH) as conn:
            for sql, params in operations:
                try:
                    if params:
                        conn.execute(sql, list(params))
                    else:
                        conn.execute(sql)
                    results.append({"sql": sql[:50], "status": "success"})
                except Exception as e:
                    results.append({"sql": sql[:50], "status": "error", "message": str(e)})
        return {"status": "success", "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e), "results": results}

# =========================================================
# Schema Setup (PostgreSQL)
# =========================================================

def setup_pg_schema():
    """
    Create tables in PostgreSQL (Supabase).
    Run this once during initial deployment.
    """
    if not DATABASE_URL:
        logger.error("DATABASE_URL not set")
        return False

    schema_sql = """
    -- Assignments table
    CREATE TABLE IF NOT EXISTS assignments (
        id SERIAL PRIMARY KEY,
        user_id VARCHAR(255),
        experiment_id VARCHAR(255),
        variant VARCHAR(10),
        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        run_id VARCHAR(255),
        weight FLOAT DEFAULT 1.0
    );

    -- Events table
    CREATE TABLE IF NOT EXISTS events (
        id SERIAL PRIMARY KEY,
        event_id VARCHAR(255),
        user_id VARCHAR(255),
        event_name VARCHAR(100),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        value DOUBLE PRECISION DEFAULT 0,
        run_id VARCHAR(255)
    );

    -- Experiments (Retrospective) table
    CREATE TABLE IF NOT EXISTS experiments (
        exp_id SERIAL PRIMARY KEY,
        target VARCHAR(255),
        hypothesis TEXT,
        primary_metric VARCHAR(100),
        guardrails VARCHAR(500),
        sample_size INTEGER,
        start_date DATE,
        end_date DATE,
        traffic_split FLOAT,
        p_value FLOAT,
        decision VARCHAR(50),
        learning_note TEXT,
        run_id VARCHAR(255),
        control_rate FLOAT,
        test_rate FLOAT,
        lift FLOAT,
        guardrail_results TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Adoptions table
    CREATE TABLE IF NOT EXISTS adoptions (
        adoption_id SERIAL PRIMARY KEY,
        experiment_id VARCHAR(255),
        variant_config TEXT,
        adopted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Active Experiment table
    CREATE TABLE IF NOT EXISTS active_experiment (
        id SERIAL PRIMARY KEY,
        is_active BOOLEAN DEFAULT FALSE,
        started_at TIMESTAMP
    );

    -- Create indexes for performance
    CREATE INDEX IF NOT EXISTS idx_assignments_run_id ON assignments(run_id);
    CREATE INDEX IF NOT EXISTS idx_events_run_id ON events(run_id);
    CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id);
    CREATE INDEX IF NOT EXISTS idx_experiments_run_id ON experiments(run_id);
    """

    try:
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(schema_sql)
        logger.info("PostgreSQL schema created successfully")
        return True
    except Exception as e:
        logger.error(f"Schema creation failed: {e}")
        return False

# =========================================================
# Migration Utilities
# =========================================================

def migrate_duckdb_to_supabase():
    """
    Migrate data from local DuckDB to Supabase PostgreSQL.
    Run this once to transfer existing data to cloud.
    """
    import pandas as pd
    import duckdb

    if not DATABASE_URL:
        logger.error("DATABASE_URL not set for migration")
        return False

    tables = ['assignments', 'events', 'experiments', 'adoptions']

    for table in tables:
        try:
            # Read from DuckDB
            with duckdb.connect(EXPERIMENT_DB_PATH, read_only=True) as duck_conn:
                df = duck_conn.execute(f"SELECT * FROM {table}").df()

            if df.empty:
                logger.info(f"Table {table} is empty, skipping")
                continue

            # Write to PostgreSQL
            with get_pg_connection() as pg_conn:
                from psycopg2.extras import execute_values
                with pg_conn.cursor() as cur:
                    columns = df.columns.tolist()
                    values = [tuple(row) for row in df.values]
                    insert_sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES %s ON CONFLICT DO NOTHING"
                    execute_values(cur, insert_sql, values)

            logger.info(f"Migrated {len(df)} rows from {table}")
        except Exception as e:
            logger.error(f"Migration error for {table}: {e}")

    return True

# =========================================================
# Health Check
# =========================================================

def health_check() -> Dict[str, Any]:
    """Check database connectivity."""
    result = {"mode": DB_MODE, "status": "unknown"}

    if DB_MODE == 'supabase' and DATABASE_URL:
        try:
            with get_pg_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            result["status"] = "connected"
            result["database"] = "PostgreSQL (Supabase)"
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
    else:
        try:
            import duckdb
            with duckdb.connect(EXPERIMENT_DB_PATH, read_only=True) as conn:
                conn.execute("SELECT 1")
            result["status"] = "connected"
            result["database"] = "DuckDB (Local)"
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

    return result

if __name__ == "__main__":
    # Test connectivity
    print("Database Health Check:")
    print(health_check())

    if DB_MODE == 'supabase':
        print("\nSetting up PostgreSQL schema...")
        setup_pg_schema()
