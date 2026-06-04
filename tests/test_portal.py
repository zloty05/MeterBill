"""Testy portalu najemcy (publiczny, token w URL).

Portal czyta service_client() z api.routers.portal i z api.routers... nie używa
get_current_org — autoryzacja idzie wyłącznie przez token. Tu patchujemy
service_client w module portalu i seedujemy fake bazę.
"""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from api.main import app
from tests.fake_supabase import FakeSupabase

ORG = "11111111-1111-4111-8111-111111111111"
OTHER_ORG = "22222222-2222-4222-8222-222222222222"
B1 = "b1111111-1111-4111-8111-111111111111"
T1 = "c1111111-1111-4111-8111-111111111111"
T2 = "c2222222-2222-4222-8222-222222222222"
M1 = "d1111111-1111-4111-8111-111111111111"
INV1 = "f1111111-1111-4111-8111-111111111111"
INV_DRAFT = "f2222222-2222-4222-8222-222222222222"
INV_OTHER = "f9999999-9999-4999-8999-999999999999"
API = "/api/v1"

VALID_TOKEN = "tok-valid"
EXPIRED_TOKEN = "tok-expired"


def _future():
    return (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()


def _past():
    return (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()


@pytest.fixture
def db():
    return {}


@pytest.fixture
def fake(db):
    f = FakeSupabase(db)
    f.data = db
    return f


@pytest.fixture
def client(fake, monkeypatch):
    monkeypatch.setattr("api.routers.portal.service_client", lambda: fake)
    return TestClient(app)


def _seed(db, *, token=VALID_TOKEN, expires=None, active=True):
    expires = expires or _future()
    db["buildings"] = [{"id": B1, "org_id": ORG, "name": "Rynek 12", "address": "ul. Rynek 12"}]
    db["tenants"] = [
        {
            "id": T1,
            "building_id": B1,
            "name": "Najemca U1",
            "email": "u1@x.pl",
            "unit_no": "U1",
            "active": active,
            "portal_token": token,
            "token_expires_at": expires,
        }
    ]
    db["meters"] = [{"id": M1, "building_id": B1, "serial_no": "MB-1"}]
    db["meter_assignments"] = [{"id": "a1", "tenant_id": T1, "meter_id": M1, "valid_from": "2026-01-01"}]
    db["readings"] = [
        {"id": "aa111111-1111-4111-8111-111111111111", "meter_id": M1,
         "read_at": "2026-04-01T00:00:00+00:00", "value_kwh": "1000.000"},
        {"id": "aa222222-2222-4222-8222-222222222222", "meter_id": M1,
         "read_at": "2026-04-30T23:00:00+00:00", "value_kwh": "1177.000"},
    ]
    db["invoices"] = [
        {"id": INV1, "org_id": ORG, "tenant_id": T1, "invoice_no": "FV/001/04/2026",
         "period_from": "2026-04-01", "period_to": "2026-04-30", "status": "sent",
         "gross_amount": "211.77", "created_at": "2026-05-01T00:00:00+00:00"},
        {"id": INV_DRAFT, "org_id": ORG, "tenant_id": T1, "invoice_no": "FV/002/05/2026",
         "period_from": "2026-05-01", "period_to": "2026-05-31", "status": "draft",
         "gross_amount": "100.00", "created_at": "2026-06-01T00:00:00+00:00"},
    ]


# --- token ---


def test_overview_valid_token(client, db):
    _seed(db)
    r = client.get(f"{API}/portal/{VALID_TOKEN}/overview")
    assert r.status_code == 200
    body = r.json()
    assert body["tenant"]["name"] == "Najemca U1"
    assert body["tenant"]["building_name"] == "Rynek 12"
    assert body["latest_invoice"]["invoice_no"] == "FV/001/04/2026"


def test_unknown_token_404(client, db):
    _seed(db)
    r = client.get(f"{API}/portal/nie-ma/overview")
    assert r.status_code == 404


def test_expired_token_404(client, db):
    _seed(db, token=EXPIRED_TOKEN, expires=_past())
    r = client.get(f"{API}/portal/{EXPIRED_TOKEN}/overview")
    assert r.status_code == 404


def test_inactive_tenant_404(client, db):
    _seed(db, active=False)
    r = client.get(f"{API}/portal/{VALID_TOKEN}/overview")
    assert r.status_code == 404


# --- readings ---


def test_readings_for_tenant(client, db):
    _seed(db)
    r = client.get(f"{API}/portal/{VALID_TOKEN}/readings")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 2
    assert rows[0]["read_at"].startswith("2026-04-30")  # najnowsze pierwsze


# --- invoices ---


def test_invoices_hide_draft(client, db):
    _seed(db)
    r = client.get(f"{API}/portal/{VALID_TOKEN}/invoices")
    assert r.status_code == 200
    nums = [i["invoice_no"] for i in r.json()]
    assert "FV/001/04/2026" in nums
    assert "FV/002/05/2026" not in nums  # draft ukryty


def test_pdf_foreign_invoice_404(client, db):
    """Faktura innego najemcy nie jest dostępna przez ten token."""
    _seed(db)
    db["tenants"].append(
        {"id": T2, "building_id": B1, "name": "Inny", "email": "x@x", "unit_no": "U2",
         "active": True, "portal_token": "tok-2", "token_expires_at": _future()}
    )
    db["invoices"].append(
        {"id": INV_OTHER, "org_id": ORG, "tenant_id": T2, "invoice_no": "FV/003/04/2026",
         "period_from": "2026-04-01", "period_to": "2026-04-30", "status": "sent",
         "created_at": "2026-05-01T00:00:00+00:00"}
    )
    # T1 próbuje pobrać fakturę T2 → 404 (zanim dojdzie do renderu PDF)
    r = client.get(f"{API}/portal/{VALID_TOKEN}/invoices/{INV_OTHER}/pdf")
    assert r.status_code == 404


def test_pdf_draft_invoice_404(client, db):
    """Szkic nie jest dostępny w portalu nawet dla właściciela."""
    _seed(db)
    r = client.get(f"{API}/portal/{VALID_TOKEN}/invoices/{INV_DRAFT}/pdf")
    assert r.status_code == 404
