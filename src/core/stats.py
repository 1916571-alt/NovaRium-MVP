import duckdb
import os
import hashlib
import numpy as np
import pandas as pd
from scipy import stats
import streamlit as st
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Stats")

# Try to load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Constants (DB Paths - Split Architecture)
# Assuming this script is in src/core/ folder, so db is two levels up
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(_BASE_DIR, 'data')
WAREHOUSE_DB_PATH = os.path.join(DATA_DIR, 'db', 'novarium_warehouse.db')  # users, orders, 30-day history
EXPERIMENT_DB_PATH = os.path.join(DATA_DIR, 'db', 'novarium_experiment.db')  # assignments, events, experiments

# Default DB_PATH points to experiment DB (most queries use this)
DB_PATH = EXPERIMENT_DB_PATH

# Cloud deployment configuration - prioritize Streamlit secrets
def _get_secret(key: str, default: str = '') -> str:
    """Get config from Streamlit secrets first, then env vars."""
    try:
        if hasattr(st, 'secrets') and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)

DB_MODE = _get_secret('DB_MODE', 'duckdb')  # 'duckdb' for local, 'supabase' for cloud
_raw_database_url = _get_secret('DATABASE_URL', '')  # PostgreSQL connection string
TARGET_APP_URL = _get_secret('TARGET_APP_URL', 'http://localhost:8000')

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

def is_cloud_mode():
    """Check if running in cloud mode (Supabase)."""
    return DB_MODE == 'supabase' and bool(DATABASE_URL)

def get_connection():
    """
    Establish a connection to the database.
    Returns DuckDB connection for local, None for cloud (use run_query instead).
    """
    if is_cloud_mode():
        return None
    return duckdb.connect(DB_PATH)

def run_query(query, con=None, max_retries=5, retry_delay=0.5, db_type='experiment'):
    """
    Execute a SQL query and return the result as a DataFrame.
    Supports both DuckDB (local) and PostgreSQL (Supabase cloud).

    Args:
        query: SQL query string
        con: Optional existing connection
        max_retries: Number of retry attempts for lock errors
        retry_delay: Base delay between retries
        db_type: 'experiment' (default) or 'warehouse'
    """
    import time
    import requests

    # Cloud mode: Use PostgreSQL
    if is_cloud_mode():
        return _pg_query(query)

    # Select DB path based on type
    target_db = WAREHOUSE_DB_PATH if db_type == 'warehouse' else EXPERIMENT_DB_PATH

    if con:
        # If connection is provided, use it directly (no retry needed)
        try:
            return con.execute(query).df()
        except Exception as e:
            try:
                logger.error(f"Query Error (Existing Conn): {repr(e)}")
            except:
                pass
            return pd.DataFrame()

    # 1. Try via Server API (Preferred) - only for experiment DB in local mode
    if db_type == 'experiment':
        try:
            response = requests.post(f"{TARGET_APP_URL}/admin/execute_sql", json={"sql": query}, timeout=2)
            if response.status_code == 200:
                res_json = response.json()
                if res_json.get("status") == "success":
                    data = res_json.get("data")
                    cols = res_json.get("columns", [])

                    if data is not None:
                        if not data and not cols:
                             return pd.DataFrame()
                        if cols:
                            return pd.DataFrame(data, columns=cols)
                        return pd.DataFrame(data)
                    else:
                        return pd.DataFrame()
        except:
            pass # API failed, fallback to direct DB

    # 2. Retry logic for transient connections (handles file locks)
    for attempt in range(max_retries):
        try:
            # Explicitly set read_only=True to allow concurrent reads even if locked by writer
            with duckdb.connect(target_db, read_only=True) as conn:
                return conn.execute(query).df()
        except Exception as e:
            error_msg = str(e).lower()

            # Check if it's a lock error
            if 'cannot open file' in error_msg or 'lock' in error_msg or 'access' in error_msg or 'process' in error_msg:
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = retry_delay * (2 ** attempt)
                    try:
                        logger.warning(f"DB locked, retrying in {wait_time:.2f}s... (Attempt {attempt + 1}/{max_retries})")
                    except:
                        pass
                    time.sleep(wait_time)
                    continue

            # Non-lock error or final retry failed
            try:
                logger.error(f"Query failed: {repr(e)}")
            except:
                pass
            return pd.DataFrame()

