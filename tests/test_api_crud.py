"""Testy warstwy HTTP dla routerów CRUD (TestClient + FakeSupabase).

Sprawdzają: round-trip create→get, filtr/izolację po org (obcy org nie wycieka),
walidację rodzica (zasób spoza org → 404), 404 dla nieistniejącego id, patch.

Id-y w fixturach to prawdziwe UUID-y, bo schematy *Out typują id/org_id jako UUID
(zgodnie z modelem bazy) — string typu "b1" nie przeszedłby walidacji odpowiedzi.
"""
from tests.conftest import ORG_TEST

OTHER_ORG = "22222222-2222-4222-8222-222222222222"
B1 = "b1111111-1111-4111-8111-111111111111"
B2 = "b2222222-2222-4222-8222-222222222222"
T1 = "c1111111-1111-4111-8111-111111111111"
M1 = "d1111111-1111-4111-8111-111111111111"
M9 = "d9999999-9999-4999-8999-999999999999"
TAR9 = "e9999999-9999-4999-8999-999999999999"
API = "/api/v1"


# ---------------------------------------------------------------------------
# organizations
# ---------------------------------------------------------------------------
def test_get_my_org(client, db):
    db["organizations"] = [{"id": ORG_TEST, "name": "Moja Org", "plan": "free"}]
    r = client.get(f"{API}/organizations/me")
    assert r.status_code == 200
    assert r.json()["name"] == "Moja Org"


def test_patch_my_org(client, db):
    db["organizations"] = [{"id": ORG_TEST, "name": "Stara", "plan": "free"}]
    r = client.patch(f"{API}/organizations/me", json={"name": "Nowa", "nip": "123"})
    assert r.status_code == 200
    assert r.json()["name"] == "Nowa"
    assert db["organizations"][0]["name"] == "Nowa"


# ---------------------------------------------------------------------------
# buildings
# ---------------------------------------------------------------------------
def test_create_then_get_building(client):
    r = client.post(
        f"{API}/buildings", json={"name": "Rynek 12", "address": "ul. Rynek 12"}
    )
    assert r.status_code == 201
    bid = r.json()["id"]
    assert r.json()["org_id"] == ORG_TEST

    r2 = client.get(f"{API}/buildings/{bid}")
    assert r2.status_code == 200
    assert r2.json()["name"] == "Rynek 12"


def test_list_buildings_isolated_by_org(client, db):
    db["buildings"] = [
        {"id": B1, "org_id": ORG_TEST, "name": "Moja", "address": "a"},
        {"id": B2, "org_id": OTHER_ORG, "name": "Obca", "address": "b"},
    ]
    r = client.get(f"{API}/buildings")
    assert r.status_code == 200
    names = {b["name"] for b in r.json()}
    assert names == {"Moja"}  # budynek obcej org nie wycieka


def test_get_building_other_org_404(client, db):
    db["buildings"] = [{"id": B2, "org_id": OTHER_ORG, "name": "Obca", "address": "b"}]
    r = client.get(f"{API}/buildings/{B2}")
    assert r.status_code == 404


def test_patch_building(client, db):
    db["buildings"] = [{"id": B1, "org_id": ORG_TEST, "name": "Stara", "address": "a"}]
    r = client.patch(f"{API}/buildings/{B1}", json={"name": "Nowa"})
    assert r.status_code == 200
    assert r.json()["name"] == "Nowa"


# ---------------------------------------------------------------------------
# tenants — izolacja przez building
# ---------------------------------------------------------------------------
def test_create_tenant_in_own_building(client, db):
    db["buildings"] = [{"id": B1, "org_id": ORG_TEST, "name": "Moja", "address": "a"}]
    r = client.post(
        f"{API}/tenants",
        json={"building_id": B1, "name": "Najemca", "email": "n@x.pl", "unit_no": "U1"},
    )
    assert r.status_code == 201
    assert r.json()["unit_no"] == "U1"


