"""
Tests for custom exception classes.
"""
import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

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


class TestNovariumError:
    """Tests for base NovariumError class."""

    def test_basic_error(self):
        error = NovariumError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details is None

    def test_error_with_details(self):
        error = NovariumError("Test error", details={"key": "value"})
        assert "Details:" in str(error)
        assert error.details == {"key": "value"}

    def test_is_exception(self):
        error = NovariumError("Test")
        assert isinstance(error, Exception)


class TestDatabaseErrors:
    """Tests for database-related exceptions."""

    def test_database_error_inheritance(self):
        error = DatabaseError("DB error")
        assert isinstance(error, NovariumError)

    def test_connection_error(self):
        error = ConnectionError("Failed to connect")
        assert isinstance(error, DatabaseError)
        assert "Failed to connect" in str(error)

    def test_query_error(self):
        query = "SELECT * FROM users WHERE id = 1"
        error = QueryError("Query failed", query=query)
        assert isinstance(error, DatabaseError)
        assert error.query == query
        assert "query" in error.details

    def test_query_error_truncates_long_query(self):
        long_query = "SELECT " + "x" * 200
        error = QueryError("Failed", query=long_query)
        assert len(error.details["query"]) <= 103  # 100 + "..."

    def test_lock_error(self):
        error = LockError("Database locked")
        assert isinstance(error, DatabaseError)


class TestValidationErrors:
    """Tests for validation-related exceptions."""

    def test_validation_error_inheritance(self):
        error = ValidationError("Invalid data")
        assert isinstance(error, NovariumError)

    def test_parameter_error(self):
        error = ParameterError("alpha", 1.5, "must be < 1")
        assert isinstance(error, ValidationError)
        assert error.param_name == "alpha"
        assert error.value == 1.5
        assert error.reason == "must be < 1"
        assert "alpha" in str(error)

    def test_sample_size_error(self):
        error = SampleSizeError(1000, 500)
        assert isinstance(error, ValidationError)
        assert error.required == 1000
        assert error.actual == 500
        assert "500 < 1000" in str(error)

    def test_data_error(self):
        error = DataError("Invalid data format")
        assert isinstance(error, ValidationError)


class TestExperimentErrors:
    """Tests for experiment-related exceptions."""

    def test_experiment_error_inheritance(self):
        error = ExperimentError("Experiment failed")
        assert isinstance(error, NovariumError)

    def test_experiment_not_found_error(self):
        error = ExperimentNotFoundError("exp_123")
        assert isinstance(error, ExperimentError)
        assert error.experiment_id == "exp_123"
        assert "exp_123" in str(error)

    def test_experiment_state_error(self):
        error = ExperimentStateError("Cannot start - already running")
        assert isinstance(error, ExperimentError)

    def test_statistical_error(self):
        error = StatisticalError("Division by zero in calculation")
        assert isinstance(error, ExperimentError)


class TestAPIErrors:
    """Tests for API-related exceptions."""

    def test_api_error_inheritance(self):
        error = APIError("API call failed")
        assert isinstance(error, NovariumError)

    def test_target_app_error(self):
        error = TargetAppError("Server unavailable", status_code=503)
        assert isinstance(error, APIError)
        assert error.status_code == 503
        assert error.details["status_code"] == 503

    def test_target_app_error_no_status(self):
        error = TargetAppError("Server unavailable")
        assert error.status_code is None
        assert error.details is None

    def test_timeout_error(self):
        error = TimeoutError("Request timed out")
        assert isinstance(error, APIError)


class TestConfigurationError:
    """Tests for configuration exceptions."""

    def test_configuration_error(self):
        error = ConfigurationError("Missing DATABASE_URL")
        assert isinstance(error, NovariumError)
        assert "DATABASE_URL" in str(error)


class TestExceptionHierarchy:
    """Tests for exception inheritance hierarchy."""

    def test_all_inherit_from_novarium_error(self):
        exceptions = [
            DatabaseError("test"),
            ConnectionError("test"),
            QueryError("test"),
            LockError("test"),
            ValidationError("test"),
            ParameterError("p", "v", "r"),
            SampleSizeError(100, 50),
            DataError("test"),
            ExperimentError("test"),
            ExperimentNotFoundError("id"),
            ExperimentStateError("test"),
            StatisticalError("test"),
            APIError("test"),
            TargetAppError("test"),
            TimeoutError("test"),
            ConfigurationError("test"),
        ]
        for exc in exceptions:
            assert isinstance(exc, NovariumError), f"{type(exc)} should inherit from NovariumError"

    def test_can_catch_by_base_class(self):
        """Verify that catching NovariumError catches all subclasses."""
        try:
            raise ParameterError("test", 1, "invalid")
        except NovariumError as e:
            assert isinstance(e, ParameterError)

    def test_specific_catch_before_general(self):
        """Verify specific exceptions can be caught separately."""
        try:
            raise QueryError("failed", "SELECT 1")
        except QueryError as e:
            assert e.query == "SELECT 1"
        except DatabaseError:
            pytest.fail("Should have caught QueryError, not DatabaseError")
