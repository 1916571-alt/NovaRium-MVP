import os
import sys

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.api.schemas.experiments import VariantUpdateRequest


def test_variant_update_requires_any_field():
    with pytest.raises(ValidationError):
        VariantUpdateRequest()


def test_variant_update_accepts_weight_only():
    req = VariantUpdateRequest(traffic_weight=33.3)
    assert req.traffic_weight == 33.3
    assert req.config_json is None


def test_variant_update_accepts_config_only():
    req = VariantUpdateRequest(config_json={"label": "B"})
    assert req.config_json == {"label": "B"}
    assert req.traffic_weight is None
