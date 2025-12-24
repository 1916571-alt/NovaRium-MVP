import pytest
import numpy as np
import sys
import os

# Add root to path to import src modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core import stats as al

def test_calculate_sample_size():
    # Baseline 10%, MDE 50% (Target 15%) -> Large effect, small sample
    # Baseline 10%, MDE 5% (Target 10.5%) -> Small effect, huge sample
    
    n_large_effect = al.calculate_sample_size(0.10, 0.50) # +50% lift
    n_small_effect = al.calculate_sample_size(0.10, 0.05) # +5% lift
    
    assert n_large_effect > 0
    assert n_small_effect > n_large_effect # Smaller effect requires more data
    
    # Border cases
    assert al.calculate_sample_size(0.5, 0) == 0 # No lift needed

def test_get_bucket():
    # Deterministic check
    # MD5("user_1") -> should always be same
    b1 = al.get_bucket("user_1")
    b2 = al.get_bucket("user_1")
    assert b1 == b2
    
    # Range check
    assert 0 <= b1 < 100
    
    # Different users, likely different buckets (collision possible but unlikely for this specific pair)
    b3 = al.get_bucket("user_2")
    assert isinstance(b3, int)

def test_calculate_statistics_significant():
    # Scenario: Clear Winner (10% vs 20% CVR, N=1000)
    c_users, c_conv = 1000, 100
    t_users, t_conv = 1000, 200
    
    stats = al.calculate_statistics(c_users, c_conv, t_users, t_conv)
    
    assert stats['control_rate'] == 0.1
    assert stats['test_rate'] == 0.2
    assert stats['lift'] == 1.0 # 100% lift
    assert stats['p_value'] < 0.05 # Should be significant

def test_calculate_statistics_insignificant():
    # Scenario: Tie (10% vs 10.1% CVR, N=1000) -> Noise
    c_users, c_conv = 1000, 100
    t_users, t_conv = 1000, 101
    
    stats = al.calculate_statistics(c_users, c_conv, t_users, t_conv)
    
    assert stats['p_value'] > 0.05 # Should not be significant

def test_format_delta():
    assert al.format_delta(0.12345) == "+12.35%"
    assert al.format_delta(-0.12345) == "-12.35%"
    assert al.format_delta(0.0001) == "+0.01%"

def test_calculate_retention_rate():
    # TDD Step 1: Define expectations first
    # Day 0: 100 users
    # Day 1: 40 users returned
    # Retention = 40%
    
    rate = al.calculate_retention_rate(100, 40)
    assert rate == 0.4
    
    # Border cases
    assert al.calculate_retention_rate(100, 0) == 0.0
    assert al.calculate_retention_rate(0, 0) == 0.0 # Divide by zero safety
