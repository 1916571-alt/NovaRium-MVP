"""
Statistics and Analytics Module for A/B Testing.

This module provides functions for:
- Database connections (DuckDB local, PostgreSQL cloud)
- Sample size calculations
- Statistical analysis (Z-tests, p-values)
- User segmentation
"""
import duckdb
import os
import hashlib
import numpy as np
import pandas as pd
from scipy import stats
import streamlit as st
from typing import Any, Dict, Optional, Union

# Use centralized logging
from src.core.logging_config import get_logger, log_db_query
from src.core.errors import QueryError, LockError, ParameterError
from src.core.validators import validate_ab_test_params, validate_user_counts

logger = get_logger(__name__)

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

def is_cloud_mode() -> bool:
    """Check if running in cloud mode (Supabase)."""
    return DB_MODE == 'supabase' and bool(DATABASE_URL)

def get_connection() -> Optional[duckdb.DuckDBPyConnection]:
    """
    Establish a connection to the database.

    Returns:
        DuckDB connection for local mode, None for cloud mode (use run_query instead)
    """
    if is_cloud_mode():
        return None
    return duckdb.connect(DB_PATH)

def run_query(
    query: str,
    con: Optional[duckdb.DuckDBPyConnection] = None,
    max_retries: int = 5,
    retry_delay: float = 0.5,
    db_type: str = 'experiment'
) -> pd.DataFrame:
    """
    Execute a SQL query and return the result as a DataFrame.

    Supports both DuckDB (local) and PostgreSQL (Supabase cloud).

    Args:
        query: SQL query string
        con: Optional existing DuckDB connection
        max_retries: Number of retry attempts for lock errors
        retry_delay: Base delay between retries (seconds)
        db_type: Database type - 'experiment' (default) or 'warehouse'

    Returns:
        Query results as pandas DataFrame, empty DataFrame on error
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
        except Exception as e:
            logger.debug(f"API fallback - Server unavailable: {type(e).__name__}")

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

def _convert_duckdb_to_pg(query: str) -> str:
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

    # DATE_DIFF('day', start, end) -> EXTRACT(DAY FROM (end - start))
    # DuckDB: DATE_DIFF('day', MIN(u.joined_at)::TIMESTAMP, CURRENT_DATE)
    # PostgreSQL: EXTRACT(DAY FROM (CURRENT_DATE - MIN(u.joined_at)::TIMESTAMP))
    pg_query = re.sub(
        r"DATE_DIFF\s*\(\s*['\"]day['\"]\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)",
        r"EXTRACT(DAY FROM (\2 - \1))",
        pg_query,
        flags=re.IGNORECASE
    )

    # DATEDIFF('second', start, end) -> EXTRACT(EPOCH FROM (end - start))
    # Simple case without nested parentheses (complex cases should be handled in app.py directly)
    pg_query = re.sub(
        r"DATEDIFF\s*\(\s*['\"]second['\"]\s*,\s*([^,)]+)\s*,\s*([^)]+)\s*\)",
        r"EXTRACT(EPOCH FROM (\2 - \1))",
        pg_query,
        flags=re.IGNORECASE
    )

    return pg_query

def _pg_query(query: str) -> pd.DataFrame:
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
def calculate_sample_size(
    baseline_cvr: float,
    mde: float,
    alpha: float = 0.05,
    power: float = 0.8
) -> int:
    """
    Calculate required sample size per variation for A/B testing.

    Uses Z-test formula for proportions.

    Args:
        baseline_cvr: Baseline conversion rate (0 < x < 1)
        mde: Minimum detectable effect as proportion (e.g., 0.05 for 5%)
        alpha: Significance level (default 0.05)
        power: Statistical power (default 0.8)

    Returns:
        Required sample size per group as integer

    Raises:
        ParameterError: If parameters are invalid
    """
    # Special case: no effect needed means no samples needed
    if mde == 0:
        return 0

    # Validate inputs (skip for edge cases that would be caught later)
    try:
        validated = validate_ab_test_params(baseline_cvr, mde, alpha, power)
        baseline_cvr = validated["baseline_cvr"]
        mde = validated["mde"]
        alpha = validated["alpha"]
        power = validated["power"]
    except ParameterError as e:
        logger.warning(f"Parameter validation: {e}")
        # Allow calculation to proceed for backwards compatibility
    except Exception as e:
        logger.warning(f"Validation skipped due to error: {e}")

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

def get_bucket(user_id: Union[str, int], num_buckets: int = 100) -> int:
    """
    Deterministic hashing function to bucket users.

    Args:
        user_id: User identifier (string or integer)
        num_buckets: Number of buckets (default 100)

    Returns:
        Integer between 0 and num_buckets-1
    """
    hash_obj = hashlib.md5(str(user_id).encode())
    return int(hash_obj.hexdigest(), 16) % num_buckets

@st.cache_data(ttl=60)  # Cache for 1 minute (short TTL for live data)
def calculate_statistics(
    c_users: int,
    c_conv: int,
    t_users: int,
    t_conv: int
) -> Dict[str, float]:
    """
    Calculate A/B test statistics: CVRs, Lift, and P-value.

    Args:
        c_users: Number of users in control group
        c_conv: Number of conversions in control group
        t_users: Number of users in test group
        t_conv: Number of conversions in test group

    Returns:
        Dictionary with: control_rate, test_rate, lift, p_value, z_score, se

    Raises:
        ParameterError: If counts are invalid
        DataError: If conversions exceed users
    """
    # Validate inputs
    try:
        validate_user_counts(c_users, c_conv, t_users, t_conv)
    except Exception as e:
        logger.warning(f"Validation warning: {e}")
        # Continue with calculation but log the issue

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

# =============================================================================
# Advanced Statistical Functions
# =============================================================================

def check_srm(
    control_users: int,
    test_users: int,
    expected_ratio: float = 0.5
) -> Dict[str, Any]:
    """
    Check for Sample Ratio Mismatch (SRM) using chi-squared test.

    SRM occurs when the actual split ratio differs significantly from expected,
    indicating potential issues with randomization or data collection.

    Args:
        control_users: Number of users in control group
        test_users: Number of users in test group
        expected_ratio: Expected proportion in control (default 0.5 for 50/50)

    Returns:
        Dictionary with:
        - observed_ratio: Actual ratio of control users
        - expected_ratio: Expected ratio
        - chi2: Chi-squared statistic
        - p_value: P-value for the test
        - is_srm: True if SRM detected (p < 0.01)
        - message: Human-readable result
    """
    total = control_users + test_users
    if total == 0:
        return {
            "observed_ratio": 0,
            "expected_ratio": expected_ratio,
            "chi2": 0,
            "p_value": 1.0,
            "is_srm": False,
            "message": "No data available"
        }

    observed_ratio = control_users / total
    expected_control = total * expected_ratio
    expected_test = total * (1 - expected_ratio)

    # Chi-squared test
    observed = [control_users, test_users]
    expected = [expected_control, expected_test]

    chi2, p_value = stats.chisquare(observed, expected)

    # SRM threshold: p < 0.01 (more strict than typical 0.05)
    is_srm = p_value < 0.01

    if is_srm:
        message = f"SRM detected (p={p_value:.4f}). Check randomization."
    else:
        message = f"No SRM (p={p_value:.4f}). Split ratio is valid."

    return {
        "observed_ratio": observed_ratio,
        "expected_ratio": expected_ratio,
        "chi2": float(chi2),
        "p_value": float(p_value),
        "is_srm": is_srm,
        "message": message
    }


def calculate_sequential_bounds(
    n_looks: int,
    alpha: float = 0.05,
    method: str = "obrien_fleming"
) -> list:
    """
    Calculate spending function boundaries for sequential testing.

    Sequential testing allows early stopping when results are conclusive,
    while controlling overall Type I error rate.

    Args:
        n_looks: Number of interim analyses planned
        alpha: Overall significance level (default 0.05)
        method: 'obrien_fleming' (conservative early) or 'pocock' (equal bounds)

    Returns:
        List of critical z-values for each look
    """
    if n_looks < 1:
        return []

    if n_looks == 1:
        # Single look = standard z-critical
        return [stats.norm.ppf(1 - alpha / 2)]

    bounds = []
    info_fractions = [(i + 1) / n_looks for i in range(n_looks)]

    for t in info_fractions:
        if method == "obrien_fleming":
            # O'Brien-Fleming: Conservative early, liberal late
            # z_critical = z_alpha / sqrt(t)
            z_base = stats.norm.ppf(1 - alpha / 2)
            z_crit = z_base / np.sqrt(t)
        elif method == "pocock":
            # Pocock: Equal bounds at each look
            # Approximation: adjust alpha for multiple looks
            adjusted_alpha = alpha / n_looks
            z_crit = stats.norm.ppf(1 - adjusted_alpha / 2)
        else:
            # Default to O'Brien-Fleming
            z_base = stats.norm.ppf(1 - alpha / 2)
            z_crit = z_base / np.sqrt(t)

        bounds.append(round(z_crit, 3))

    return bounds


def check_sequential_stopping(
    z_score: float,
    current_look: int,
    n_looks: int,
    alpha: float = 0.05,
    method: str = "obrien_fleming"
) -> Dict[str, Any]:
    """
    Check if experiment can be stopped early based on sequential testing.

    Args:
        z_score: Current z-score from calculate_statistics
        current_look: Which interim analysis this is (1-indexed)
        n_looks: Total number of planned looks
        alpha: Overall significance level
        method: Boundary method ('obrien_fleming' or 'pocock')

    Returns:
        Dictionary with:
        - can_stop: True if early stopping is justified
        - z_boundary: Critical z-value for this look
        - z_score: Observed z-score
        - info_fraction: Proportion of data analyzed
        - message: Human-readable recommendation
    """
    if current_look < 1 or current_look > n_looks:
        return {
            "can_stop": False,
            "z_boundary": None,
            "z_score": z_score,
            "info_fraction": 0,
            "message": "Invalid look number"
        }

    bounds = calculate_sequential_bounds(n_looks, alpha, method)
    z_boundary = bounds[current_look - 1]
    info_fraction = current_look / n_looks

    can_stop = abs(z_score) >= z_boundary

    if can_stop:
        if z_score > 0:
            message = f"Early stop: Test wins (z={z_score:.2f} >= {z_boundary:.2f})"
        else:
            message = f"Early stop: Control wins (z={z_score:.2f} <= -{z_boundary:.2f})"
    else:
        remaining = n_looks - current_look
        if remaining > 0:
            message = f"Continue: z={z_score:.2f} (need |z| >= {z_boundary:.2f}). {remaining} looks remaining."
        else:
            message = f"Final look: Result is {'significant' if abs(z_score) >= z_boundary else 'not significant'}."

    return {
        "can_stop": can_stop,
        "z_boundary": z_boundary,
        "z_score": z_score,
        "info_fraction": info_fraction,
        "message": message
    }


def bonferroni_correction(p_values: list, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Bonferroni correction for multiple comparisons.

    When testing multiple hypotheses (e.g., multiple guardrail metrics),
    this adjusts the significance threshold to control family-wise error rate.

    Args:
        p_values: List of p-values from multiple tests
        alpha: Desired family-wise error rate (default 0.05)

    Returns:
        Dictionary with:
        - adjusted_alpha: Corrected significance threshold
        - n_tests: Number of tests
        - significant: List of booleans indicating significance
        - n_significant: Count of significant results
        - any_significant: True if any test is significant
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return {
            "adjusted_alpha": alpha,
            "n_tests": 0,
            "significant": [],
            "n_significant": 0,
            "any_significant": False
        }

    adjusted_alpha = alpha / n_tests
    significant = [p < adjusted_alpha for p in p_values]

    return {
        "adjusted_alpha": adjusted_alpha,
        "n_tests": n_tests,
        "significant": significant,
        "n_significant": sum(significant),
        "any_significant": any(significant)
    }


def calculate_confidence_interval(
    rate: float,
    n: int,
    confidence: float = 0.95
) -> Dict[str, float]:
    """
    Calculate confidence interval for a proportion.

    Uses Wilson score interval for better coverage with small samples.

    Args:
        rate: Observed proportion (0 to 1)
        n: Sample size
        confidence: Confidence level (default 0.95)

    Returns:
        Dictionary with:
        - rate: Point estimate
        - lower: Lower bound of CI
        - upper: Upper bound of CI
        - margin_of_error: Half-width of interval
    """
    if n <= 0:
        return {"rate": 0, "lower": 0, "upper": 0, "margin_of_error": 0}

    z = stats.norm.ppf(1 - (1 - confidence) / 2)

    # Wilson score interval
    denominator = 1 + z**2 / n
    center = (rate + z**2 / (2 * n)) / denominator
    margin = (z / denominator) * np.sqrt(rate * (1 - rate) / n + z**2 / (4 * n**2))

    lower = max(0, center - margin)
    upper = min(1, center + margin)

    return {
        "rate": rate,
        "lower": lower,
        "upper": upper,
        "margin_of_error": margin
    }


def calculate_lift_confidence_interval(
    c_rate: float,
    c_n: int,
    t_rate: float,
    t_n: int,
    confidence: float = 0.95
) -> Dict[str, float]:
    """
    Calculate confidence interval for relative lift.

    Args:
        c_rate: Control conversion rate
        c_n: Control sample size
        t_rate: Test conversion rate
        t_n: Test sample size
        confidence: Confidence level (default 0.95)

    Returns:
        Dictionary with:
        - lift: Point estimate of relative lift
        - lower: Lower bound of lift CI
        - upper: Upper bound of lift CI
        - is_significant: True if CI doesn't include 0
    """
    if c_rate <= 0 or c_n <= 0 or t_n <= 0:
        return {"lift": 0, "lower": 0, "upper": 0, "is_significant": False}

    # Point estimate
    lift = (t_rate - c_rate) / c_rate

    # Delta method for variance of ratio
    z = stats.norm.ppf(1 - (1 - confidence) / 2)

    # Variance of difference
    var_diff = (c_rate * (1 - c_rate) / c_n) + (t_rate * (1 - t_rate) / t_n)
    se_diff = np.sqrt(var_diff)

    # CI for difference
    diff = t_rate - c_rate
    diff_lower = diff - z * se_diff
    diff_upper = diff + z * se_diff

    # Convert to relative lift
    lift_lower = diff_lower / c_rate
    lift_upper = diff_upper / c_rate

    # Significant if CI doesn't include 0
    is_significant = (lift_lower > 0) or (lift_upper < 0)

    return {
        "lift": lift,
        "lower": lift_lower,
        "upper": lift_upper,
        "is_significant": is_significant
    }


def format_delta(val: float, is_percent: bool = True) -> str:
    """
    Format delta strings (e.g., "+5.00%" or "-0.12").

    Args:
        val: Numeric value to format
        is_percent: If True, multiply by 100 and add % suffix

    Returns:
        Formatted string with +/- prefix
    """
    prefix = "+" if val >= 0 else ""
    if is_percent:
        return f"{prefix}{val*100:.2f}%"
    return f"{prefix}{val:.4f}"

def calculate_retention_rate(cohort_size: int, retained_count: int) -> float:
    """
    Calculate retention rate.

    Args:
        cohort_size: Total users in cohort
        retained_count: Users retained

    Returns:
        Retention rate between 0.0 and 1.0
    """
    if cohort_size <= 0:
        return 0.0
    return retained_count / cohort_size

def get_user_segments(
    con: Optional[duckdb.DuckDBPyConnection] = None
) -> Dict[str, int]:
    """
    Analyze existing user behavior in DB to define Persona Distribution.

    Args:
        con: Optional existing DuckDB connection

    Returns:
        Dictionary with percentage values (0-100) for each segment:
        - Window, Mission, Rational, Impulsive, Cautious

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
