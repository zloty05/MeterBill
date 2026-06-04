"""Fixtury testów warstwy HTTP (API CRUD).

Routery wołają service_client() bezpośrednio (zaimportowany do przestrzeni nazw
każdego modułu) i get_current_org z deps. W testach:
  - podmieniamy service_client w każdym module routera + api.ownership na wspólny
    FakeSupabase (in-memory, bez sieci);
  - nadpisujemy get_current_org przez dependency_overrides na stały ORG_TEST,
    omijając weryfikację JWT.
"""
import pytest
from fastapi.testclient import TestClient

from api.deps import get_current_org, get_current_user
from api.main import app
from tests.fake_supabase import FakeSupabase

ORG_TEST = "11111111-1111-4111-8111-111111111111"

# Moduły, w których nazwa service_client jest używana i którą trzeba podmienić.
# api.ownership NIE jest tu — jego helpery dostają klienta jako argument z routera.
_PATCH_TARGETS = [
    "api.routers.organizations",
    "api.routers.buildings",
    "api.routers.tenants",
    "api.routers.meters",
    "api.routers.tariffs",
    "api.routers.readings",
]


@pytest.fixture
def db():
    """Pusta in-memory baza; testy seedują przez fixture data lub bezpośrednio."""
    return {}


@pytest.fixture
def fake(db):
    f = FakeSupabase(db)
    f.data = db  # współdziel TEN dict (FakeSupabase robi `data or {}`, gubi pusty dict)
    return f


@pytest.fixture
def client(fake, monkeypatch):
    """TestClient z podmienionym klientem Supabase i auth → ORG_TEST."""
    for target in _PATCH_TARGETS:
        monkeypatch.setattr(f"{target}.service_client", lambda: fake)

    app.dependency_overrides[get_current_org] = lambda: ORG_TEST
    # get_current_user używany przez router organizations — zwróć minimalny obiekt.
    app.dependency_overrides[get_current_user] = lambda: type(
        "U", (), {"id": "u-test", "email": "t@t", "org_id": ORG_TEST, "role": "admin"}
    )()
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