def _convert_duckdb_to_pg(query):
    """Convert DuckDB SQL syntax to PostgreSQL."""
    import re
    pg_query = query

    # INTERVAL 30 MINUTE -> INTERVAL '30 minutes'
    pg_query = re.sub(
        r"INTERVAL\s+(\d+)\s+MINUTE",
        r"INTERVAL '\1 minutes'",
        pg_query,
        flags=re.IGNORECASE
    )

    # INTERVAL 1 DAY -> INTERVAL '1 day'
    pg_query = re.sub(
        r"INTERVAL\s+(\d+)\s+DAY",
        r"INTERVAL '\1 days'",
        pg_query,
        flags=re.IGNORECASE
    )

    # INTERVAL 1 HOUR -> INTERVAL '1 hour'
    pg_query = re.sub(
        r"INTERVAL\s+(\d+)\s+HOUR",
        r"INTERVAL '\1 hours'",
        pg_query,
        flags=re.IGNORECASE
    )

    return pg_query

def _pg_query(query):
    """Execute query on PostgreSQL (Supabase cloud)."""
    global _pg_pool
    try:
        import psycopg2
        from psycopg2 import pool

        # Convert DuckDB syntax to PostgreSQL
        pg_query = _convert_duckdb_to_pg(query)

        # Get connection from pool (create if needed)
        if _pg_pool is None:
            logger.info(f"Creating PostgreSQL pool (DB_MODE={DB_MODE})")
            _pg_pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=5,
                dsn=DATABASE_URL
            )
            logger.info("PostgreSQL pool created successfully")

        conn = _pg_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(pg_query)
                if cur.description:
                    columns = [desc[0] for desc in cur.description]
                    data = cur.fetchall()
                    return pd.DataFrame(data, columns=columns)
                return pd.DataFrame()
        finally:
            _pg_pool.putconn(conn)
    except psycopg2.OperationalError as e:
        logger.error(f"PostgreSQL OperationalError: {e}")
        logger.error("Check: DATABASE_URL, password, SSL settings")
        _pg_pool = None
        return pd.DataFrame()
    except psycopg2.Error as e:
        logger.error(f"PostgreSQL Error [{e.pgcode}]: {e.pgerror or e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"PostgreSQL query error: {type(e).__name__}: {e}")
        return pd.DataFrame()

_pg_pool = None


@st.cache_data(ttl=3600)  # Cache for 1 hour
def calculate_sample_size(baseline_cvr, mde, alpha=0.05, power=0.8):
    """
    Calculate required sample size per variation for A/B testing.
    Uses Z-test formula for proportions.
    """
    standard_norm = stats.norm()
    Z_alpha = standard_norm.ppf(1 - alpha/2)
    Z_beta = standard_norm.ppf(power)

    p1 = baseline_cvr
    p2 = baseline_cvr * (1 + mde)

    pooled_prob = (p1 + p2) / 2

    if p1 == p2:
        return 0

    n = (2 * pooled_prob * (1 - pooled_prob) * (Z_alpha + Z_beta)**2) / (p1 - p2)**2
    return int(n)

def get_bucket(user_id, num_buckets=100):
    """
    Deterministic hashing function to bucket users.
    Returns an integer between 0 and num_buckets-1.
    """
    hash_obj = hashlib.md5(str(user_id).encode())
    return int(hash_obj.hexdigest(), 16) % num_buckets

@st.cache_data(ttl=60)  # Cache for 1 minute (short TTL for live data)
def calculate_statistics(c_users, c_conv, t_users, t_conv):
    """
    Calculate A/B test statistics: CVRs, Lift, and P-value.
    Returns a dictionary with results.
    """
    # Rates
    c_rate = c_conv / c_users if c_users > 0 else 0
    t_rate = t_conv / t_users if t_users > 0 else 0
    
    # Lift
    lift = (t_rate - c_rate) / c_rate if c_rate > 0 else 0
    
    # P-value (Two-proportion Z-test)
    p_val = 1.0
    se = 0
    z = 0
    margin_of_error = 0
    
    if c_users > 0 and t_users > 0:
        pooled_p = (c_conv + t_conv) / (c_users + t_users)
        se = np.sqrt(pooled_p * (1 - pooled_p) * (1/c_users + 1/t_users))
        
        if se > 0:
            z = (t_rate - c_rate) / se
            p_val = stats.norm.sf(abs(z)) * 2  # Two-tailed
    
    return {
        "control_rate": c_rate,
        "test_rate": t_rate,
        "lift": lift,
        "p_value": p_val,
        "z_score": z,
        "se": se
    }

def format_delta(val, is_percent=True):
    """
    Helper to format delta strings (e.g., "+5.00%" or "-0.12")
    """
    prefix = "+" if val >= 0 else ""
    if is_percent:
        return f"{prefix}{val*100:.2f}%"
    return f"{prefix}{val:.4f}"

def calculate_retention_rate(cohort_size, retained_count):
    """
    Calculate retention rate.
    Returns value between 0.0 and 1.0.
    """
    if cohort_size <= 0:
        return 0.0
    return retained_count / cohort_size

def get_user_segments(con=None):
    """
    Analyze existing user behavior in DB to define Persona Distribution.
    Returns a dictionary with percentage values (0-100) for each segment.
    Uses WAREHOUSE DB (users, orders tables).
    """
    sql = """
    WITH user_metrics AS (
        SELECT
            u.user_id,
            COUNT(o.order_id) as order_count,
            COALESCE(SUM(o.amount), 0) as total_spent,
            DATE_DIFF('day', MIN(u.joined_at)::TIMESTAMP, CURRENT_DATE) as tenure_days
        FROM users u
        LEFT JOIN orders o ON u.user_id = o.user_id
        GROUP BY 1
    ),
    averages AS (
        SELECT AVG(total_spent) as avg_spent FROM user_metrics WHERE order_count > 0
    )
    SELECT
        CASE
            WHEN order_count = 0 THEN 'Window'
            WHEN order_count >= 3 THEN 'Mission'
            WHEN total_spent > (SELECT avg_spent FROM averages) THEN 'Rational'
            WHEN tenure_days < 30 THEN 'Impulsive'
            ELSE 'Cautious'
        END as segment,
        COUNT(*) as cnt
    FROM user_metrics
    GROUP BY 1
    """
    # Uses warehouse DB for users/orders data
    df = run_query(sql, con, db_type='warehouse')
    
    if df.empty:
        # Fallback default
        return {'Impulsive': 20, 'Rational': 20, 'Window': 40, 'Mission': 10, 'Cautious': 10}
        
    total = df['cnt'].sum()
    if total == 0: return {}
    
    seg_map = df.set_index('segment')['cnt'].to_dict()
    
    # Normalize to 100% total (integer)
    raw_dist = {k: (v/total)*100 for k, v in seg_map.items()}
    
    # Fill missing keys
    keys = ['Impulsive', 'Rational', 'Window', 'Mission', 'Cautious']
    final_dist = {k: int(raw_dist.get(k, 0)) for k in keys}
    
    # Adjust rounding error to ensure 100
    current_sum = sum(final_dist.values())
    diff = 100 - current_sum
    if diff != 0:
        # Add diff to the largest segment
        max_key = max(final_dist, key=final_dist.get)
        final_dist[max_key] += diff
        
    return final_dist
