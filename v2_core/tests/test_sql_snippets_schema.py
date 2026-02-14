import os
import sys

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.api.schemas.sql_lab import SqlSnippetUpdateRequest


def test_sql_snippet_update_requires_any_field():
    with pytest.raises(ValidationError):
        SqlSnippetUpdateRequest()


def test_sql_snippet_update_accepts_title_only():
    req = SqlSnippetUpdateRequest(title="rename")
    assert req.title == "rename"
    assert req.sql_text is None


def test_sql_snippet_update_accepts_sql_only():
    req = SqlSnippetUpdateRequest(sql_text="select 1")
    assert req.title is None
    assert req.sql_text == "select 1"


def test_sql_snippet_update_accepts_tags_only():
    req = SqlSnippetUpdateRequest(tags=["analysis", "funnel"])
    assert req.title is None
    assert req.sql_text is None
    assert req.tags == ["analysis", "funnel"]


def test_sql_snippet_update_accepts_pin_only():
    req = SqlSnippetUpdateRequest(is_pinned=True)
    assert req.is_pinned is True
