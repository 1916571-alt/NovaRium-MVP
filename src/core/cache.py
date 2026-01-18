"""
Caching utilities for NovaRium Edu.

Provides cached query functions to improve performance by reducing
redundant database calls. Uses Streamlit's caching mechanism.
"""
import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any, List
from functools import wraps
import hashlib

from src.core import stats as al


# =============================================================================
# Cache Configuration
# =============================================================================

# TTL (Time To Live) in seconds for different cache types
CACHE_TTL = {
    'realtime': 30,      # Live data - refresh every 30 seconds
    'short': 60,         # Short-lived data - 1 minute
    'medium': 300,       # Medium data - 5 minutes
    'long': 3600,        # Long-lived data - 1 hour
    'static': 86400,     # Static data - 24 hours
}


# =============================================================================
# Dashboard Cached Queries
# =============================================================================

@st.cache_data(ttl=CACHE_TTL['realtime'])
def get_live_stats() -> pd.DataFrame:
    """
    Get real-time statistics (active users, today's orders/revenue).

    Returns:
        DataFrame with columns: active_users, today_orders, today_revenue
    """
    sql = """
        SELECT
            COUNT(DISTINCT user_id) as active_users,
            (SELECT COUNT(*) FROM events
             WHERE event_name = 'purchase'
             AND timestamp >= CURRENT_DATE) as today_orders,
            (SELECT COALESCE(SUM(value), 0) FROM events
             WHERE event_name = 'purchase'
             AND timestamp >= CURRENT_DATE) as today_revenue
        FROM events
        WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 30 MINUTE
    """
    return al.run_query(sql)


@st.cache_data(ttl=CACHE_TTL['realtime'])
def get_recent_events(limit: int = 5) -> pd.DataFrame:
    """
    Get recent event log entries.

    Args:
        limit: Maximum number of events to return

    Returns:
        DataFrame with recent events
    """
    sql = f"""
        SELECT user_id, event_name, value, timestamp
        FROM events
        ORDER BY timestamp DESC
        LIMIT {limit}
    """
    return al.run_query(sql)


@st.cache_data(ttl=CACHE_TTL['medium'])
def get_daily_kpi() -> pd.DataFrame:
    """
    Get daily KPI data from data mart.

    Returns:
        DataFrame with daily KPI metrics
    """
    return al.run_query("SELECT * FROM dm_daily_kpi ORDER BY report_date ASC")


@st.cache_data(ttl=CACHE_TTL['short'])
def check_historical_data() -> bool:
    """
    Check if historical data exists in the database.

    Returns:
        True if historical data exists
    """
    df = al.run_query(
        "SELECT COUNT(*) as cnt FROM assignments WHERE user_id LIKE 'user_hist_%'"
    )
    return not df.empty and df.iloc[0, 0] > 0


# =============================================================================
# Experiment Cached Queries
# =============================================================================

@st.cache_data(ttl=CACHE_TTL['short'])
def get_experiment_stats(run_id: str, metric_type: str = 'ctr') -> pd.DataFrame:
    """
    Get experiment statistics for a specific run.

    Args:
        run_id: Experiment run identifier
        metric_type: Type of metric ('ctr' or 'cvr')

    Returns:
        DataFrame with group statistics
    """
    event_filter = 'click_banner' if metric_type == 'ctr' else 'purchase'

    sql = f"""
        SELECT
            a.variant,
            COUNT(DISTINCT a.user_id) as users,
            COUNT(DISTINCT CASE WHEN e.event_name = '{event_filter}' THEN e.user_id END) as conversions
        FROM assignments a
        LEFT JOIN events e ON a.user_id = e.user_id AND a.run_id = e.run_id
        WHERE a.run_id = '{run_id}'
        GROUP BY a.variant
    """
    return al.run_query(sql)


@st.cache_data(ttl=CACHE_TTL['medium'])
def get_available_runs() -> pd.DataFrame:
    """
    Get list of available experiment runs.

    Returns:
        DataFrame with run_id and count information
    """
    sql = """
        SELECT run_id, COUNT(*) as cnt
        FROM assignments
        WHERE run_id IS NOT NULL
        GROUP BY run_id
        ORDER BY run_id DESC
    """
    return al.run_query(sql)


