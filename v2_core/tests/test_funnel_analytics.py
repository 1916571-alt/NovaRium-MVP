import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from apps.api.services.analytics import (
    compute_funnel_overview,
    list_simulation_templates,
    resolve_template_seed_preset,
    resolve_template_sql_challenges,
    resolve_template_steps,
    resolve_template_settings,
)


def test_compute_funnel_overview_basic():
    overview = compute_funnel_overview(
        [
            (0, "session_start", 1000),
            (1, "view_home", 900),
            (2, "view_detail", 700),
            (3, "click_cta", 420),
            (4, "add_to_cart", 320),
            (5, "start_checkout", 280),
            (6, "purchase", 220),
        ]
    )
    assert overview["total_users"] == 1000
    assert overview["bottleneck_step"] == "click_cta"
    assert len(overview["steps"]) == 7
    assert overview["steps"][0]["conversion_rate"] == 1.0
    assert overview["steps"][-1]["users_count"] == 220


def test_compute_funnel_overview_empty():
    overview = compute_funnel_overview([])
    assert overview["total_users"] == 0
    assert overview["bottleneck_step"] is None
    assert overview["steps"] == []


def test_simulation_templates_exist():
    items = list_simulation_templates()
    keys = {x["key"] for x in items}
    assert {"commerce", "content", "saas"}.issubset(keys)
    assert "preset_defaults" in items[0]


def test_resolve_template_settings_unknown_raises():
    with pytest.raises(ValueError):
        resolve_template_settings("unknown-template")


def test_resolve_template_steps_differs_by_template():
    commerce = resolve_template_steps("commerce")
    content = resolve_template_steps("content")
    saas = resolve_template_steps("saas")
    assert commerce != content
    assert commerce != saas
    assert content != saas
    assert commerce[0] == "session_start"
    assert content[-1] == "purchase"


def test_resolve_template_sql_challenges_has_items():
    items = resolve_template_sql_challenges("commerce")
    assert len(items) >= 1
    first = items[0]
    assert "title" in first
    assert "prompt_md" in first
    assert "expected_schema" in first
    assert "expected_metrics" in first


def test_resolve_template_seed_preset_changes_user_count():
    beginner = resolve_template_seed_preset("commerce", "beginner")
    standard = resolve_template_seed_preset("commerce", "standard")
    advanced = resolve_template_seed_preset("commerce", "advanced")
    assert beginner["user_count"] < standard["user_count"] < advanced["user_count"]
