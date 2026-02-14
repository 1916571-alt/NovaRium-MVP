import os
import sys

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.api.schemas.events import EventIngestBatchRequest, EventIngestItem


def test_event_ingest_item_valid_minimal():
    row = EventIngestItem(
        project_id="00000000-0000-0000-0000-000000000010",
        user_key="user-1",
        event_name="view_home",
    )
    assert row.schema_version == "event-v1"
    assert row.source == "sdk"


def test_event_ingest_item_rejects_unknown_event_name():
    with pytest.raises(ValidationError):
        EventIngestItem(
            project_id="00000000-0000-0000-0000-000000000010",
            user_key="user-1",
            event_name="unknown_event",
        )


def test_event_ingest_item_rejects_blank_project_id():
    with pytest.raises(ValidationError):
        EventIngestItem(
            project_id="   ",
            user_key="user-1",
            event_name="view_home",
        )


def test_event_ingest_batch_requires_items():
    with pytest.raises(ValidationError):
        EventIngestBatchRequest(items=[])
