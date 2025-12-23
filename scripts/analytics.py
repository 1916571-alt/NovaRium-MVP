import duckdb
import os
import hashlib
import numpy as np
import pandas as pd
from scipy import stats

# Constants (DB Path)
# Assuming this script is in scripts/ folder, so db is one level up
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'novarium_local.db')

def get_connection():
    """
    Establish a connection to the DuckDB database.
    """
    return duckdb.connect(DB_PATH)

def run_query(query, con):
    """
    Execute a SQL query and return the result as a DataFrame.
    Gracefully handles errors by returning string error message or empty DF.
    """
    try:
        return con.execute(query).df()
    except Exception as e:
        print(f"Query Error: {e}")
        return str(e)

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
