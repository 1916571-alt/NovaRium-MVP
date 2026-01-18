"""
Input validation functions for NovaRium Edu.

This module provides validation utilities for A/B test parameters,
experiment data, and user inputs.
"""
from typing import List, Optional, Any, Union
import re

from src.core.errors import ParameterError, SampleSizeError, DataError


# =============================================================================
# A/B Test Parameter Validators
# =============================================================================

def validate_conversion_rate(value: float, param_name: str = "conversion_rate") -> float:
    """
    Validate that a conversion rate is between 0 and 1 (exclusive).

    Args:
        value: The conversion rate to validate
        param_name: Name of the parameter for error messages

    Returns:
        The validated value

    Raises:
        ParameterError: If value is not in valid range
    """
    if not isinstance(value, (int, float)):
        raise ParameterError(param_name, value, "must be a number")

    if not 0 < value < 1:
        raise ParameterError(
            param_name, value,
            "must be between 0 and 1 (exclusive). Example: 0.10 for 10%"
        )

    return float(value)


def validate_mde(value: float, param_name: str = "mde") -> float:
    """
    Validate Minimum Detectable Effect (MDE).

    Args:
        value: The MDE value to validate (as a proportion, e.g., 0.05 for 5%)
        param_name: Name of the parameter for error messages

    Returns:
        The validated value

    Raises:
        ParameterError: If value is not positive or unreasonably large
    """
    if not isinstance(value, (int, float)):
        raise ParameterError(param_name, value, "must be a number")

    if value <= 0:
        raise ParameterError(param_name, value, "must be positive")

    if value > 1:
        raise ParameterError(
            param_name, value,
            "must be a proportion (e.g., 0.05 for 5% lift), not a percentage"
        )

    return float(value)


def validate_alpha(value: float, param_name: str = "alpha") -> float:
    """
    Validate significance level (alpha).

    Args:
        value: The alpha value to validate
        param_name: Name of the parameter for error messages

    Returns:
        The validated value

    Raises:
        ParameterError: If value is not in valid range
    """
    if not isinstance(value, (int, float)):
        raise ParameterError(param_name, value, "must be a number")

    if not 0 < value < 0.5:
        raise ParameterError(
            param_name, value,
            "must be between 0 and 0.5. Common values: 0.05, 0.01, 0.10"
        )

    return float(value)


def validate_power(value: float, param_name: str = "power") -> float:
    """
    Validate statistical power.

    Args:
        value: The power value to validate
        param_name: Name of the parameter for error messages

    Returns:
        The validated value

    Raises:
        ParameterError: If value is not in valid range
    """
    if not isinstance(value, (int, float)):
        raise ParameterError(param_name, value, "must be a number")

    if not 0.5 <= value < 1:
        raise ParameterError(
            param_name, value,
            "must be between 0.5 and 1 (exclusive). Common values: 0.80, 0.90"
        )

    return float(value)


def validate_ab_test_params(
    baseline_cvr: float,
    mde: float,
    alpha: float = 0.05,
    power: float = 0.8
) -> dict:
    """
    Validate all A/B test parameters at once.

    Args:
        baseline_cvr: Baseline conversion rate
        mde: Minimum detectable effect
        alpha: Significance level
        power: Statistical power

    Returns:
        Dictionary of validated parameters

    Raises:
        ParameterError: If any parameter is invalid
    """
    return {
        "baseline_cvr": validate_conversion_rate(baseline_cvr, "baseline_cvr"),
        "mde": validate_mde(mde, "mde"),
        "alpha": validate_alpha(alpha, "alpha"),
        "power": validate_power(power, "power")
    }


# =============================================================================
# Sample Size Validators
# =============================================================================

def validate_sample_size(
    required: int,
    actual: int,
    min_threshold: int = 100
) -> bool:
    """
    Validate that sample size meets requirements.

    Args:
        required: Required sample size from power analysis
        actual: Actual sample size collected
        min_threshold: Absolute minimum sample size

    Returns:
        True if valid

    Raises:
        SampleSizeError: If sample size is insufficient
    """
    if actual < min_threshold:
        raise SampleSizeError(min_threshold, actual)

    if actual < required:
        raise SampleSizeError(required, actual)

    return True