def test_create_tenant_in_foreign_building_404(client, db):
    db["buildings"] = [{"id": B2, "org_id": OTHER_ORG, "name": "Obca", "address": "b"}]
    r = client.post(
        f"{API}/tenants",
        json={"building_id": B2, "name": "X", "email": "x@x.pl", "unit_no": "U9"},
    )
    assert r.status_code == 404  # budynek spoza org


def test_list_tenants_filtered_by_building(client, db):
    db["buildings"] = [{"id": B1, "org_id": ORG_TEST, "name": "Moja", "address": "a"}]
    db["tenants"] = [
        {"id": T1, "building_id": B1, "name": "A", "email": "a@x", "unit_no": "U1", "active": True},
        {"id": M1, "building_id": B1, "name": "B", "email": "b@x", "unit_no": "U2", "active": True},
    ]
    r = client.get(f"{API}/tenants", params={"building_id": B1})
    assert r.status_code == 200
    assert len(r.json()) == 2


# ---------------------------------------------------------------------------
# meters + assignments
# ---------------------------------------------------------------------------
def test_create_meter_and_assignment(client, db):
    db["buildings"] = [{"id": B1, "org_id": ORG_TEST, "name": "Moja", "address": "a"}]
    db["tenants"] = [
        {"id": T1, "building_id": B1, "name": "A", "email": "a@x", "unit_no": "U1", "active": True}
    ]
    rm = client.post(f"{API}/meters", json={"building_id": B1, "serial_no": "MB-1"})
    assert rm.status_code == 201
    mid = rm.json()["id"]

    ra = client.post(
        f"{API}/meters/{mid}/assignments",
        json={"tenant_id": T1, "valid_from": "2026-01-01"},
    )
    assert ra.status_code == 201
    assert ra.json()["meter_id"] == mid
    assert len(db["meter_assignments"]) == 1


def test_meter_readings_history(client, db):
    db["buildings"] = [{"id": B1, "org_id": ORG_TEST, "name": "Moja", "address": "a"}]
    db["meters"] = [{"id": M1, "building_id": B1, "serial_no": "MB-1"}]
    db["readings"] = [
        {"id": T1, "meter_id": M1, "read_at": "2026-04-01T00:00:00", "value_kwh": "1000.000"},
        {"id": B2, "meter_id": M1, "read_at": "2026-04-30T23:00:00", "value_kwh": "1177.000"},
    ]
    r = client.get(f"{API}/meters/{M1}/readings")
    assert r.status_code == 200
    assert len(r.json()) == 2
    # najnowsze pierwsze
    assert r.json()[0]["read_at"].startswith("2026-04-30")


def test_meter_from_foreign_building_404(client, db):
    db["buildings"] = [{"id": B2, "org_id": OTHER_ORG, "name": "Obca", "address": "b"}]
    db["meters"] = [{"id": M9, "building_id": B2, "serial_no": "X"}]
    r = client.get(f"{API}/meters/{M9}/readings")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# tariffs + components
# ---------------------------------------------------------------------------
def test_create_tariff_and_component(client):
    rt = client.post(
        f"{API}/tariffs", json={"name": "G11 2026", "valid_from": "2026-01-01"}
    )
    assert rt.status_code == 201
    tid = rt.json()["id"]

    rc = client.post(
        f"{API}/tariffs/{tid}/components",
        json={"name": "Energia", "component_type": "per_kwh", "unit_price": "0.51760"},
    )
    assert rc.status_code == 201

    rg = client.get(f"{API}/tariffs/{tid}")
    assert rg.status_code == 200
    assert len(rg.json()["components"]) == 1
    assert rg.json()["components"][0]["name"] == "Energia"


def test_add_component_to_foreign_tariff_404(client, db):
    db["tariff_templates"] = [
        {"id": TAR9, "org_id": OTHER_ORG, "name": "Obca", "valid_from": "2026-01-01"}
    ]
    r = client.post(
        f"{API}/tariffs/{TAR9}/components",
        json={"name": "X", "component_type": "per_kwh", "unit_price": "1.0"},
    )
    assert r.status_code == 404
