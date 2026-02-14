import os
import sys

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.api.schemas.workspaces import WorkspaceRetentionUpdateRequest


def test_workspace_retention_update_valid_range():
    req = WorkspaceRetentionUpdateRequest(simulation_retention_days=30)
    assert req.simulation_retention_days == 30


def test_workspace_retention_update_rejects_low_value():
    with pytest.raises(ValidationError):
        WorkspaceRetentionUpdateRequest(simulation_retention_days=0)


def test_workspace_retention_update_rejects_high_value():
    with pytest.raises(ValidationError):
        WorkspaceRetentionUpdateRequest(simulation_retention_days=366)
