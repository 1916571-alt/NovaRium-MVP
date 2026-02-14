import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.api.services.sql_lab import grade_submission_result


def test_grade_submission_result_pass():
    result = {
        "columns": ["segment", "users"],
        "rows": [["A", 10], ["B", 20]],
        "row_count": 2,
        "truncated": False,
    }
    expected_schema = {"columns": ["segment", "users"]}
    expected_metrics = {"row_count": 2, "must_have_columns": ["users"]}

    ok, feedback = grade_submission_result(result, expected_schema, expected_metrics)
    assert ok is True
    assert feedback["status"] == "graded"
    assert all(check["ok"] for check in feedback["checks"])


def test_grade_submission_result_fail_on_missing_column():
    result = {
        "columns": ["segment"],
        "rows": [["A"], ["B"]],
        "row_count": 2,
        "truncated": False,
    }
    expected_schema = {}
    expected_metrics = {"must_have_columns": ["users"]}

    ok, feedback = grade_submission_result(result, expected_schema, expected_metrics)
    assert ok is False
    missing_check = next(
        c for c in feedback["checks"] if c["name"] == "metrics.must_have_columns"
    )
    assert missing_check["missing"] == ["users"]


def test_grade_submission_result_pending_when_no_rules():
    result = {"columns": ["x"], "rows": [[1]], "row_count": 1, "truncated": False}
    ok, feedback = grade_submission_result(result, {}, {})
    assert ok is False
    assert feedback["status"] == "pending_rules"
    assert feedback["checks"] == []


def test_grade_submission_result_expected_rows_unordered_with_tolerance():
    result = {
        "columns": ["segment", "rate"],
        "rows": [["B", 0.2002], ["A", 0.0999]],
        "row_count": 2,
        "truncated": False,
    }
    expected_schema = {}
    expected_metrics = {
        "unordered_rows": True,
        "numeric_tolerance": 0.001,
        "expected_rows": [
            {"segment": "A", "rate": 0.1},
            {"segment": "B", "rate": 0.2},
        ],
    }

    ok, feedback = grade_submission_result(result, expected_schema, expected_metrics)
    assert ok is True
    check = next(c for c in feedback["checks"] if c["name"] == "metrics.expected_rows")
    assert check["ok"] is True


def test_grade_submission_result_expected_rows_ordered_fail():
    result = {
        "columns": ["k", "v"],
        "rows": [["B", 2], ["A", 1]],
        "row_count": 2,
        "truncated": False,
    }
    expected_metrics = {
        "unordered_rows": False,
        "expected_rows": [
            {"k": "A", "v": 1},
            {"k": "B", "v": 2},
        ],
    }
    ok, feedback = grade_submission_result(result, {}, expected_metrics)
    assert ok is False
    check = next(c for c in feedback["checks"] if c["name"] == "metrics.expected_rows")
    assert check["ok"] is False
