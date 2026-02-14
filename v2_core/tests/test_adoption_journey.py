import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.api.services.adoptions import build_adoption_patch, merge_state


def test_merge_state_nested():
    current = {
        "features": {
            "experiment:1": {"variant": "A", "traffic_percentage": 100.0},
            "experiment:2": {"variant": "B", "traffic_percentage": 50.0},
        },
        "theme": "default",
    }
    patch = {
        "features": {"experiment:1": {"variant": "B", "traffic_percentage": 20.0}},
        "badge": "shipper",
    }

    merged = merge_state(current, patch)
    assert merged["features"]["experiment:1"]["variant"] == "B"
    assert merged["features"]["experiment:2"]["variant"] == "B"
    assert merged["badge"] == "shipper"
    assert merged["theme"] == "default"


def test_build_adoption_patch_shape():
    adoption = {
        "id": 7,
        "experiment_id": "exp-123",
        "winning_variant_key": "B",
        "traffic_percentage": 42.0,
    }
    patch = build_adoption_patch(adoption)
    feature_key = "experiment:exp-123"
    assert "features" in patch
    assert patch["features"][feature_key]["variant"] == "B"
    assert patch["features"][feature_key]["traffic_percentage"] == 42.0
    assert patch["features"][feature_key]["adoption_id"] == 7

