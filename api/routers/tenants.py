"""Najemcy. Izolacja przez building_id → buildings.org_id (tenants nie ma org_id)."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status

from api.deps import get_current_org
from api.ownership import assert_building_in_org
from api.schemas.tenants import TenantCreate, TenantOut, TenantUpdate
from db.supabase_client import service_client

router = APIRouter(prefix="/tenants", tags=["tenants"])


def _building_ids(client, org_id: str) -> list[str]:
    """Id budynków organizacji — do filtrowania najemców (brak org_id w tenants)."""
    res = client.table("buildings").select("id").eq("org_id", org_id).execute()
    return [b["id"] for b in (res.data or [])]


@router.get("", response_model=list[TenantOut])
def list_tenants(
    building_id: str | None = None, org_id: str = Depends(get_current_org)
):
    """Lista najemców organizacji, opcjonalnie zawężona do jednego budynku."""
    client = service_client()
    if building_id is not None:
        assert_building_in_org(client, building_id, org_id)
        res = client.table("tenants").select("*").eq("building_id", building_id).execute()
        return [TenantOut(**row) for row in (res.data or [])]

    ids = _building_ids(client, org_id)
    if not ids:
        return []
    res = client.table("tenants").select("*").in_("building_id", ids).execute()
    return [TenantOut(**row) for row in (res.data or [])]


@router.post("", response_model=TenantOut, status_code=http_status.HTTP_201_CREATED)
def create_tenant(body: TenantCreate, org_id: str = Depends(get_current_org)):
    """Tworzy najemcę w budynku należącym do organizacji."""
    client = service_client()
    assert_building_in_org(client, str(body.building_id), org_id)
    row = body.model_dump(mode="json")
    res = client.table("tenants").insert(row).execute()
    return TenantOut(**(res.data or [row])[0])


@router.get("/{tenant_id}", response_model=TenantOut)
def get_tenant(tenant_id: str, org_id: str = Depends(get_current_org)):
    """Szczegóły najemcy (jeśli należy do organizacji)."""
    client = service_client()
    res = client.table("tenants").select("*").eq("id", tenant_id).limit(1).execute()
    rows = res.data or []
    if not rows:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Nie znaleziono najemcy"
        )
    assert_building_in_org(client, rows[0]["building_id"], org_id)
    return TenantOut(**rows[0])


@router.patch("/{tenant_id}", response_model=TenantOut)
def update_tenant(
    body: TenantUpdate, tenant_id: str, org_id: str = Depends(get_current_org)
):
    """Aktualizuje najemcę (tylko przekazane pola). Budynku nie zmieniamy."""
    patch = body.model_dump(exclude_unset=True, mode="json")
    if not patch:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Brak pól do aktualizacji",
        )
    client = service_client()
    # Najpierw potwierdź własność (i istnienie) najemcy.
    existing = client.table("tenants").select("building_id").eq("id", tenant_id).limit(1).execute()
    rows = existing.data or []
    if not rows:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Nie znaleziono najemcy"
        )
    assert_building_in_org(client, rows[0]["building_id"], org_id)

    res = client.table("tenants").update(patch).eq("id", tenant_id).execute()
    return TenantOut(**(res.data or [])[0])
