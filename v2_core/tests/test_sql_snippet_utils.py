import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.api.services.sql_lab import normalize_snippet_tags


def test_normalize_snippet_tags_filters_and_deduplicates():
    tags = [" Analysis ", "analysis", "A/B", "funnel_1", "valid-tag", "bad tag"]
    assert normalize_snippet_tags(tags) == ["analysis", "funnel_1", "valid-tag"]


def test_normalize_snippet_tags_limit_10():
    tags = [f"t{i}" for i in range(20)]
    out = normalize_snippet_tags(tags)
    assert len(out) == 10
    assert out[0] == "t0"
    assert out[-1] == "t9"
