"""Testy generowania/rotacji portal_token (core.portal_auth.ensure_portal_token)
oraz walidacji (resolve_tenant_by_token) — bez sieci, na FakeSupabase.
"""
from datetime import datetime, timedelta, timezone

import pytest

from core.portal_auth import (
    PortalTokenInvalid,
    ensure_portal_token,
    resolve_tenant_by_token,
)
from tests.fake_supabase import FakeSupabase

ORG = "11111111-1111-4111-8111-111111111111"
B1 = "b1111111-1111-4111-8111-111111111111"
T1 = "c1111111-1111-4111-8111-111111111111"


def _future(days=30):
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def _past():
    return (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()


def _fake(tenant):
    return FakeSupabase(
        {
            "buildings": [{"id": B1, "org_id": ORG, "name": "B", "address": "a"}],
            "tenants": [tenant],
        }
    )


# --- ensure_portal_token ---


def test_generates_token_when_missing():
    f = _fake({"id": T1, "building_id": B1, "active": True, "portal_token": None, "token_expires_at": None})
    token = ensure_portal_token(f, T1, ttl_days=90)
    assert token
    saved = f.data["tenants"][0]
    assert saved["portal_token"] == token
    assert saved["token_expires_at"]  # ustawiona data ważności


def test_rotates_when_expired():
    old = "stary-token"
    f = _fake({"id": T1, "building_id": B1, "active": True, "portal_token": old, "token_expires_at": _past()})
    token = ensure_portal_token(f, T1, ttl_days=90)
    assert token != old
    assert f.data["tenants"][0]["portal_token"] == token


def test_keeps_valid_token():
    valid = "wazny-token"
    exp = _future()
    f = _fake({"id": T1, "building_id": B1, "active": True, "portal_token": valid, "token_expires_at": exp})
    token = ensure_portal_token(f, T1, ttl_days=90)
    assert token == valid
    assert f.data["tenants"][0]["token_expires_at"] == exp  # data nietknięta


# --- resolve_tenant_by_token ---


def test_resolve_valid():
    f = _fake({"id": T1, "building_id": B1, "name": "N", "email": "e", "unit_no": "U1",
               "active": True, "portal_token": "tok", "token_expires_at": _future()})
    tenant = resolve_tenant_by_token(f, "tok")
    assert tenant["id"] == T1
    assert tenant["org_id"] == ORG
    assert tenant["building"]["name"] == "B"


def test_resolve_expired_raises():
    f = _fake({"id": T1, "building_id": B1, "active": True, "portal_token": "tok", "token_expires_at": _past()})
    with pytest.raises(PortalTokenInvalid):
        resolve_tenant_by_token(f, "tok")


def test_resolve_unknown_raises():
    f = _fake({"id": T1, "building_id": B1, "active": True, "portal_token": "tok", "token_expires_at": _future()})
    with pytest.raises(PortalTokenInvalid):
        resolve_tenant_by_token(f, "inny")


def test_resolve_inactive_raises():
    f = _fake({"id": T1, "building_id": B1, "active": False, "portal_token": "tok", "token_expires_at": _future()})
    with pytest.raises(PortalTokenInvalid):
        resolve_tenant_by_token(f, "tok")
