import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.api.services.scenarios import (
    _build_share_token,
    _verify_share_token,
    adapt_v1_payload_to_v2,
    adapt_v2_payload_to_v1,
    normalize_import_payload,
    normalize_import_payload_by_version,
    validate_scenario_pack_payload,
)


def test_normalize_import_payload_accepts_minimal_shape():
    out = normalize_import_payload({})
    assert out["experiments"] == []
    assert out["sql_challenges"] == []
    assert out["feature_states"] == []
    assert out["community_posts"] == []


def test_normalize_import_payload_rejects_invalid_top_level_types():
    with pytest.raises(ValueError):
        normalize_import_payload({"experiments": {}})


def test_normalize_import_payload_clamps_variant_weight_and_defaults():
    out = normalize_import_payload(
        {
            "experiments": [
                {
                    "hypothesis": "",
                    "primary_metric": "",
                    "guardrail_metrics": ["a"],
                    "variants": [
                        {"variant_key": "%%%bad", "traffic_weight": 999, "config_json": []}
                    ],
                }
            ]
        }
    )
    exp = out["experiments"][0]
    assert exp["hypothesis"] == "Imported hypothesis"
    assert exp["primary_metric"] == "purchase_conversion"
    assert exp["variants"][0]["variant_key"] == "variant"
    assert exp["variants"][0]["traffic_weight"] == 100.0
    assert exp["variants"][0]["config_json"] == {}


def test_normalize_import_payload_rejects_too_many_experiments():
    with pytest.raises(ValueError):
        normalize_import_payload({"experiments": [{} for _ in range(201)]})


def test_normalize_import_payload_by_version_rejects_unsupported():
    with pytest.raises(ValueError):
        normalize_import_payload_by_version("scenario-pack-v999", {})


def test_adapt_v2_payload_to_v1_maps_mixed_keys():
    payload_v2 = {
        "data": {
            "experiments": [
                {
                    "id": "exp_1",
                    "hypothesis": "H",
                    "metrics": {"primary": "purchase_conversion", "guardrails": ["bounce_rate"]},
                    "variants": [
                        {"key": "control", "config": {"label": "A"}, "weight": 50},
                        {"key": "test", "config": {"label": "B"}, "weight": 50},
                    ],
                }
            ],
            "sqlChallenges": [
                {
                    "title": "Q1",
                    "prompt": "write sql",
                    "difficulty": "easy",
                    "expectedSchema": {"columns": ["c1"]},
                    "expectedMetrics": {"row_count": 1},
                }
            ],
            "featureStates": [{"key": "hero", "state": {"headline": "X"}}],
            "communityPosts": [{"title": "post", "body": "why", "tags": ["sql"]}],
        }
    }
    out = adapt_v2_payload_to_v1(payload_v2)
    assert out["experiments"][0]["source_experiment_id"] == "exp_1"
    assert out["experiments"][0]["variants"][0]["variant_key"] == "control"
    assert out["sql_challenges"][0]["prompt_md"] == "write sql"
    assert out["feature_states"][0]["feature_key"] == "hero"
    assert out["community_posts"][0]["body_md"] == "why"


def test_normalize_import_payload_by_version_accepts_v2():
    out = normalize_import_payload_by_version(
        "scenario-pack-v2",
        {
            "data": {
                "experiments": [{"variants": [{"key": "x", "weight": 200}]}],
            }
        },
    )
    assert out["experiments"][0]["variants"][0]["variant_key"] == "x"
    assert out["experiments"][0]["variants"][0]["traffic_weight"] == 100.0


def test_validate_scenario_pack_payload_returns_counts():
    out = validate_scenario_pack_payload(
        "scenario-pack-v1",
        {
            "experiments": [{"variants": [{"variant_key": "a"}, {"variant_key": "b"}]}],
            "sql_challenges": [{}],
            "feature_states": [{}, {}],
            "community_posts": [{}],
        },
    )
    assert out["accepted_schema_version"] == "scenario-pack-v1"
    assert out["normalized_counts"]["experiments"] == 1
    assert out["normalized_counts"]["variants"] == 2
    assert out["normalized_counts"]["sql_challenges"] == 1


def test_adapt_v1_payload_to_v2_roundtrip_import_normalization():
    v1 = {
        "experiments": [
            {
                "source_experiment_id": "e1",
                "hypothesis": "H",
                "primary_metric": "purchase_conversion",
                "guardrail_metrics": ["bounce_rate"],
                "variants": [{"variant_key": "control", "config_json": {}, "traffic_weight": 50}],
            }
        ],
        "sql_challenges": [{"title": "q", "prompt_md": "p", "difficulty": "easy"}],
        "feature_states": [{"feature_key": "hero", "state_json": {"a": 1}}],
        "community_posts": [{"title": "t", "body_md": "b", "tags": ["x"]}],
    }
    v2 = adapt_v1_payload_to_v2(v1)
    out = normalize_import_payload_by_version("scenario-pack-v2", v2)
    assert out["experiments"][0]["source_experiment_id"] == "e1"
    assert out["sql_challenges"][0]["title"] == "q"
    assert out["feature_states"][0]["feature_key"] == "hero"


def test_validate_scenario_pack_payload_emits_warnings_for_clamp_and_truncate():
    out = validate_scenario_pack_payload(
        "scenario-pack-v1",
        {
            "experiments": [
                {
                    "hypothesis": "x" * 5000,
                    "variants": [{"variant_key": "%%%bad", "traffic_weight": 999}],
                }
            ],
            "community_posts": [{"title": "t" * 500, "body_md": "b" * 21000}],
        },
    )
    joined = "\n".join(out["warnings"])
    assert "traffic_weight is clamped" in joined
    assert "hypothesis is truncated" in joined
    assert "community_posts.body_md is truncated" in joined


def test_validate_scenario_pack_payload_emits_tag_normalization_drop_counts():
    out = validate_scenario_pack_payload(
        "scenario-pack-v1",
        {
            "community_posts": [
                {
                    "title": "tag test",
                    "body_md": "body",
                    "tags": [
                        " TagA ",
                        "taga",
                        "",
                        "X" * 40,
                        "b",
                        "c",
                        "d",
                        "e",
                        "f",
                        "g",
                        "h",
                        "i",
                        "j",
                    ],
                },
                {
                    "title": "bad tags",
                    "body_md": "body2",
                    "tags": "not-a-list",
                },
            ]
        },
    )
    joined = "\n".join(out["warnings"])
    assert "normalized by trim/lowercase" in joined
    assert "duplicates are dropped" in joined
    assert "empty items are dropped" in joined
    assert "overflow items are dropped" in joined
    assert "items are truncated to 24 chars" in joined
    assert "non-list replaced with empty list" in joined


def test_share_token_build_verify_roundtrip():
    token = _build_share_token("00000000-0000-0000-0000-000000000001")
    share_id = _verify_share_token(token)
    assert share_id == "00000000-0000-0000-0000-000000000001"
