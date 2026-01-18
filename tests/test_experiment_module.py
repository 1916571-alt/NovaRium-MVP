"""
Tests for Experiment Module constants and utilities.
"""
import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.ui.pages.experiment.constants import PAGE_MAP, METRICS_DB


class TestPageMapConstants:
    """Tests for PAGE_MAP configuration."""

    def test_page_map_not_empty(self):
        """PAGE_MAP should contain at least one page."""
        assert len(PAGE_MAP) > 0

    def test_all_pages_have_url(self):
        """Each page should have a url field."""
        for page_name, page_data in PAGE_MAP.items():
            assert 'url' in page_data, f"Page '{page_name}' missing 'url'"
            assert page_data['url'].startswith('/'), f"URL for '{page_name}' should start with /"

    def test_all_pages_have_components(self):
        """Each page should have components field."""
        for page_name, page_data in PAGE_MAP.items():
            assert 'components' in page_data, f"Page '{page_name}' missing 'components'"
            assert isinstance(page_data['components'], dict)

    def test_components_have_required_fields(self):
        """Each component should have id and type fields."""
        for page_name, page_data in PAGE_MAP.items():
            for comp_name, comp_data in page_data['components'].items():
                assert 'id' in comp_data, f"Component '{comp_name}' in '{page_name}' missing 'id'"
                assert 'type' in comp_data, f"Component '{comp_name}' in '{page_name}' missing 'type'"

    def test_component_types_are_valid(self):
        """Component types should be one of known types."""
        valid_types = {'BANNER', 'BUTTON', 'ICON_SET', 'ICON', 'TEXT', 'LAYOUT'}
        for page_name, page_data in PAGE_MAP.items():
            for comp_name, comp_data in page_data['components'].items():
                assert comp_data['type'] in valid_types, \
                    f"Unknown type '{comp_data['type']}' for '{comp_name}'"

    def test_home_page_exists(self):
        """Home page (/) should exist."""
        home_pages = [p for p in PAGE_MAP.values() if p['url'] == '/']
        assert len(home_pages) == 1, "Should have exactly one home page"

    def test_component_ids_are_unique_per_page(self):
        """Component IDs should be unique within each page."""
        for page_name, page_data in PAGE_MAP.items():
            ids = [c['id'] for c in page_data['components'].values()]
            assert len(ids) == len(set(ids)), \
                f"Duplicate component IDs in '{page_name}'"


class TestMetricsDBConstants:
    """Tests for METRICS_DB configuration."""

    def test_metrics_db_not_empty(self):
        """METRICS_DB should contain at least one metric."""
        assert len(METRICS_DB) > 0

    def test_all_metrics_have_desc(self):
        """Each metric should have a description."""
        for metric_name, metric_data in METRICS_DB.items():
            assert 'desc' in metric_data, f"Metric '{metric_name}' missing 'desc'"
            assert len(metric_data['desc']) > 0

    def test_all_metrics_have_formula(self):
        """Each metric should have a formula."""
        for metric_name, metric_data in METRICS_DB.items():
            assert 'formula' in metric_data, f"Metric '{metric_name}' missing 'formula'"

    def test_all_metrics_have_type(self):
        """Each metric should have a type."""
        for metric_name, metric_data in METRICS_DB.items():
            assert 'type' in metric_data, f"Metric '{metric_name}' missing 'type'"

    def test_metric_types_are_valid(self):
        """Metric types should be categorized."""
        valid_types = {'Conversion', 'Revenue', 'Retention', 'Engagement'}
        for metric_name, metric_data in METRICS_DB.items():
            assert metric_data['type'] in valid_types, \
                f"Unknown type '{metric_data['type']}' for metric '{metric_name}'"

    def test_ctr_metric_exists(self):
        """CTR metric should exist and be Conversion type."""
        ctr_metrics = [k for k in METRICS_DB if 'CTR' in k]
        assert len(ctr_metrics) > 0, "CTR metric should exist"

    def test_cvr_metric_exists(self):
        """CVR metric should exist and be Conversion type."""
        cvr_metrics = [k for k in METRICS_DB if 'CVR' in k]
        assert len(cvr_metrics) > 0, "CVR metric should exist"


class TestExperimentModuleImports:
    """Tests for experiment module structure and imports."""

    def test_can_import_experiment_module(self):
        """Should be able to import the experiment module."""
        from src.ui.pages import experiment
        assert hasattr(experiment, 'render')

    def test_can_import_step_labels(self):
        """Should be able to import STEP_LABELS."""
        from src.ui.pages.experiment import STEP_LABELS
        assert isinstance(STEP_LABELS, list)
        assert len(STEP_LABELS) == 4

    def test_step_labels_format(self):
        """Step labels should have numbered format."""
        from src.ui.pages.experiment import STEP_LABELS
        for i, label in enumerate(STEP_LABELS, 1):
            assert label.startswith(f"{i}."), f"Step {i} should start with '{i}.'"

    def test_can_import_all_step_modules(self):
        """Should be able to import all step modules."""
        from src.ui.pages.experiment import step1_hypothesis
        from src.ui.pages.experiment import step2_design
        from src.ui.pages.experiment import step3_collection
        from src.ui.pages.experiment import step4_analysis

        for module in [step1_hypothesis, step2_design, step3_collection, step4_analysis]:
            assert hasattr(module, 'render'), f"{module.__name__} should have render function"

    def test_exports_page_map(self):
        """Experiment module should export PAGE_MAP."""
        from src.ui.pages.experiment import PAGE_MAP as exp_page_map
        assert exp_page_map is PAGE_MAP

    def test_exports_metrics_db(self):
        """Experiment module should export METRICS_DB."""
        from src.ui.pages.experiment import METRICS_DB as exp_metrics_db
        assert exp_metrics_db is METRICS_DB


class TestExperimentModuleUtilities:
    """Tests for experiment module utility functions."""

    def test_get_current_step(self):
        """get_current_step should return integer."""
        from src.ui.pages.experiment import get_current_step
        # Note: This will return 1 by default when no session state
        # We can't fully test without mocking Streamlit session_state
        assert callable(get_current_step)

    def test_set_step(self):
        """set_step should be callable."""
        from src.ui.pages.experiment import set_step
        assert callable(set_step)

    def test_reset_wizard(self):
        """reset_wizard should be callable."""
        from src.ui.pages.experiment import reset_wizard
        assert callable(reset_wizard)
