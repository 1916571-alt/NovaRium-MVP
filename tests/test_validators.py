"""
Tests for input validation functions.
"""
import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.validators import (
    validate_conversion_rate,
    validate_mde,
    validate_alpha,
    validate_power,
    validate_ab_test_params,
    validate_sample_size,
    validate_user_counts,
    validate_traffic_split,
    validate_experiment_name,
    validate_metric_name,
    validate_user_id,
    validate_sql_identifier,
)
from src.core.errors import ParameterError, SampleSizeError, DataError


class TestValidateConversionRate:
    """Tests for validate_conversion_rate function."""

    def test_valid_conversion_rate(self):
        assert validate_conversion_rate(0.1) == 0.1
        assert validate_conversion_rate(0.5) == 0.5
        assert validate_conversion_rate(0.99) == 0.99

    def test_boundary_values_invalid(self):
        with pytest.raises(ParameterError):
            validate_conversion_rate(0)
        with pytest.raises(ParameterError):
            validate_conversion_rate(1)

    def test_negative_value(self):
        with pytest.raises(ParameterError):
            validate_conversion_rate(-0.1)

    def test_non_numeric_value(self):
        with pytest.raises(ParameterError):
            validate_conversion_rate("0.1")


class TestValidateMDE:
    """Tests for validate_mde function."""

    def test_valid_mde(self):
        assert validate_mde(0.05) == 0.05
        assert validate_mde(0.1) == 0.1
        assert validate_mde(0.5) == 0.5

    def test_zero_mde(self):
        with pytest.raises(ParameterError):
            validate_mde(0)

    def test_negative_mde(self):
        with pytest.raises(ParameterError):
            validate_mde(-0.1)

    def test_mde_greater_than_one(self):
        with pytest.raises(ParameterError):
            validate_mde(1.5)  # Should be proportion, not percentage


class TestValidateAlpha:
    """Tests for validate_alpha function."""

    def test_valid_alpha(self):
        assert validate_alpha(0.05) == 0.05
        assert validate_alpha(0.01) == 0.01
        assert validate_alpha(0.1) == 0.1

    def test_alpha_boundary_invalid(self):
        with pytest.raises(ParameterError):
            validate_alpha(0)
        with pytest.raises(ParameterError):
            validate_alpha(0.5)  # Too high

    def test_alpha_too_high(self):
        with pytest.raises(ParameterError):
            validate_alpha(0.6)


class TestValidatePower:
    """Tests for validate_power function."""

    def test_valid_power(self):
        assert validate_power(0.8) == 0.8
        assert validate_power(0.9) == 0.9
        assert validate_power(0.5) == 0.5

    def test_power_boundary_invalid(self):
        with pytest.raises(ParameterError):
            validate_power(0.4)  # Too low
        with pytest.raises(ParameterError):
            validate_power(1.0)  # Cannot be 100%


class TestValidateABTestParams:
    """Tests for validate_ab_test_params function."""

    def test_valid_params(self):
        result = validate_ab_test_params(0.1, 0.05, 0.05, 0.8)
        assert result["baseline_cvr"] == 0.1
        assert result["mde"] == 0.05
        assert result["alpha"] == 0.05
        assert result["power"] == 0.8

    def test_default_params(self):
        result = validate_ab_test_params(0.1, 0.05)
        assert result["alpha"] == 0.05
        assert result["power"] == 0.8

    def test_invalid_baseline_raises(self):
        with pytest.raises(ParameterError):
            validate_ab_test_params(0, 0.05)  # Invalid baseline

    def test_invalid_mde_raises(self):
        with pytest.raises(ParameterError):
            validate_ab_test_params(0.1, 0)  # Invalid MDE


class TestValidateSampleSize:
    """Tests for validate_sample_size function."""

    def test_sufficient_sample(self):
        assert validate_sample_size(1000, 1500) is True

    def test_exact_sample(self):
        assert validate_sample_size(1000, 1000) is True

    def test_insufficient_sample(self):
        with pytest.raises(SampleSizeError) as exc_info:
            validate_sample_size(1000, 500)
        assert exc_info.value.required == 1000
        assert exc_info.value.actual == 500

    def test_below_min_threshold(self):
        with pytest.raises(SampleSizeError):
            validate_sample_size(50, 50, min_threshold=100)


