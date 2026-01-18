"""
Test suite for Advanced Statistical Functions.

Tests verify:
1. SRM (Sample Ratio Mismatch) detection
2. Sequential testing boundaries
3. Bonferroni correction for multiple comparisons
4. Confidence interval calculations
"""
import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.stats import (
    check_srm,
    calculate_sequential_bounds,
    check_sequential_stopping,
    bonferroni_correction,
    calculate_confidence_interval,
    calculate_lift_confidence_interval
)


class TestSRMCheck:
    """Test suite for Sample Ratio Mismatch detection."""

    def test_no_srm_balanced_split(self):
        """50/50 split should not trigger SRM."""
        result = check_srm(1000, 1000)
        assert result["is_srm"] == False
        assert result["observed_ratio"] == 0.5
        assert result["p_value"] > 0.01

    def test_no_srm_slight_imbalance(self):
        """Small natural variance should not trigger SRM."""
        # 490/510 is within normal variance for n=1000
        result = check_srm(490, 510)
        assert result["is_srm"] == False
        assert result["p_value"] > 0.01

    def test_srm_detected_major_imbalance(self):
        """Significant imbalance should trigger SRM."""
        # 400/600 is a 40/60 split - clearly wrong
        result = check_srm(400, 600)
        assert result["is_srm"] == True
        assert result["p_value"] < 0.01
        assert "SRM detected" in result["message"]

    def test_srm_custom_ratio(self):
        """Should work with non-50/50 expected ratios."""
        # 70/30 split as expected
        result = check_srm(700, 300, expected_ratio=0.7)
        assert result["is_srm"] == False

        # 50/50 when expecting 70/30
        result = check_srm(500, 500, expected_ratio=0.7)
        assert result["is_srm"] == True

    def test_srm_empty_data(self):
        """Should handle empty data gracefully."""
        result = check_srm(0, 0)
        assert result["is_srm"] == False
        assert result["p_value"] == 1.0
        assert "No data" in result["message"]

    def test_srm_returns_all_fields(self):
        """Result should contain all expected fields."""
        result = check_srm(500, 500)
        assert "observed_ratio" in result
        assert "expected_ratio" in result
        assert "chi2" in result
        assert "p_value" in result
        assert "is_srm" in result
        assert "message" in result


class TestSequentialBounds:
    """Test suite for sequential testing boundary calculations."""

    def test_single_look(self):
        """Single look should return standard z-critical."""
        bounds = calculate_sequential_bounds(1, alpha=0.05)
        assert len(bounds) == 1
        # Standard two-tailed 95% critical value ~1.96
        assert 1.9 < bounds[0] < 2.0

    def test_obrien_fleming_decreasing(self):
        """O'Brien-Fleming bounds should decrease over time."""
        bounds = calculate_sequential_bounds(5, alpha=0.05, method="obrien_fleming")
        assert len(bounds) == 5
        # Early bounds should be higher (more conservative)
        for i in range(len(bounds) - 1):
            assert bounds[i] > bounds[i + 1]

    def test_pocock_equal_bounds(self):
        """Pocock bounds should be approximately equal."""
        bounds = calculate_sequential_bounds(5, alpha=0.05, method="pocock")
        assert len(bounds) == 5
        # All bounds should be roughly equal
        for b in bounds:
            assert abs(b - bounds[0]) < 0.01

    def test_obrien_fleming_first_look_strict(self):
        """First O'Brien-Fleming look should require very high z."""
        bounds = calculate_sequential_bounds(4, alpha=0.05, method="obrien_fleming")
        # First look at 25% info should need z > 3.9
        assert bounds[0] > 3.5

    def test_empty_looks(self):
        """Zero looks should return empty list."""
        bounds = calculate_sequential_bounds(0)
        assert bounds == []


