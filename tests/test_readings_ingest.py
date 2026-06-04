"""Testy POST /readings — przyjmowanie odczytów z gateway (PLC, X-API-Key).

Endpoint autoryzuje się przez get_api_key_org (nie get_current_org), więc tu
nadpisujemy tę zależność osobno. Dla testów 401 (zły/brak klucza) używamy
klienta BEZ nadpisania — żeby zadziałała prawdziwa weryfikacja X-API-Key,
seedujemy api_keys w fake bazie.
"""
import hashlib

import pytest
from fastapi.testclient import TestClient

from api.deps import get_api_key_org
from api.main import app
from tests.conftest import ORG_TEST
from tests.fake_supabase import FakeSupabase

OTHER_ORG = "22222222-2222-4222-8222-222222222222"
B1 = "b1111111-1111-4111-8111-111111111111"
M1 = "d1111111-1111-4111-8111-111111111111"
M9 = "d9999999-9999-4999-8999-999999999999"
API = "/api/v1"


@pytest.fixture
def db():
    return {}


@pytest.fixture
def fake(db):
    f = FakeSupabase(db)
    f.data = db
    return f


def _seed_meter_in_org(db, *, building_id=B1, meter_id=M1, org_id=ORG_TEST):
    db.setdefault("buildings", []).append(
        {"id": building_id, "org_id": org_id, "name": "Moja", "address": "a"}
    )
    db.setdefault("meters", []).append(
        {"id": meter_id, "building_id": building_id, "serial_no": "MB-1"}
    )


@pytest.fixture
def client(fake, monkeypatch):
    """Klient z nadpisanym get_api_key_org → ORG_TEST (omija weryfikację klucza)."""
    monkeypatch.setattr("api.routers.readings.service_client", lambda: fake)
    app.dependency_overrides[get_api_key_org] = lambda: ORG_TEST
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def raw_client(fake, monkeypatch):
    """Klient BEZ nadpisania auth — testuje prawdziwą weryfikację X-API-Key.

    deps.get_api_key_org woła service_client() z api.deps, więc patchujemy tam.
    """
    monkeypatch.setattr("api.routers.readings.service_client", lambda: fake)
    monkeypatch.setattr("api.deps.service_client", lambda: fake)
    return TestClient(app)


# --- tor z nadpisaną autoryzacją (logika endpointu) ---


def test_create_reading_201(client, db):
    _seed_meter_in_org(db)
    r = client.post(f"{API}/readings", json={"meter_id": M1, "value_kwh": 1234.567})
    assert r.status_code == 201
    body = r.json()
    assert body["meter_id"] == M1
    assert body["source"] == "plc"  # domyślne źródło
    assert len(db["readings"]) == 1


def test_create_reading_idempotent_retry(client, db):
    """Ten sam (meter_id, read_at) drugi raz → 200, bez duplikatu."""
    _seed_meter_in_org(db)
    payload = {"meter_id": M1, "value_kwh": 1000, "read_at": "2026-04-30T23:00:00+00:00"}
    r1 = client.post(f"{API}/readings", json=payload)
    assert r1.status_code == 201
    r2 = client.post(f"{API}/readings", json=payload)
    assert r2.status_code == 200
    assert len(db["readings"]) == 1  # brak duplikatu


def test_create_reading_foreign_meter_404(client, db):
    """meter_id spoza organizacji klucza → 404 (izolacja)."""
    db["buildings"] = [{"id": B1, "org_id": OTHER_ORG, "name": "Obca", "address": "b"}]
    db["meters"] = [{"id": M9, "building_id": B1, "serial_no": "X"}]
    r = client.post(f"{API}/readings", json={"meter_id": M9, "value_kwh": 100})
    assert r.status_code == 404


def test_create_reading_negative_value_422(client, db):
    _seed_meter_in_org(db)
    r = client.post(f"{API}/readings", json={"meter_id": M1, "value_kwh": -5})
    assert r.status_code == 422


# --- tor z prawdziwą weryfikacją X-API-Key ---


def test_missing_api_key_401(raw_client):
    r = raw_client.post(f"{API}/readings", json={"meter_id": M1, "value_kwh": 100})
    assert r.status_code == 401


def test_invalid_api_key_401(raw_client, db):
    r = raw_client.post(
        f"{API}/readings",
        json={"meter_id": M1, "value_kwh": 100},
        headers={"X-API-Key": "nie-istnieje"},
    )
    assert r.status_code == 401


def test_valid_api_key_accepts_reading(raw_client, db):
    """Poprawny klucz w api_keys → odczyt przechodzi (201)."""
    key = "tajny-klucz-gateway"
    db["api_keys"] = [
        {
            "id": "k1",
            "org_id": ORG_TEST,
            "key_hash": hashlib.sha256(key.encode()).hexdigest(),
            "active": True,
        }
    ]
    _seed_meter_in_org(db)
    r = raw_client.post(
        f"{API}/readings",
        json={"meter_id": M1, "value_kwh": 1234.567},
        headers={"X-API-Key": key},
    )
    assert r.status_code == 201
