import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.api.services.community import compute_rank_score, normalize_tags


def test_normalize_tags_filters_and_deduplicates():
    tags = [
        " SQL ",
        "sql",
        "A/B",
        "growth_hacking",
        "veryveryveryveryveryverylongtag",
        "pm",
        "pm",
        "valid-tag",
    ]
    out = normalize_tags(tags)
    assert out == ["sql", "growth_hacking", "pm", "valid-tag"]


def test_normalize_tags_limit_10():
    tags = [f"t{i}" for i in range(20)]
    out = normalize_tags(tags)
    assert len(out) == 10
    assert out[0] == "t0"
    assert out[-1] == "t9"


def test_compute_rank_score_prefers_forks_and_comments():
    base = compute_rank_score(comment_count=0, fork_count=0, age_hours=1)
    with_comments = compute_rank_score(comment_count=2, fork_count=0, age_hours=1)
    with_forks = compute_rank_score(comment_count=0, fork_count=1, age_hours=1)
    one_comment = compute_rank_score(comment_count=1, fork_count=0, age_hours=1)
    assert with_comments > base
    assert with_forks > one_comment


def test_compute_rank_score_decays_with_age():
    fresh = compute_rank_score(comment_count=1, fork_count=1, age_hours=1)
    old = compute_rank_score(comment_count=1, fork_count=1, age_hours=100)
    assert fresh > old