@st.cache_data(ttl=CACHE_TTL['short'])
def get_run_assignment_count(run_id: str) -> int:
    """
    Get the number of assignments for a specific run.

    Args:
        run_id: Experiment run identifier

    Returns:
        Number of assignments
    """
    df = al.run_query(
        f"SELECT COUNT(*) as cnt FROM assignments WHERE run_id = '{run_id}'"
    )
    return df.iloc[0]['cnt'] if not df.empty else 0


@st.cache_data(ttl=CACHE_TTL['short'])
def get_run_events(run_id: str, limit: int = 5) -> pd.DataFrame:
    """
    Get recent events for a specific run.

    Args:
        run_id: Experiment run identifier
        limit: Maximum events to return

    Returns:
        DataFrame with event data
    """
    sql = f"""
        SELECT timestamp, user_id, event_name
        FROM events
        WHERE run_id = '{run_id}'
        ORDER BY timestamp DESC
        LIMIT {limit}
    """
    return al.run_query(sql)


# =============================================================================
# Portfolio Cached Queries
# =============================================================================

@st.cache_data(ttl=CACHE_TTL['medium'])
def get_adopted_experiments() -> pd.DataFrame:
    """
    Get list of adopted experiments with details.

    Returns:
        DataFrame with adoption and experiment details
    """
    sql = """
        SELECT
            a.experiment_id,
            a.adopted_at,
            a.lift,
            a.p_value,
            e.hypothesis,
            e.target,
            e.primary_metric
        FROM adoptions a
        LEFT JOIN experiments e ON a.experiment_id = e.run_id
        ORDER BY a.adopted_at DESC
    """
    return al.run_query(sql)


@st.cache_data(ttl=CACHE_TTL['medium'])
def get_experiment_history() -> pd.DataFrame:
    """
    Get full experiment history.

    Returns:
        DataFrame with all experiment records
    """
    return al.run_query("SELECT * FROM experiments ORDER BY created_at DESC")


# =============================================================================
# Baseline Cached Queries
# =============================================================================

@st.cache_data(ttl=CACHE_TTL['long'])
def get_baseline_metric(metric_type: str = 'ctr') -> float:
    """
    Get baseline metric from historical data.

    Args:
        metric_type: Type of metric ('ctr' or 'cvr')

    Returns:
        Baseline metric value (default 0.10 if not found)
    """
    event_filter = 'click_banner' if metric_type == 'ctr' else 'purchase'

    sql = f"""
        SELECT
            (COUNT(DISTINCT CASE WHEN e.event_name = '{event_filter}' THEN e.user_id END)::FLOAT /
             NULLIF(COUNT(DISTINCT a.user_id), 0)) as metric_value
        FROM assignments a
        LEFT JOIN events e ON a.user_id = e.user_id
        WHERE a.user_id LIKE 'user_hist_%'
    """
    try:
        df = al.run_query(sql)
        if not df.empty and df.iloc[0, 0]:
            return float(df.iloc[0, 0])
    except Exception:
        pass
    return 0.10  # Default baseline


# =============================================================================
# Simulation Cached Queries
# =============================================================================

@st.cache_data(ttl=CACHE_TTL['medium'])
def get_user_segments() -> Dict[str, int]:
    """
    Get user segment distribution for agent simulation.

    Returns:
        Dict mapping segment names to percentages
    """
    return al.get_user_segments()


# =============================================================================
# Cache Management
# =============================================================================

def clear_all_caches() -> None:
    """Clear all Streamlit caches."""
    st.cache_data.clear()


def clear_realtime_caches() -> None:
    """Clear only realtime data caches."""
    # Note: Streamlit doesn't support selective cache clearing by TTL
    # This clears all caches; in production, consider using a more
    # sophisticated caching solution like Redis
    get_live_stats.clear()
    get_recent_events.clear()


def clear_experiment_caches() -> None:
    """Clear experiment-related caches."""
    get_experiment_stats.clear()
    get_available_runs.clear()
    get_run_assignment_count.clear()
    get_run_events.clear()
