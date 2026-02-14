import os
import sys

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.api.routers import events as events_router
from apps.api.schemas.auth import CurrentUser
from apps.api.schemas.events import EventIngestBatchRequest, EventIngestItem


def test_events_ingest_router_success(monkeypatch):
    monkeypatch.setattr(events_router, "ensure_app_user", lambda user_id, email: None)
    monkeypatch.setattr(
        events_router,
        "ingest_events_for_user",
        lambda user_id, body: {
            "accepted_count": len(body.items),
            "duplicated_count": 0,
            "dropped_count": 0,
            "dropped_reasons": [],
        },
    )

    body = EventIngestBatchRequest(
        items=[
            EventIngestItem(
                project_id="00000000-0000-0000-0000-000000000010",
                user_key="u1",
                event_name="view_home",
            )
        ]
    )
    current_user = CurrentUser(
        user_id="00000000-0000-0000-0000-000000000001",
        email="u@example.com",
    )
    resp = events_router.ingest_events(body, current_user)
    assert resp.accepted_count == 1
    assert resp.duplicated_count == 0


def test_events_ingest_router_permission_denied(monkeypatch):
    monkeypatch.setattr(events_router, "ensure_app_user", lambda user_id, email: None)

    def _raise(*args, **kwargs):
        raise PermissionError("forbidden")

    monkeypatch.setattr(events_router, "ingest_events_for_user", _raise)

    body = EventIngestBatchRequest(
        items=[
            EventIngestItem(
                project_id="00000000-0000-0000-0000-000000000010",
                user_key="u1",
                event_name="view_home",
            )
        ]
    )
    current_user = CurrentUser(
        user_id="00000000-0000-0000-0000-000000000001",
        email="u@example.com",
    )
    with pytest.raises(HTTPException) as exc_info:
        events_router.ingest_events(body, current_user)

    assert exc_info.value.status_code == 403
    assert "forbidden" in str(exc_info.value.detail)
