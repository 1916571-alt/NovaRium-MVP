import os
import sys

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.api.routers import scenarios as scenarios_router
from apps.api.schemas.auth import CurrentUser
from apps.api.schemas.scenarios import ScenarioImportRequest


def test_scenario_export_router_success(monkeypatch):
    monkeypatch.setattr(scenarios_router, "ensure_app_user", lambda user_id, email: None)
    monkeypatch.setattr(
        scenarios_router,
        "export_scenario_pack_for_user",
        lambda user_id, project_id, schema_version=None: {
            "schema_version": "scenario-pack-v1",
            "exported_at": "2026-02-13T00:00:00",
            "source_project_id": project_id,
            "source_project_name": "Demo",
            "payload": {"experiments": []},
        },
    )

    current_user = CurrentUser(
        user_id="00000000-0000-0000-0000-000000000001",
        email="u@example.com",
    )
    resp = scenarios_router.export_scenario_pack("p1", None, current_user)
    assert resp.schema_version == "scenario-pack-v1"
    assert resp.source_project_id == "p1"


def test_scenario_export_router_supports_v2(monkeypatch):
    monkeypatch.setattr(scenarios_router, "ensure_app_user", lambda user_id, email: None)
    monkeypatch.setattr(
        scenarios_router,
        "export_scenario_pack_for_user",
        lambda user_id, project_id, schema_version=None: {
            "schema_version": schema_version or "scenario-pack-v1",
            "exported_at": "2026-02-13T00:00:00",
            "source_project_id": project_id,
            "source_project_name": "Demo",
            "payload": {"data": {"experiments": []}},
        },
    )
    current_user = CurrentUser(
        user_id="00000000-0000-0000-0000-000000000001",
        email="u@example.com",
    )
    resp = scenarios_router.export_scenario_pack("p1", "scenario-pack-v2", current_user)
    assert resp.schema_version == "scenario-pack-v2"


def test_scenario_import_router_permission_denied(monkeypatch):
    monkeypatch.setattr(scenarios_router, "ensure_app_user", lambda user_id, email: None)

    def _raise_permission(*args, **kwargs):
        raise PermissionError("not allowed")

    monkeypatch.setattr(scenarios_router, "import_scenario_pack_for_user", _raise_permission)

    current_user = CurrentUser(
        user_id="00000000-0000-0000-0000-000000000001",
        email="u@example.com",
    )
    body = ScenarioImportRequest(
        workspace_id="w1",
        project_name="Imported",
        payload={},
    )

    with pytest.raises(HTTPException) as exc_info:
        scenarios_router.import_scenario_pack(body, current_user)

    assert exc_info.value.status_code == 403
    assert "not allowed" in str(exc_info.value.detail)


def test_scenario_validate_router_success(monkeypatch):
    monkeypatch.setattr(scenarios_router, "ensure_app_user", lambda user_id, email: None)
    monkeypatch.setattr(
        scenarios_router,
        "validate_scenario_pack_payload",
        lambda schema_version, payload: {
            "accepted_schema_version": schema_version or "scenario-pack-v1",
            "normalized_counts": {"experiments": 1, "variants": 2},
            "warnings": [],
        },
    )

    current_user = CurrentUser(
        user_id="00000000-0000-0000-0000-000000000001",
        email="u@example.com",
    )
    body = ScenarioImportRequest(
        workspace_id="w1",
        project_name="Imported",
        schema_version="scenario-pack-v2",
        payload={},
    )
    resp = scenarios_router.validate_scenario_pack(body, current_user)
    assert resp.accepted_schema_version == "scenario-pack-v2"
    assert resp.normalized_counts["variants"] == 2


def test_scenario_share_create_router_success(monkeypatch):
    monkeypatch.setattr(scenarios_router, "ensure_app_user", lambda user_id, email: None)
    monkeypatch.setattr(
        scenarios_router,
        "create_scenario_share_for_user",
        lambda **kwargs: {
            "share_token": "token",
            "expires_at": "2026-02-14T00:00:00",
            "schema_version": "scenario-pack-v2",
        },
    )
    current_user = CurrentUser(
        user_id="00000000-0000-0000-0000-000000000001",
        email="u@example.com",
    )
    body = scenarios_router.ScenarioShareCreateRequest(
        project_id="p1",
        schema_version="scenario-pack-v2",
        expires_hours=24,
    )
    resp = scenarios_router.create_scenario_share(body, current_user)
    assert resp.share_token == "token"


def test_scenario_share_resolve_router_not_found(monkeypatch):
    def _raise(*args, **kwargs):
        raise ValueError("Share link not found")

    monkeypatch.setattr(scenarios_router, "resolve_scenario_share", _raise)
    with pytest.raises(HTTPException) as exc_info:
        scenarios_router.resolve_share_link("bad")
    assert exc_info.value.status_code == 404


def test_scenario_share_revoke_router_success(monkeypatch):
    monkeypatch.setattr(scenarios_router, "ensure_app_user", lambda user_id, email: None)
    monkeypatch.setattr(
        scenarios_router,
        "revoke_scenario_share_for_user",
        lambda user_id, share_token: {
            "revoked": True,
            "revoked_at": "2026-02-14T12:00:00+00:00",
        },
    )
    current_user = CurrentUser(
        user_id="00000000-0000-0000-0000-000000000001",
        email="u@example.com",
    )
    resp = scenarios_router.revoke_share_link("share-token", current_user)
    assert resp.revoked is True


def test_scenario_share_revoke_router_forbidden(monkeypatch):
    monkeypatch.setattr(scenarios_router, "ensure_app_user", lambda user_id, email: None)

    def _raise_permission(*args, **kwargs):
        raise PermissionError("Not allowed to revoke this share link")

    monkeypatch.setattr(scenarios_router, "revoke_scenario_share_for_user", _raise_permission)
    current_user = CurrentUser(
        user_id="00000000-0000-0000-0000-000000000001",
        email="u@example.com",
    )

    with pytest.raises(HTTPException) as exc_info:
        scenarios_router.revoke_share_link("share-token", current_user)

    assert exc_info.value.status_code == 403
