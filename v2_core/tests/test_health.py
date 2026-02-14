import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.api.routers.health import health


def test_health():
    response = health()
    assert response["status"] == "ok"
