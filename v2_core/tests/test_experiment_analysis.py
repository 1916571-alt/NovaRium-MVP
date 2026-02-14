import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.api.services.experiment_analysis import calculate_ab_stats


def test_calculate_ab_stats_adopt():
    res = calculate_ab_stats(
        control_users=5000,
        control_conversions=500,  # 10%
        test_users=5000,
        test_conversions=650,  # 13%
    )
    assert res["lift"] > 0
    assert res["p_value"] < 0.05
    assert res["recommendation"] == "adopt"


def test_calculate_ab_stats_reject():
    res = calculate_ab_stats(
        control_users=5000,
        control_conversions=600,  # 12%
        test_users=5000,
        test_conversions=450,  # 9%
    )
    assert res["lift"] < 0
    assert res["p_value"] < 0.05
    assert res["recommendation"] == "reject"


def test_calculate_ab_stats_srm_invalid():
    res = calculate_ab_stats(
        control_users=9000,
        control_conversions=900,
        test_users=1000,
        test_conversions=100,
    )
    assert res["srm_detected"] is True
    assert res["recommendation"] == "invalid_srm"

