import duckdb
import os
import hashlib
import numpy as np
import pandas as pd
from scipy import stats
import streamlit as st

# Constants (DB Path)
# Assuming this script is in src/core/ folder, so db is two levels up
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'novarium_local.db')

def get_connection():
    """
    Establish a connection to the DuckDB database.
    """
    return duckdb.connect(DB_PATH)

def run_query(query, con=None, max_retries=5, retry_delay=0.5):
    """
    Execute a SQL query and return the result as a DataFrame.
    Prioritizes Server API to avoid file locking, then falls back to direct access.
    """
    import time
    import requests
    
    if con:
        # If connection is provided, use it directly (no retry needed)
        try:
            return con.execute(query).df()
        except Exception as e:
            try:
                print(f"Query Error (Existing Conn): {repr(e)}")
            except:
                pass
            return pd.DataFrame()

    # 1. Try via Server API (Preferred)
    try:
        response = requests.post("http://localhost:8000/admin/execute_sql", json={"sql": query}, timeout=2)
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
            with duckdb.connect(DB_PATH, read_only=True) as conn:
                return conn.execute(query).df()
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check if it's a lock error
            if 'cannot open file' in error_msg or 'lock' in error_msg or 'access' in error_msg or 'process' in error_msg:
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = retry_delay * (2 ** attempt)
                    try:
                        print(f"[Stats] DB locked, retrying in {wait_time:.2f}s... (Attempt {attempt + 1}/{max_retries})")
                    except:
                        pass
                    time.sleep(wait_time)
                    continue
            
            # Non-lock error or final retry failed
            try:
                print(f"[Stats] Query failed: {repr(e)}")
            except:
                pass
            return pd.DataFrame()


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
