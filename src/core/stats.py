"""
Statistics and database utilities for NovaRium Edu.

This module provides:
- Database connection management
- SQL query execution with retry logic
- A/B test statistical calculations
- User segmentation analysis
"""
import duckdb
import os
import hashlib
import logging
import time
from typing import Optional, Dict, Any, Union

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
import requests
import streamlit as st

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'novarium_local.db'
)


class DatabaseError(Exception):
    """Base exception for database errors."""
    pass


class QueryError(DatabaseError):
    """Exception raised when a query fails."""
    pass


class ConnectionError(DatabaseError):
    """Exception raised when database connection fails."""
    pass


def get_connection() -> duckdb.DuckDBPyConnection:
    """
    Establish a connection to the DuckDB database.

    Returns:
        DuckDB connection object

    Raises:
        ConnectionError: If connection cannot be established
    """
    try:
        return duckdb.connect(DB_PATH)
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise ConnectionError(f"Failed to connect to database: {e}") from e


def run_query(
    query: str,
    con: Optional[duckdb.DuckDBPyConnection] = None,
    max_retries: int = 5,
    retry_delay: float = 0.5
) -> pd.DataFrame:
    """
    Execute a SQL query and return the result as a DataFrame.

    Prioritizes Server API to avoid file locking, then falls back to direct access.

    Args:
        query: SQL query string to execute
        con: Optional existing database connection
        max_retries: Maximum number of retry attempts for lock errors
        retry_delay: Base delay between retries (uses exponential backoff)

    Returns:
        Query results as a pandas DataFrame. Empty DataFrame on error.
    """
    if con:
        return _execute_with_connection(query, con)

    # Try via Server API first (preferred to avoid locking)
    result = _try_server_api(query)
    if result is not None:
        return result

    # Fallback to direct DB access with retry logic
    return _execute_with_retry(query, max_retries, retry_delay)


def _execute_with_connection(
    query: str,
    con: duckdb.DuckDBPyConnection
) -> pd.DataFrame:
    """Execute query using an existing connection."""
    try:
        return con.execute(query).df()
    except Exception as e:
        logger.warning(f"Query failed with existing connection: {e}")
        return pd.DataFrame()


def _try_server_api(query: str) -> Optional[pd.DataFrame]:
    """
    Try to execute query via the server API.

    Returns:
        DataFrame if successful, None if API is unavailable
    """
    try:
        response = requests.post(
            "http://localhost:8000/admin/execute_sql",
            json={"sql": query},
            timeout=2
        )
        if response.status_code == 200:
            res_json = response.json()
            if res_json.get("status") == "success":
                data = res_json.get("data")
                cols = res_json.get("columns", [])

                if data is None:
                    return pd.DataFrame()
                if not data and not cols:
                    return pd.DataFrame()
                if cols:
                    return pd.DataFrame(data, columns=cols)
                return pd.DataFrame(data)
    except requests.RequestException as e:
        logger.debug(f"Server API unavailable: {e}")
    except Exception as e:
        logger.debug(f"Server API error: {e}")

    return None


