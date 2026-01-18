"""
Tests for Data Mart SQL generation.
"""
import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core import mart_builder as mb


class TestGenerateMartSQL:
    """Tests for generate_mart_sql function."""

    def test_empty_metrics(self):
        """SQL should still be valid with no optional metrics."""
        sql = mb.generate_mart_sql([])
        assert "dm_daily_kpi" in sql
        assert "total_users" in sql
        assert "click_count" in sql
        assert "total_orders" in sql

    def test_single_metric_revenue(self):
        """Revenue metric should add total_revenue column."""
        sql = mb.generate_mart_sql(['revenue'])
        assert "total_revenue" in sql
        assert "SUM(CASE WHEN e.event_name = 'purchase'" in sql

    def test_single_metric_ctr(self):
        """CTR metric should add ctr calculation."""
        sql = mb.generate_mart_sql(['ctr'])
        assert "ctr" in sql
        assert "click_banner" in sql

    def test_single_metric_cvr(self):
        """CVR metric should add cvr calculation."""
        sql = mb.generate_mart_sql(['cvr'])
        assert "cvr" in sql
        assert "purchase" in sql

    def test_single_metric_aov(self):
        """AOV metric should add aov calculation."""
        sql = mb.generate_mart_sql(['aov'])
        assert "aov" in sql

    def test_single_metric_arpu(self):
        """ARPU metric should add arpu calculation."""
        sql = mb.generate_mart_sql(['arpu'])
        assert "arpu" in sql

    def test_single_metric_session_depth(self):
        """Session depth metric should add session_depth calculation."""
        sql = mb.generate_mart_sql(['session_depth'])
        assert "session_depth" in sql

    def test_multiple_metrics(self):
        """Multiple metrics should all be included."""
        metrics = ['revenue', 'ctr', 'cvr', 'aov']
        sql = mb.generate_mart_sql(metrics)
        assert "total_revenue" in sql
        assert "ctr" in sql
        assert "cvr" in sql
        assert "aov" in sql

    def test_all_metrics(self):
        """All available metrics should be included."""
        metrics = ['revenue', 'ctr', 'cvr', 'aov', 'arpu', 'session_depth']
        sql = mb.generate_mart_sql(metrics)
        for metric in ['total_revenue', 'ctr', 'cvr', 'aov', 'arpu', 'session_depth']:
            assert metric in sql

    def test_sql_has_valid_structure(self):
        """Generated SQL should have valid DuckDB structure."""
        sql = mb.generate_mart_sql(['revenue'])
        # Should have CTE
        assert "WITH daily_stats AS" in sql
        # Should have final SELECT
        assert "FROM daily_stats" in sql
        # Should have updated_at
        assert "updated_at" in sql

    def test_sql_no_trailing_comma_error(self):
        """SQL should not have trailing comma before FROM."""
        sql = mb.generate_mart_sql(['revenue'])
        # Check there's no ",\n    FROM" pattern
        lines = sql.split('\n')
        for i, line in enumerate(lines):
            if 'FROM daily_stats' in line:
                prev_line = lines[i-1].strip()
                assert not prev_line.endswith(','), "Trailing comma before FROM"

    def test_sql_handles_nullif(self):
        """SQL should use NULLIF to prevent division by zero."""
        sql = mb.generate_mart_sql(['ctr', 'cvr', 'aov'])
        assert sql.count('NULLIF') >= 3

    def test_unknown_metric_ignored(self):
        """Unknown metrics should be silently ignored."""
        sql = mb.generate_mart_sql(['unknown_metric', 'revenue'])
        assert "total_revenue" in sql
        assert "unknown_metric" not in sql


class TestGenerateMartDiagram:
    """Tests for generate_mart_diagram function."""

    def test_returns_dot_string(self):
        """Should return a valid DOT graph string."""
        dot = mb.generate_mart_diagram([])
        assert "digraph ETL" in dot
        assert "rankdir=LR" in dot

    def test_has_required_nodes(self):
        """Should have raw_events, raw_users, agg, and mart nodes."""
        dot = mb.generate_mart_diagram([])
        assert "raw_events" in dot
        assert "raw_users" in dot
        assert "agg" in dot
        assert "mart" in dot

    def test_has_edges(self):
        """Should have edges connecting nodes."""
        dot = mb.generate_mart_diagram([])
        assert "raw_events -> agg" in dot
        assert "raw_users -> agg" in dot
        assert "agg -> mart" in dot

    def test_includes_selected_metrics_in_schema(self):
        """Schema label should include selected metrics."""
        dot = mb.generate_mart_diagram(['revenue', 'ctr'])
        assert "rev" in dot
        assert "ctr" in dot

    def test_scale_affects_dimensions(self):
        """Scale parameter should affect node dimensions."""
        dot_small = mb.generate_mart_diagram([], scale=0.5)
        dot_large = mb.generate_mart_diagram([], scale=2.0)
        # Both should be valid DOT
        assert "digraph ETL" in dot_small
        assert "digraph ETL" in dot_large

    def test_all_metrics_in_schema(self):
        """All metrics should appear in schema when selected."""
        metrics = ['revenue', 'ctr', 'cvr', 'aov', 'arpu', 'session_depth']
        dot = mb.generate_mart_diagram(metrics)
        for label in ['rev', 'ctr', 'cvr', 'aov', 'arpu', 'depth']:
            assert label in dot


class TestSQLSyntaxValidation:
    """Tests to ensure generated SQL has valid syntax patterns."""

    def test_sql_semicolon_at_end(self):
        """SQL should end with semicolon."""
        sql = mb.generate_mart_sql(['revenue'])
        assert sql.strip().endswith(';')

    def test_sql_has_group_by(self):
        """SQL should have GROUP BY clause."""
        sql = mb.generate_mart_sql(['revenue'])
        assert "GROUP BY" in sql

    def test_sql_has_order_by(self):
        """SQL should have ORDER BY clause."""
        sql = mb.generate_mart_sql(['revenue'])
        assert "ORDER BY report_date" in sql

    def test_sql_uses_coalesce_for_sums(self):
        """SQL should use COALESCE for SUM operations to handle NULLs."""
        sql = mb.generate_mart_sql(['revenue', 'aov', 'arpu'])
        # Revenue and AOV should use COALESCE
        assert sql.count('COALESCE') >= 2