class TestSequentialStopping:
    """Test suite for early stopping decisions."""

    def test_early_stop_strong_effect(self):
        """Very strong effect should allow early stopping."""
        # z=4.5 is very significant - should pass first look (~3.92 threshold)
        result = check_sequential_stopping(
            z_score=4.5,
            current_look=1,
            n_looks=4,
            method="obrien_fleming"
        )
        assert result["can_stop"] == True
        assert "Early stop" in result["message"]

    def test_continue_weak_effect(self):
        """Weak effect should require more data."""
        result = check_sequential_stopping(
            z_score=1.5,
            current_look=1,
            n_looks=4,
            method="obrien_fleming"
        )
        assert result["can_stop"] == False
        assert "Continue" in result["message"]

    def test_final_look_significant(self):
        """Final look with significant result."""
        result = check_sequential_stopping(
            z_score=2.2,
            current_look=4,
            n_looks=4,
            method="obrien_fleming"
        )
        # At final look, z=2.2 > ~1.96 should be significant
        assert result["can_stop"] == True

    def test_info_fraction_calculation(self):
        """Info fraction should be correctly calculated."""
        result = check_sequential_stopping(
            z_score=2.0,
            current_look=2,
            n_looks=4
        )
        assert result["info_fraction"] == 0.5

    def test_invalid_look_number(self):
        """Invalid look numbers should be handled."""
        result = check_sequential_stopping(
            z_score=2.0,
            current_look=0,
            n_looks=4
        )
        assert result["can_stop"] == False
        assert "Invalid" in result["message"]

        result = check_sequential_stopping(
            z_score=2.0,
            current_look=5,
            n_looks=4
        )
        assert result["can_stop"] == False


class TestBonferroniCorrection:
    """Test suite for multiple comparison correction."""

    def test_single_test_no_change(self):
        """Single test should keep original alpha."""
        result = bonferroni_correction([0.03], alpha=0.05)
        assert result["adjusted_alpha"] == 0.05
        assert result["n_tests"] == 1
        assert result["significant"] == [True]

    def test_multiple_tests_stricter_threshold(self):
        """Multiple tests should have stricter threshold."""
        result = bonferroni_correction([0.01, 0.02, 0.03], alpha=0.05)
        # 0.05 / 3 = 0.0167
        assert result["adjusted_alpha"] == pytest.approx(0.0167, rel=0.01)
        assert result["n_tests"] == 3
        # Only p=0.01 is significant with adjusted threshold
        assert result["significant"] == [True, False, False]
        assert result["n_significant"] == 1

    def test_no_significant_after_correction(self):
        """Marginal p-values may become non-significant."""
        # All p-values near 0.05 won't survive correction
        result = bonferroni_correction([0.04, 0.045, 0.05], alpha=0.05)
        assert result["any_significant"] == False
        assert result["n_significant"] == 0

    def test_all_significant_after_correction(self):
        """Very low p-values should remain significant."""
        result = bonferroni_correction([0.001, 0.002, 0.003], alpha=0.05)
        assert result["any_significant"] == True
        assert result["n_significant"] == 3

    def test_empty_list(self):
        """Empty p-value list should be handled."""
        result = bonferroni_correction([], alpha=0.05)
        assert result["n_tests"] == 0
        assert result["any_significant"] == False


class TestConfidenceInterval:
    """Test suite for confidence interval calculations."""

    def test_ci_contains_true_rate(self):
        """CI should contain the observed rate."""
        result = calculate_confidence_interval(0.10, 1000)
        assert result["lower"] <= 0.10 <= result["upper"]

    def test_ci_width_decreases_with_n(self):
        """Larger samples should have narrower CIs."""
        ci_small = calculate_confidence_interval(0.10, 100)
        ci_large = calculate_confidence_interval(0.10, 10000)

        width_small = ci_small["upper"] - ci_small["lower"]
        width_large = ci_large["upper"] - ci_large["lower"]

        assert width_large < width_small

    def test_ci_95_wider_than_90(self):
        """95% CI should be wider than 90% CI."""
        ci_95 = calculate_confidence_interval(0.10, 1000, confidence=0.95)
        ci_90 = calculate_confidence_interval(0.10, 1000, confidence=0.90)

        width_95 = ci_95["upper"] - ci_95["lower"]
        width_90 = ci_90["upper"] - ci_90["lower"]

        assert width_95 > width_90

    def test_ci_bounds_between_0_and_1(self):
        """CI bounds should be valid proportions."""
        # Test edge case: rate near 0
        result = calculate_confidence_interval(0.01, 100)
        assert result["lower"] >= 0
        assert result["upper"] <= 1

        # Test edge case: rate near 1
        result = calculate_confidence_interval(0.99, 100)
        assert result["lower"] >= 0
        assert result["upper"] <= 1

    def test_ci_zero_sample(self):
        """Zero sample size should return zeros."""
        result = calculate_confidence_interval(0.10, 0)
        assert result["lower"] == 0
        assert result["upper"] == 0


