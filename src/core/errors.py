"""
Custom exceptions for NovaRium Edu.

This module provides a hierarchy of exceptions for better error handling
across the application.
"""
from typing import Optional, Any


class NovariumError(Exception):
    """Base exception for all NovaRium errors."""

    def __init__(self, message: str, details: Optional[Any] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


# =============================================================================
# Database Errors
# =============================================================================

class DatabaseError(NovariumError):
    """Base exception for database-related errors."""
    pass


class ConnectionError(DatabaseError):
    """Raised when database connection fails."""
    pass


class QueryError(DatabaseError):
    """Raised when a SQL query fails."""

    def __init__(self, message: str, query: Optional[str] = None):
        self.query = query
        details = {"query": query[:100] + "..." if query and len(query) > 100 else query}
        super().__init__(message, details)


class LockError(DatabaseError):
    """Raised when database is locked by another process."""
    pass


# =============================================================================
# Validation Errors
# =============================================================================

class ValidationError(NovariumError):
    """Base exception for validation errors."""
    pass


class ParameterError(ValidationError):
    """Raised when a parameter value is invalid."""

    def __init__(self, param_name: str, value: Any, reason: str):
        self.param_name = param_name
        self.value = value
        self.reason = reason
        message = f"Invalid parameter '{param_name}': {reason}"
        super().__init__(message, {"param": param_name, "value": value})


class SampleSizeError(ValidationError):
    """Raised when sample size is insufficient."""

    def __init__(self, required: int, actual: int):
        self.required = required
        self.actual = actual
        message = f"Insufficient sample size: {actual} < {required} required"
        super().__init__(message, {"required": required, "actual": actual})


class DataError(ValidationError):
    """Raised when data format or content is invalid."""
    pass


# =============================================================================
# Experiment Errors
# =============================================================================

class ExperimentError(NovariumError):
    """Base exception for experiment-related errors."""
    pass


class ExperimentNotFoundError(ExperimentError):
    """Raised when an experiment cannot be found."""

    def __init__(self, experiment_id: str):
        self.experiment_id = experiment_id
        message = f"Experiment not found: {experiment_id}"
        super().__init__(message, {"experiment_id": experiment_id})


class ExperimentStateError(ExperimentError):
    """Raised when experiment is in an invalid state for the operation."""
    pass


class StatisticalError(ExperimentError):
    """Raised when statistical calculation fails."""
    pass


# =============================================================================
# API/Network Errors
# =============================================================================

class APIError(NovariumError):
    """Base exception for API-related errors."""
    pass


class TargetAppError(APIError):
    """Raised when Target App communication fails."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.status_code = status_code
        details = {"status_code": status_code} if status_code else None
        super().__init__(message, details)


class TimeoutError(APIError):
    """Raised when an API request times out."""
    pass


# =============================================================================
# Configuration Errors
# =============================================================================

class ConfigurationError(NovariumError):
    """Raised when configuration is missing or invalid."""
    pass
