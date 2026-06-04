"""Walidacja przynależności zasobów do organizacji (izolacja multi-tenant).

Backend działa na service_client() (bypass RLS), więc izolację wymusza warstwa
aplikacji. Tabele bez własnej kolumny org_id (meters, tenants, readings,
tariff_components, meter_assignments) walidujemy „przez rodzica": sprawdzamy, że
budynek/taryfa/licznik należy do org, zanim cokolwiek zwrócimy lub zmienimy.

Każdy helper rzuca HTTPException 404 z polskim komunikatem, gdy zasób nie istnieje
lub należy do innej organizacji (nie zdradzamy, który z dwóch przypadków zaszedł).
"""
from fastapi import HTTPException
from fastapi import status as http_status


def _not_found(detail: str):
    return HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=detail)


def assert_building_in_org(client, building_id: str, org_id: str) -> None:
    """Potwierdza, że budynek istnieje i należy do organizacji."""
    res = (
        client.table("buildings")
        .select("id")
        .eq("id", building_id)
        .eq("org_id", org_id)
        .limit(1)
        .execute()
    )
    if not (res.data or []):
        raise _not_found("Nie znaleziono budynku")


def assert_tariff_in_org(client, tariff_id: str, org_id: str) -> None:
    """Potwierdza, że taryfa istnieje i należy do organizacji."""
    res = (
        client.table("tariff_templates")
        .select("id")
        .eq("id", tariff_id)
        .eq("org_id", org_id)
        .limit(1)
        .execute()
    )
    if not (res.data or []):
        raise _not_found("Nie znaleziono taryfy")


def get_meter_in_org(client, meter_id: str, org_id: str) -> dict:
    """Zwraca licznik, jeśli należy do organizacji (przez building → org).

    Rzuca 404, gdy licznik nie istnieje lub jest spoza org. Używane przy odczytach
    i przypisaniach, gdzie potrzebny też building_id licznika.
    """
    res = (
        client.table("meters")
        .select("id, building_id")
        .eq("id", meter_id)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    if not rows:
        raise _not_found("Nie znaleziono licznika")
    assert_building_in_org(client, rows[0]["building_id"], org_id)
    return rows[0]


def assert_tenant_in_org(client, tenant_id: str, org_id: str) -> None:
    """Potwierdza, że najemca należy do organizacji (przez building → org)."""
    res = (
        client.table("tenants")
        .select("id, building_id")
        .eq("id", tenant_id)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    if not rows:
        raise _not_found("Nie znaleziono najemcy")
    assert_building_in_org(client, rows[0]["building_id"], org_id)
