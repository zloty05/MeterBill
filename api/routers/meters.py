"""Liczniki (podliczniki M-Bus) i przypisania licznik↔najemca.

Izolacja przez building_id → buildings.org_id (meters nie ma własnego org_id).
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status

from api.deps import get_current_org
from api.ownership import (
    assert_building_in_org,
    assert_tenant_in_org,
    get_meter_in_org,
)
from api.schemas.meters import (
    AssignmentCreate,
    AssignmentOut,
    MeterCreate,
    MeterOut,
    MeterUpdate,
)
from api.schemas.readings import ReadingOut
from db.supabase_client import service_client

router = APIRouter(prefix="/meters", tags=["meters"])


def _building_ids(client, org_id: str) -> list[str]:
    res = client.table("buildings").select("id").eq("org_id", org_id).execute()
    return [b["id"] for b in (res.data or [])]


@router.get("", response_model=list[MeterOut])
def list_meters(building_id: str | None = None, org_id: str = Depends(get_current_org)):
    """Lista liczników organizacji, opcjonalnie zawężona do jednego budynku."""
    client = service_client()
    if building_id is not None:
        assert_building_in_org(client, building_id, org_id)
        res = client.table("meters").select("*").eq("building_id", building_id).execute()
        return [MeterOut(**row) for row in (res.data or [])]

    ids = _building_ids(client, org_id)
    if not ids:
        return []
    res = client.table("meters").select("*").in_("building_id", ids).execute()
    return [MeterOut(**row) for row in (res.data or [])]


@router.post("", response_model=MeterOut, status_code=http_status.HTTP_201_CREATED)
def create_meter(body: MeterCreate, org_id: str = Depends(get_current_org)):
    """Tworzy licznik w budynku należącym do organizacji."""
    client = service_client()
    assert_building_in_org(client, str(body.building_id), org_id)
    if body.tariff_id is not None:
        from api.ownership import assert_tariff_in_org

        assert_tariff_in_org(client, str(body.tariff_id), org_id)
    row = body.model_dump(mode="json")
    res = client.table("meters").insert(row).execute()
    return MeterOut(**(res.data or [row])[0])


@router.patch("/{meter_id}", response_model=MeterOut)
def update_meter(
    body: MeterUpdate, meter_id: str, org_id: str = Depends(get_current_org)
):
    """Aktualizuje licznik (tylko przekazane pola). Budynku nie zmieniamy."""
    patch = body.model_dump(exclude_unset=True, mode="json")
    if not patch:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Brak pól do aktualizacji",
        )
    client = service_client()
    get_meter_in_org(client, meter_id, org_id)  # walidacja własności + istnienia
    if "tariff_id" in patch and patch["tariff_id"] is not None:
        from api.ownership import assert_tariff_in_org

        assert_tariff_in_org(client, patch["tariff_id"], org_id)
    res = client.table("meters").update(patch).eq("id", meter_id).execute()
    return MeterOut(**(res.data or [])[0])


@router.get("/{meter_id}/readings", response_model=list[ReadingOut])
def meter_readings(meter_id: str, org_id: str = Depends(get_current_org)):
    """Historia odczytów licznika (najnowsze pierwsze)."""
    client = service_client()
    get_meter_in_org(client, meter_id, org_id)
    res = (
        client.table("readings")
        .select("*")
        .eq("meter_id", meter_id)
        .order("read_at", desc=True)
        .execute()
    )
    return [ReadingOut(**row) for row in (res.data or [])]


# --- Przypisania licznik↔najemca (meter_assignments) ---


@router.post(
    "/{meter_id}/assignments",
    response_model=AssignmentOut,
    status_code=http_status.HTTP_201_CREATED,
)
def create_assignment(
    body: AssignmentCreate, meter_id: str, org_id: str = Depends(get_current_org)
):
    """Przypisuje najemcę do licznika w danym okresie (valid_from..valid_to)."""
    client = service_client()
    get_meter_in_org(client, meter_id, org_id)
    assert_tenant_in_org(client, str(body.tenant_id), org_id)
    row = {**body.model_dump(mode="json"), "meter_id": meter_id}
    res = client.table("meter_assignments").insert(row).execute()
    return AssignmentOut(**(res.data or [row])[0])


@router.get("/{meter_id}/assignments", response_model=list[AssignmentOut])
def list_assignments(meter_id: str, org_id: str = Depends(get_current_org)):
    """Lista przypisań licznika."""
    client = service_client()
    get_meter_in_org(client, meter_id, org_id)
    res = (
        client.table("meter_assignments")
        .select("*")
        .eq("meter_id", meter_id)
        .execute()
    )
    return [AssignmentOut(**row) for row in (res.data or [])]