def _execute_with_retry(
    query: str,
    max_retries: int,
    retry_delay: float
) -> pd.DataFrame:
    """Execute query with retry logic for transient lock errors."""
    for attempt in range(max_retries):
        try:
            with duckdb.connect(DB_PATH, read_only=True) as conn:
                return conn.execute(query).df()
        except Exception as e:
            error_msg = str(e).lower()

            # Check if it's a lock-related error
            is_lock_error = any(
                keyword in error_msg
                for keyword in ['cannot open file', 'lock', 'access', 'process']
            )

            if is_lock_error and attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                logger.info(
                    f"DB locked, retrying in {wait_time:.2f}s "
                    f"(Attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(wait_time)
                continue

            # Non-lock error or final retry failed
            logger.warning(f"Query failed after {attempt + 1} attempts: {e}")
            return pd.DataFrame()

    return pd.DataFrame()


@st.cache_data(ttl=3600)
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
        baseline_cvr: Baseline conversion rate (e.g., 0.10 for 10%)
        mde: Minimum detectable effect as a proportion (e.g., 0.05 for 5% lift)
        alpha: Significance level (default 0.05)
        power: Statistical power (default 0.8)

    Returns:
        Required sample size per group as an integer
    """
    standard_norm = scipy_stats.norm()
    z_alpha = standard_norm.ppf(1 - alpha / 2)
    z_beta = standard_norm.ppf(power)

    p1 = baseline_cvr
    p2 = baseline_cvr * (1 + mde)

    pooled_prob = (p1 + p2) / 2

    if p1 == p2:
        return 0

    n = (2 * pooled_prob * (1 - pooled_prob) * (z_alpha + z_beta) ** 2) / (p1 - p2) ** 2
    return int(n)


def get_bucket(user_id: Union[str, int], num_buckets: int = 100) -> int:
    """
    Deterministic hashing function to bucket users.

    Args:
        user_id: User identifier
        num_buckets: Number of buckets to distribute users into

    Returns:
        Bucket number between 0 and num_buckets-1
    """
    hash_obj = hashlib.md5(str(user_id).encode())
    return int(hash_obj.hexdigest(), 16) % num_buckets


@st.cache_data(ttl=60)
def calculate_statistics(
    c_users: int,
    c_conv: int,
    t_users: int,
    t_conv: int
) -> Dict[str, float]:
    """
    Calculate A/B test statistics: conversion rates, lift, and P-value.

    Args:
        c_users: Number of users in control group
        c_conv: Number of conversions in control group
        t_users: Number of users in test group
        t_conv: Number of conversions in test group

    Returns:
        Dictionary containing:
        - control_rate: Control group conversion rate
        - test_rate: Test group conversion rate
        - lift: Relative lift (test vs control)
        - p_value: Two-tailed p-value from Z-test
        - z_score: Z-statistic
        - se: Standard error
    """
    # Calculate rates
    c_rate = c_conv / c_users if c_users > 0 else 0.0
    t_rate = t_conv / t_users if t_users > 0 else 0.0

    # Calculate lift
    lift = (t_rate - c_rate) / c_rate if c_rate > 0 else 0.0

    # Calculate P-value (Two-proportion Z-test)
    p_val = 1.0
    se = 0.0
    z = 0.0

    if c_users > 0 and t_users > 0:
        pooled_p = (c_conv + t_conv) / (c_users + t_users)
        se = np.sqrt(pooled_p * (1 - pooled_p) * (1 / c_users + 1 / t_users))

        if se > 0:
            z = (t_rate - c_rate) / se
            p_val = scipy_stats.norm.sf(abs(z)) * 2  # Two-tailed

    return {
        "control_rate": c_rate,
        "test_rate": t_rate,
        "lift": lift,
        "p_value": p_val,
        "z_score": z,
        "se": se
    }


def format_delta(val: float, is_percent: bool = True) -> str:
    """
    Format a delta value as a string with sign prefix.

    Args:
        val: The value to format
        is_percent: If True, format as percentage

    Returns:
        Formatted string (e.g., "+5.00%" or "-0.12")
    """
    prefix = "+" if val >= 0 else ""
    if is_percent:
        return f"{prefix}{val * 100:.2f}%"
    return f"{prefix}{val:.4f}"


def calculate_retention_rate(cohort_size: int, retained_count: int) -> float:
    """
    Calculate retention rate.

    Args:
        cohort_size: Total users in cohort
        retained_count: Number of users retained

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

    Segments users based on order history and spending patterns:
    - Window: No orders (browsing only)
    - Mission: 3+ orders (loyal customers)
    - Rational: Above-average spending
    - Impulsive: New users (< 30 days)
    - Cautious: Long tenure with occasional orders

    Args:
        con: Optional database connection

    Returns:
        Dictionary with percentage values (0-100) for each segment
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

    df = run_query(sql, con)

    # Default distribution if query fails
    default_dist = {
        'Impulsive': 20,
        'Rational': 20,
        'Window': 40,
        'Mission': 10,
        'Cautious': 10
    }

    if df.empty:
        logger.info("Using default user segment distribution")
        return default_dist

    total = df['cnt'].sum()
    if total == 0:
        return default_dist

    seg_map = df.set_index('segment')['cnt'].to_dict()

    # Normalize to 100% total (integer)
    raw_dist = {k: (v / total) * 100 for k, v in seg_map.items()}

    # Fill missing keys
    keys = ['Impulsive', 'Rational', 'Window', 'Mission', 'Cautious']
    final_dist = {k: int(raw_dist.get(k, 0)) for k in keys}

    # Adjust rounding error to ensure sum is 100
    current_sum = sum(final_dist.values())
    diff = 100 - current_sum
    if diff != 0:
        max_key = max(final_dist, key=final_dist.get)
        final_dist[max_key] += diff

    return final_dist