def validate_user_counts(
    control_users: int,
    test_users: int,
    control_conversions: int,
    test_conversions: int
) -> dict:
    """
    Validate experiment user counts and conversions.

    Args:
        control_users: Number of users in control group
        test_users: Number of users in test group
        control_conversions: Conversions in control group
        test_conversions: Conversions in test group

    Returns:
        Dictionary of validated counts

    Raises:
        ParameterError: If any count is invalid
        DataError: If conversions exceed users
    """
    for name, value in [
        ("control_users", control_users),
        ("test_users", test_users),
        ("control_conversions", control_conversions),
        ("test_conversions", test_conversions)
    ]:
        if not isinstance(value, int) or value < 0:
            raise ParameterError(name, value, "must be a non-negative integer")

    if control_conversions > control_users:
        raise DataError(
            f"Control conversions ({control_conversions}) exceeds "
            f"control users ({control_users})"
        )

    if test_conversions > test_users:
        raise DataError(
            f"Test conversions ({test_conversions}) exceeds "
            f"test users ({test_users})"
        )

    return {
        "control_users": control_users,
        "test_users": test_users,
        "control_conversions": control_conversions,
        "test_conversions": test_conversions
    }


# =============================================================================
# Experiment Configuration Validators
# =============================================================================

def validate_traffic_split(value: float, param_name: str = "traffic_split") -> float:
    """
    Validate traffic split ratio.

    Args:
        value: Traffic split ratio (0 to 1, where 0.5 means 50/50)
        param_name: Name of the parameter for error messages

    Returns:
        The validated value

    Raises:
        ParameterError: If value is not in valid range
    """
    if not isinstance(value, (int, float)):
        raise ParameterError(param_name, value, "must be a number")

    if not 0 < value < 1:
        raise ParameterError(
            param_name, value,
            "must be between 0 and 1 (exclusive). Example: 0.5 for 50/50 split"
        )

    return float(value)


def validate_experiment_name(value: str, param_name: str = "experiment_name") -> str:
    """
    Validate experiment name/hypothesis.

    Args:
        value: The experiment name or hypothesis
        param_name: Name of the parameter for error messages

    Returns:
        The validated and stripped value

    Raises:
        ParameterError: If value is empty or too long
    """
    if not isinstance(value, str):
        raise ParameterError(param_name, value, "must be a string")

    value = value.strip()

    if not value:
        raise ParameterError(param_name, value, "cannot be empty")

    if len(value) > 500:
        raise ParameterError(param_name, value, "must be 500 characters or less")

    return value


def validate_metric_name(value: str, allowed_metrics: Optional[List[str]] = None) -> str:
    """
    Validate metric name.

    Args:
        value: The metric name
        allowed_metrics: Optional list of allowed metric names

    Returns:
        The validated metric name

    Raises:
        ParameterError: If metric is invalid or not in allowed list
    """
    if not isinstance(value, str):
        raise ParameterError("metric", value, "must be a string")

    value = value.strip().lower()

    if not value:
        raise ParameterError("metric", value, "cannot be empty")

    if allowed_metrics and value not in allowed_metrics:
        raise ParameterError(
            "metric", value,
            f"must be one of: {', '.join(allowed_metrics)}"
        )

    return value


# =============================================================================
# Data Validators
# =============================================================================

def validate_user_id(value: Union[str, int], param_name: str = "user_id") -> str:
    """
    Validate user ID format.

    Args:
        value: The user ID
        param_name: Name of the parameter for error messages

    Returns:
        The validated user ID as string

    Raises:
        ParameterError: If user ID is invalid
    """
    value = str(value).strip()

    if not value:
        raise ParameterError(param_name, value, "cannot be empty")

    if len(value) > 255:
        raise ParameterError(param_name, value, "must be 255 characters or less")

    return value


def validate_sql_identifier(value: str, param_name: str = "identifier") -> str:
    """
    Validate SQL identifier (table name, column name) to prevent injection.

    Args:
        value: The identifier to validate
        param_name: Name of the parameter for error messages

    Returns:
        The validated identifier

    Raises:
        ParameterError: If identifier contains invalid characters
    """
    if not isinstance(value, str):
        raise ParameterError(param_name, value, "must be a string")

    value = value.strip()

    if not value:
        raise ParameterError(param_name, value, "cannot be empty")

    # Only allow alphanumeric and underscore
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', value):
        raise ParameterError(
            param_name, value,
            "must start with a letter or underscore, "
            "and contain only letters, numbers, and underscores"
        )

    if len(value) > 64:
        raise ParameterError(param_name, value, "must be 64 characters or less")

    return value