class TestValidateUserCounts:
    """Tests for validate_user_counts function."""

    def test_valid_counts(self):
        result = validate_user_counts(1000, 1000, 100, 120)
        assert result["control_users"] == 1000
        assert result["test_users"] == 1000
        assert result["control_conversions"] == 100
        assert result["test_conversions"] == 120

    def test_conversions_exceed_users(self):
        with pytest.raises(DataError):
            validate_user_counts(100, 100, 150, 50)  # Control conversions > users

        with pytest.raises(DataError):
            validate_user_counts(100, 100, 50, 150)  # Test conversions > users

    def test_negative_values(self):
        with pytest.raises(ParameterError):
            validate_user_counts(-100, 100, 50, 50)


class TestValidateTrafficSplit:
    """Tests for validate_traffic_split function."""

    def test_valid_split(self):
        assert validate_traffic_split(0.5) == 0.5
        assert validate_traffic_split(0.3) == 0.3
        assert validate_traffic_split(0.7) == 0.7

    def test_boundary_invalid(self):
        with pytest.raises(ParameterError):
            validate_traffic_split(0)
        with pytest.raises(ParameterError):
            validate_traffic_split(1)


class TestValidateExperimentName:
    """Tests for validate_experiment_name function."""

    def test_valid_name(self):
        assert validate_experiment_name("Test hypothesis") == "Test hypothesis"

    def test_strips_whitespace(self):
        assert validate_experiment_name("  Test  ") == "Test"

    def test_empty_name(self):
        with pytest.raises(ParameterError):
            validate_experiment_name("")
        with pytest.raises(ParameterError):
            validate_experiment_name("   ")

    def test_too_long_name(self):
        with pytest.raises(ParameterError):
            validate_experiment_name("x" * 501)


class TestValidateMetricName:
    """Tests for validate_metric_name function."""

    def test_valid_metric(self):
        assert validate_metric_name("CTR") == "ctr"  # Lowercased

    def test_metric_with_allowed_list(self):
        allowed = ["ctr", "cvr", "aov"]
        assert validate_metric_name("CTR", allowed) == "ctr"

    def test_metric_not_in_allowed(self):
        allowed = ["ctr", "cvr"]
        with pytest.raises(ParameterError):
            validate_metric_name("aov", allowed)

    def test_empty_metric(self):
        with pytest.raises(ParameterError):
            validate_metric_name("")


class TestValidateUserId:
    """Tests for validate_user_id function."""

    def test_valid_string_id(self):
        assert validate_user_id("user_123") == "user_123"

    def test_valid_numeric_id(self):
        assert validate_user_id(12345) == "12345"

    def test_empty_id(self):
        with pytest.raises(ParameterError):
            validate_user_id("")

    def test_too_long_id(self):
        with pytest.raises(ParameterError):
            validate_user_id("x" * 256)


class TestValidateSqlIdentifier:
    """Tests for validate_sql_identifier function."""

    def test_valid_identifier(self):
        assert validate_sql_identifier("table_name") == "table_name"
        assert validate_sql_identifier("_private") == "_private"
        assert validate_sql_identifier("Column1") == "Column1"

    def test_identifier_with_numbers(self):
        assert validate_sql_identifier("table_1") == "table_1"

    def test_invalid_start_with_number(self):
        with pytest.raises(ParameterError):
            validate_sql_identifier("1table")

    def test_invalid_special_chars(self):
        with pytest.raises(ParameterError):
            validate_sql_identifier("table-name")
        with pytest.raises(ParameterError):
            validate_sql_identifier("table name")
        with pytest.raises(ParameterError):
            validate_sql_identifier("table;drop")

    def test_sql_injection_prevention(self):
        with pytest.raises(ParameterError):
            validate_sql_identifier("users; DROP TABLE users;--")

    def test_empty_identifier(self):
        with pytest.raises(ParameterError):
            validate_sql_identifier("")

    def test_too_long_identifier(self):
        with pytest.raises(ParameterError):
            validate_sql_identifier("x" * 65)