class TestLiftConfidenceInterval:
    """Test suite for lift CI calculations."""

    def test_significant_positive_lift(self):
        """Clear winner should have significant lift."""
        # Control 10%, Test 15% - clear improvement
        result = calculate_lift_confidence_interval(
            c_rate=0.10, c_n=1000,
            t_rate=0.15, t_n=1000
        )
        assert result["lift"] == pytest.approx(0.50, rel=0.01)  # 50% lift
        assert result["is_significant"] == True
        assert result["lower"] > 0  # Entire CI above 0

    def test_not_significant_small_lift(self):
        """Small difference should not be significant."""
        # Control 10%, Test 10.5% - too close
        result = calculate_lift_confidence_interval(
            c_rate=0.10, c_n=100,
            t_rate=0.105, t_n=100
        )
        assert result["is_significant"] == False

    def test_negative_lift(self):
        """Test worse than control should show negative lift."""
        # Need larger sample or bigger difference for CI to be entirely below 0
        result = calculate_lift_confidence_interval(
            c_rate=0.10, c_n=5000,
            t_rate=0.07, t_n=5000
        )
        assert result["lift"] < 0  # -30% lift
        assert result["upper"] < 0  # Entire CI below 0

    def test_zero_control_rate(self):
        """Zero control rate should be handled."""
        result = calculate_lift_confidence_interval(
            c_rate=0, c_n=1000,
            t_rate=0.10, t_n=1000
        )
        assert result["lift"] == 0
        assert result["is_significant"] == False

    def test_lift_ci_returns_all_fields(self):
        """Result should contain all expected fields."""
        result = calculate_lift_confidence_interval(
            c_rate=0.10, c_n=1000,
            t_rate=0.12, t_n=1000
        )
        assert "lift" in result
        assert "lower" in result
        assert "upper" in result
        assert "is_significant" in result


class TestStatisticalIntegration:
    """Integration tests combining multiple statistical functions."""

    def test_full_experiment_analysis(self):
        """Simulate complete experiment analysis workflow."""
        # Experiment data
        control_users, control_conv = 5000, 500  # 10% CVR
        test_users, test_conv = 5000, 600  # 12% CVR

        # 1. Check SRM
        srm = check_srm(control_users, test_users)
        assert srm["is_srm"] == False, "SRM check should pass for balanced split"

        # 2. Calculate lift CI
        c_rate = control_conv / control_users
        t_rate = test_conv / test_users
        lift_ci = calculate_lift_confidence_interval(c_rate, control_users, t_rate, test_users)
        assert lift_ci["lift"] == pytest.approx(0.20, rel=0.01)  # ~20% lift

        # 3. Sequential testing (simulate 2nd of 4 looks)
        from src.core.stats import calculate_statistics
        stats_result = calculate_statistics(control_users, control_conv, test_users, test_conv)
        seq = check_sequential_stopping(
            stats_result["z_score"],
            current_look=2,
            n_looks=4
        )
        # With 20% lift and 10k users, should be conclusive
        assert seq["z_score"] > 2  # Should be significant

    def test_guardrail_analysis_with_bonferroni(self):
        """Multiple guardrail metrics with correction."""
        # Simulate 3 guardrail p-values
        guardrail_pvalues = [0.001, 0.03, 0.08]

        correction = bonferroni_correction(guardrail_pvalues, alpha=0.05)

        # With Bonferroni, threshold is 0.05/3 = 0.0167
        # Only the first p-value (0.001) should be significant
        assert correction["significant"] == [True, False, False]
        assert correction["n_significant"] == 1
