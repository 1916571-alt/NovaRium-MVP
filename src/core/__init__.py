"""
Core module for NovaRium Edu.

Provides statistics, validation, error handling, and logging utilities.
"""
from src.core.errors import (
    NovariumError,
    DatabaseError,
    ConnectionError,
    QueryError,
    LockError,
    ValidationError,
    ParameterError,
    SampleSizeError,
    DataError,
    ExperimentError,
    ExperimentNotFoundError,
    ExperimentStateError,
    StatisticalError,
    APIError,
    TargetAppError,
    TimeoutError,
    ConfigurationError,
)

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

from src.core.logging_config import (
    get_logger,
    log_exception,
    log_api_call,
    log_db_query,
    LogTimer,
)

__all__ = [
    # Errors
    "NovariumError",
    "DatabaseError",
    "ConnectionError",
    "QueryError",
    "LockError",
    "ValidationError",
    "ParameterError",
    "SampleSizeError",
    "DataError",
    "ExperimentError",
    "ExperimentNotFoundError",
    "ExperimentStateError",
    "StatisticalError",
    "APIError",
    "TargetAppError",
    "TimeoutError",
    "ConfigurationError",
    # Validators
    "validate_conversion_rate",
    "validate_mde",
    "validate_alpha",
    "validate_power",
    "validate_ab_test_params",
    "validate_sample_size",
    "validate_user_counts",
    "validate_traffic_split",
    "validate_experiment_name",
    "validate_metric_name",
    "validate_user_id",
    "validate_sql_identifier",
    # Logging
    "get_logger",
    "log_exception",
    "log_api_call",
    "log_db_query",
    "LogTimer",
]
