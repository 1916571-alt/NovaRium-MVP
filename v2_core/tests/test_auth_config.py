import os
import sys

from fastapi import HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.api.core.config import settings
from apps.api.routers.auth import post_refresh, post_sign_in, post_sign_out
from apps.api.schemas.auth import RefreshTokenRequest, SignInRequest


def test_sign_in_requires_supabase_config():
    old_url = settings.supabase_url
    old_key = settings.supabase_anon_key
    try:
        settings.supabase_url = ""
        settings.supabase_anon_key = ""
        try:
            post_sign_in(SignInRequest(email="x@example.com", password="password"))
        except HTTPException as exc:
            assert exc.status_code == 503
            return
        assert False, "Expected HTTPException"
    finally:
        settings.supabase_url = old_url
        settings.supabase_anon_key = old_key


def test_refresh_requires_supabase_config():
    old_url = settings.supabase_url
    old_key = settings.supabase_anon_key
    try:
        settings.supabase_url = ""
        settings.supabase_anon_key = ""
        try:
            post_refresh(RefreshTokenRequest(refresh_token="dummy"))
        except HTTPException as exc:
            assert exc.status_code == 503
            return
        assert False, "Expected HTTPException"
    finally:
        settings.supabase_url = old_url
        settings.supabase_anon_key = old_key


def test_sign_out_requires_bearer_token():
    try:
        post_sign_out(None)
    except HTTPException as exc:
        assert exc.status_code == 401
        return
    assert False, "Expected HTTPException"
